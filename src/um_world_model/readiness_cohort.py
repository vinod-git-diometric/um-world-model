"""Freeze the nonoverlapping Phase 2.1 census cohort before merchant retrieval."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from .business_first import RELEASE, place_key
from .commercial import name_key
from .physical_graph import digest

QUOTAS = {
    "original_with_url": 20,
    "overture_with_url": 20,
    "overture_without_url": 10,
    "difficult": 10,
}
SEED = "stoneham-readiness-2026-11-27-v1"
CONTROLS = {"the book oasis", "gaetano s", "patina d"}


def freeze(graph: dict, places_result: dict, leads: list[dict], physical: dict) -> dict:
    if places_result["overture"]["release"] != RELEASE:
        raise ValueError("Expected pinned Places release")
    by_business = {row["id"]: row for row in graph["businesses"]}
    occupancy = defaultdict(list)
    for row in graph["occupancies"]:
        occupancy[row["business_id"]].append(row)
    key_count = Counter()
    civic_names = defaultdict(set)
    by_civic = defaultdict(list)
    for row in physical["address_parcel_edges"]:
        by_civic[row["civic"]].append(row)
    baseline_civics = {row["civic"] for row in graph["occupancies"]}
    controls = []
    original = []
    for row in leads:
        business = by_business[row["business_id"]]
        rows = occupancy[business["id"]]
        if len(rows) != 1 or not rows[0]["civic"]:
            continue
        address = rows[0]
        case = {
            "id": business["id"],
            "name": business["name"],
            "civic": address["civic"],
            "unit": address.get("unit"),
            "urls": row["urls"],
            "source_refs": business["observations"],
            "observed_flags": [],
        }
        if name_key(business["name"]) in CONTROLS:
            controls.append(case)
        elif row["urls"]:
            original.append(case)
    pools = defaultdict(list)
    for place in places_result["places"]:
        if place["disposition"] == "business_candidate" and (key := place_key(place)):
            key_count[key] += 1
            civic_names[key[1]].add(key[0])
    for place in places_result["places"]:
        key = place_key(place)
        if (
            place["disposition"] != "business_candidate"
            or not key
            or key[1] in baseline_civics
        ):
            continue
        civic = key[1]
        multi = len(civic_names[civic]) > 1
        duplicate = key_count[key] > 1
        units = sum(bool(r.get("unit")) for r in by_civic[civic])
        flags = [
            label
            for flag, label in (
                (multi, "multiple_place_names_at_civic"),
                (duplicate, "duplicate_gers_key_candidate"),
                (units > 1, "multiple_physical_units"),
            )
            if flag
        ]
        case = {
            "id": "overture:" + place["id"],
            "name": place["name"],
            "civic": civic,
            "unit": None,
            "urls": place["websites"] or [],
            "source_refs": [place["id"]],
            "observed_flags": flags,
        }
        stratum = (
            "difficult"
            if flags
            else ("overture_with_url" if case["urls"] else "overture_without_url")
        )
        pools[stratum].append(case)
    pools["original_with_url"] = original

    used = {row["civic"] for row in controls}
    cases = []
    shared_original_sites = []
    expected_slots = dict(QUOTAS)
    if len(original) != QUOTAS["original_with_url"]:
        raise ValueError(
            f"Expected 20 remaining original URL leads, got {len(original)}"
        )
    original_civic_count = len({row["civic"] for row in original})
    expected_slots["original_with_url"] = original_civic_count
    expected_slots["difficult"] += QUOTAS["original_with_url"] - original_civic_count
    for stratum, goal in expected_slots.items():

        def rank(row, stratum=stratum):
            # Reserve a difficult stratum with physical multi-unit evidence.
            priority = (
                0
                if stratum == "difficult"
                and "multiple_physical_units" in row["observed_flags"]
                else 1
            )
            return priority, sha256(f"{SEED}:{row['id']}".encode()).hexdigest()

        count = 0
        for row in sorted(pools[stratum], key=rank):
            if row["civic"] in used:
                continue
            used.add(row["civic"])
            cases.append({"stratum": stratum, **row})
            count += 1
            if count == goal:
                break
        if count != goal:
            raise ValueError(
                f"{stratum}: only {count} distinct civic sites, expected {goal}"
            )
    selected_ids = {row["id"] for row in cases}
    for row in original:
        if row["id"] not in selected_ids:
            shared_original_sites.append(
                {"stratum": "original_shared_civic_companion", **row}
            )
    if len(controls) != 3:
        raise ValueError("Expected all three positive controls")
    return {
        "release": RELEASE,
        "seed": SEED,
        "frozen_at": datetime.now(UTC).isoformat(),
        "cases": cases,
        "controls": controls,
        "shared_original_companions": shared_original_sites,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph_directory", type=Path)
    parser.add_argument("places_result", type=Path)
    parser.add_argument("lead_audit", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paths = {
        "commercial": args.graph_directory / "commercial-1.0.json",
        "places": args.places_result,
        "leads": args.lead_audit,
        "physical": args.graph_directory / "physical-1.0.json",
    }
    result = freeze(*(json.loads(path.read_bytes()) for path in paths.values()))
    result["input_sha256"] = {key: digest(path) for key, path in paths.items()}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(Counter(row["stratum"] for row in result["cases"])))


if __name__ == "__main__":
    main()
