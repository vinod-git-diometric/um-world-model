"""Compare upstream MassGIS links with frozen hybrid predictions."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .normalize import normalize_address
from .resolve import read_rows


def compare_linkage(export: Path, normalized: Path) -> dict:
    with export.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    official = defaultdict(list)
    for row in rows:
        if row["ADDRESS_ID"].strip() not in {"", "0"}:
            official[row["ADDRESS_ID"]].append(row)

    parcels = read_rows(normalized / "parcels.parquet")
    loc_ids = {row["loc_id"] for row in parcels if row["loc_id"]}
    addresses = {
        row["address_id"]: row["normalized_address"]
        for row in read_rows(normalized / "addresses.parquet")
    }
    outcomes = Counter()
    disagreement_details = Counter()
    with (normalized / "spatial-resolutions.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            prediction = json.loads(line)
            addr_id = prediction["address_id"]
            labels = official.get(addr_id)
            if not labels:
                outcomes["hybrid_id_absent_from_export"] += 1
                continue
            # Check civic identity rather than trusting numeric ID overlap alone.
            matching = [
                row
                for row in labels
                if normalize_address(f"{row['ADDR_NUM']} {row['STREETNAME']}")
                == addresses[addr_id]
            ]
            if not matching:
                outcomes["shared_id_civic_text_mismatch"] += 1
                continue
            links = {row["LOC_ID"].strip() for row in matching if row["LOC_ID"].strip()}
            if not links:
                outcomes["export_loc_id_missing"] += 1
            elif not links <= loc_ids:
                outcomes["export_loc_id_absent_from_parcel_snapshot"] += 1
                disagreement_details["missing_loc_id:" + prediction["reason"]] += 1
            elif prediction["status"] != "accepted":
                outcomes["hybrid_abstained"] += 1
                disagreement_details["abstained:" + prediction["reason"]] += 1
            elif set(prediction["parcel_ids"]) == links:
                outcomes["exact_parcel_set_agreement"] += 1
            else:
                outcomes["parcel_set_disagreement"] += 1
                inside = set(prediction["interior"])
                text = set(prediction["text"])
                if links & inside:
                    disagreement_details[
                        "disagreed:official_link_in_interior_candidates"
                    ] += 1
                elif links & text:
                    disagreement_details[
                        "disagreed:official_link_in_text_candidates"
                    ] += 1
                else:
                    disagreement_details[
                        "disagreed:official_link_outside_hybrid_candidates"
                    ] += 1
                disagreement_details[
                    f"disagreed:point_type:{prediction.get('point_type')}"
                ] += 1

    export_links = {row["LOC_ID"].strip() for row in rows if row["LOC_ID"].strip()}
    return {
        "export_rows": len(rows),
        "export_loc_id_populated_rows": sum(
            bool(row["LOC_ID"].strip()) for row in rows
        ),
        "export_loc_id_absent_from_parcels_rows": sum(
            bool(loc := row["LOC_ID"].strip()) and loc not in loc_ids for row in rows
        ),
        "export_distinct_loc_ids": len(export_links),
        "export_distinct_loc_ids_absent_from_parcels": len(export_links - loc_ids),
        "export_rows_missing_address_id": len(rows) - sum(map(len, official.values())),
        "export_distinct_address_ids": len(official),
        "export_address_ids_with_multiple_rows": sum(
            len(group) > 1 for group in official.values()
        ),
        "export_address_ids_with_multiple_loc_ids": sum(
            len({row["LOC_ID"].strip() for row in group} - {""}) > 1
            for group in official.values()
        ),
        "export_address_ids_absent_from_hybrid": len(
            official.keys() - addresses.keys()
        ),
        "outcomes": outcomes,
        "disagreement_details": disagreement_details,
    }
