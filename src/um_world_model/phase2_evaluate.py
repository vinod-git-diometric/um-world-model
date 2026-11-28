"""Evaluate physical graph on assessor-only cards held out of commercial inputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from .assessor_validation import metrics
from .commercial import link_physical
from .normalize import normalize_address


def assess_physical_holdout(frozen: dict, physical: dict, commercial: dict) -> dict:
    observed_civic = {node["civic"] for node in commercial["occupancies"]}
    by_civic = defaultdict(list)
    for edge in physical["address_parcel_edges"]:
        by_civic[edge["civic"]].append(edge)
    keys = defaultdict(set)
    for parcel, rows in physical["parcel_assessor_rows"].items():
        keys[parcel].update(
            row["prop_id"].strip().upper() for row in rows if row["prop_id"]
        )
    exclusions = Counter()
    expected_address, guessed_address = [], []
    expected_parcel, guessed_parcel = [], []
    for case in frozen["cases"]:
        if case["status"] != "card_verified":
            exclusions["assessor_card_unverified"] += 1
            continue
        if case["lead_evidence"] or case["normalized_query"] in observed_civic:
            exclusions["external_lead_or_discovery_overlap"] += 1
            continue
        if all(card["class"].startswith("337") for card in case["cards"]):
            exclusions["parking_only"] += 1
            continue
        civic = case["normalized_query"]
        rows = by_civic[civic]
        link = link_physical(rows, None)
        expected_address.append(
            {normalize_address(card["fields"]["Location"]) for card in case["cards"]}
        )
        guessed_address.append({civic} if rows else set())
        expected_parcel.append(
            {card["tax_key"].strip().upper() for card in case["cards"]}
        )
        ids = link["parcel_ids"]
        guessed_parcel.append(
            set().union(*(keys[pid] for pid in ids))
            if ids and all(keys[pid] for pid in ids)
            else set()
        )
    return {
        "municipal_civic_lookup": metrics(expected_address, guessed_address),
        "municipal_parcel_tax_keys": metrics(expected_parcel, guessed_parcel),
        "exclusions": exclusions,
        "independent_occupancy_audit_cases": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("graph_directory", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            assess_physical_holdout(
                json.loads(args.reference.read_bytes()),
                json.loads((args.graph_directory / "physical-1.0.json").read_bytes()),
                json.loads((args.graph_directory / "commercial-1.0.json").read_bytes()),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
