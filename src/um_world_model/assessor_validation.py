"""Project frozen Gate A.1 predictions onto assessor civic and tax-key labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .evaluate import wilson
from .normalize import normalize_address
from .resolve import read_rows


def metrics(expected: list[set[str]], predicted: list[set[str]]) -> dict:
    correct = sum(
        bool(guess) and guess == label
        for label, guess in zip(expected, predicted, strict=True)
    )
    accepted = sum(bool(guess) for guess in predicted)
    total = len(expected)
    return {
        "auditable": total,
        "accepted": accepted,
        "correct": correct,
        "precision": correct / accepted if accepted else None,
        "precision_interval_95": wilson(correct, accepted),
        "recall": correct / total if total else None,
        "recall_interval_95": wilson(correct, total),
    }


def assess_cohort(frozen_reference: Path, normalized: Path) -> dict:
    cases = json.loads(frozen_reference.read_text(encoding="utf-8"))["cases"]
    keys = [case["normalized_query"] for case in cases]
    if len(set(keys)) != len(keys):
        raise ValueError("Cohort queries must be distinct civic keys")
    addresses = defaultdict(list)
    for row in read_rows(normalized / "addresses.parquet"):
        addresses[row["normalized_address"]].append(row["address_id"])
    parcel_tax_keys = defaultdict(set)
    for row in read_rows(normalized / "parcels.parquet"):
        if row["prop_id"]:
            parcel_tax_keys[row["parcel_id"]].add(row["prop_id"].strip().upper())
    with (normalized / "spatial-resolutions.jsonl").open(encoding="utf-8") as handle:
        results = {
            row["address_id"]: row for line in handle if (row := json.loads(line))
        }

    strata = defaultdict(list)
    disagreements = Counter()
    for case in cases:
        if case["status"] != "card_verified":
            continue
        key = case["normalized_query"]
        address_ids = addresses[key]
        expected_tax_keys = {card["tax_key"].strip().upper() for card in case["cards"]}
        # Require all address records at the civic key to resolve to the same parcel set.
        resolved_sets = {
            frozenset(results[addr_id]["parcel_ids"])
            for addr_id in address_ids
            if addr_id in results and results[addr_id]["status"] == "accepted"
        }
        guessed_tax_keys = set()
        if len(resolved_sets) == 1 and all(
            addr_id in results and results[addr_id]["status"] == "accepted"
            for addr_id in address_ids
        ):
            parcel_ids = next(iter(resolved_sets))
            if all(parcel_tax_keys[pid] for pid in parcel_ids):
                guessed_tax_keys = set().union(
                    *(parcel_tax_keys[pid] for pid in parcel_ids)
                )
        if not address_ids:
            disagreements["no_exact_address_candidate"] += 1
        elif not guessed_tax_keys:
            disagreements["hybrid_or_tax_key_projection_abstention"] += 1
        elif guessed_tax_keys != expected_tax_keys:
            if expected_tax_keys < guessed_tax_keys:
                disagreements["predicted_physical_parcel_has_extra_tax_accounts"] += 1
            elif guessed_tax_keys < expected_tax_keys:
                disagreements["only_subset_of_municipal_tax_accounts"] += 1
            elif guessed_tax_keys & expected_tax_keys:
                disagreements["partly_overlapping_tax_accounts"] += 1
            else:
                disagreements["disjoint_tax_accounts"] += 1
        result = (
            {
                normalized
                for card in case["cards"]
                if (normalized := normalize_address(card["fields"]["Location"]))
            },
            {key} if address_ids else set(),
            expected_tax_keys,
            guessed_tax_keys,
        )
        strata["all_verified"].append(result)
        strata[case["frame"]].append(result)

    return {
        "candidate_count": len(cases),
        "statuses": Counter(case["status"] for case in cases),
        "frame_counts": Counter(case["frame"] for case in cases),
        "abcc_cases": sum(
            any(lead["source"] == "ABCC retail" for lead in case["lead_evidence"])
            for case in cases
        ),
        "strata": {
            stratum: {
                "address_exact_civic_lookup": metrics(
                    [row[0] for row in items], [row[1] for row in items]
                ),
                "parcel_assessor_tax_key_agreement": metrics(
                    [row[2] for row in items], [row[3] for row in items]
                ),
            }
            for stratum, items in strata.items()
        },
        "diagnostics": disagreements,
    }
