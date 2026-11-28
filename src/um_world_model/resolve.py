"""Conservative Address -> Parcel resolution."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from rapidfuzz import fuzz, process

from .models import Evidence, Resolution


def read_rows(path: Path) -> list[dict[str, Any]]:
    return pq.read_table(path).to_pylist()


def parse_evidence(value: str | dict[str, Any]) -> Evidence:
    payload = json.loads(value) if isinstance(value, str) else value
    return Evidence.model_validate(payload)


def resolve_run(
    address_path: Path,
    parcel_path: Path,
    output_path: Path | None = None,
    *,
    candidate_threshold: float = 85.0,
) -> Path:
    addresses = read_rows(address_path)
    parcels = read_rows(parcel_path)
    parcels_by_address: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for parcel in parcels:
        if parcel.get("normalized_address"):
            parcels_by_address[parcel["normalized_address"]].append(parcel)
    parcel_address_choices = sorted(parcels_by_address)
    results: list[Resolution] = []
    for address in addresses:
        normalized = address["normalized_address"]
        exact = parcels_by_address.get(normalized, [])
        address_evidence = parse_evidence(address["evidence"])
        if exact:
            results.append(
                Resolution(
                    address_id=address["address_id"],
                    parcel_ids=sorted({parcel["parcel_id"] for parcel in exact}),
                    status="accepted",
                    method="exact_normalized_address",
                    score=100.0,
                    evidence=[address_evidence]
                    + [parse_evidence(parcel["evidence"]) for parcel in exact],
                )
            )
            continue
        matches = process.extract(
            normalized,
            parcel_address_choices,
            scorer=fuzz.WRatio,
            score_cutoff=candidate_threshold,
            limit=5,
        )
        candidate_ids = sorted(
            {
                parcel["parcel_id"]
                for candidate, _score, _index in matches
                for parcel in parcels_by_address[candidate]
            }
        )
        results.append(
            Resolution(
                address_id=address["address_id"],
                status="ambiguous" if matches else "not_found",
                method="fuzzy_candidate_only" if matches else "no_candidate",
                score=float(matches[0][1]) if matches else None,
                candidate_parcel_ids=candidate_ids,
                evidence=[address_evidence],
            )
        )
    target = output_path or address_path.parent / "resolutions.jsonl"
    with target.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(result.model_dump_json() + "\n")
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        counts[result.status] += 1
    summary = {
        "address_count": len(results),
        "status_counts": dict(sorted(counts.items())),
        "accepted_coverage": counts["accepted"] / len(results) if results else None,
        "candidate_threshold": candidate_threshold,
        "acceptance_methods": ["exact_normalized_address"],
        "candidate_only_methods": ["fuzzy_candidate_only"],
    }
    (target.parent / "resolution-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target


def load_resolutions(path: Path) -> list[Resolution]:
    return [
        Resolution.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
