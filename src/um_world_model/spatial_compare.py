"""Compare text and spatial outputs without publishing row-level data."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .ingest import load_manifest, verify_snapshots
from .normalize import iter_features, normalize_address
from .resolve import load_resolutions, read_rows


def compare_spatial(manifest: Path, baseline: Path, seed: Path) -> dict:
    normalized = manifest.parent / "normalized"
    verify_snapshots(manifest)
    old = {row.address_id: row for row in load_resolutions(baseline)}
    text = {
        row.address_id: row
        for row in load_resolutions(normalized / "resolutions.jsonl")
    }
    spatial = {
        row["address_id"]: row
        for line in (normalized / "spatial-resolutions.jsonl").read_text().splitlines()
        if (row := json.loads(line))
    }
    if text.keys() != spatial.keys():
        raise ValueError("Same-snapshot comparison requires identical address IDs")
    transitions = Counter(
        (text[key].status, row["status"]) for key, row in spatial.items()
    )
    unresolved = {key for key, row in old.items() if row.status != "accepted"}
    unresolved_reasons = Counter(
        spatial[key]["reason"] for key in unresolved & spatial.keys()
    )
    unresolved_text = Counter(
        spatial[key]["text_diagnostic"] for key in unresolved & spatial.keys()
    )

    source_ids = {}
    for source, field in (
        ("massgis_addresses", "MASTER_ADDRESS_ID"),
        ("massgis_parcels", "OBJECTID"),
    ):
        for feature, snap in iter_features(manifest, source):
            source_ids.setdefault((snap.source_id, snap.path, snap.sha256), set()).add(
                str(feature["attributes"][field])
            )
    traced = sum(
        bool(row["evidence"])
        and all(
            ev["source_record_id"]
            in source_ids.get(
                (ev["source_id"], ev["raw_evidence_ref"], ev["raw_sha256"]), ()
            )
            for ev in row["evidence"]
        )
        for row in spatial.values()
    )
    by_address = defaultdict(list)
    for address in read_rows(normalized / "addresses.parquet"):
        by_address[address["normalized_address"]].append(address["address_id"])
    seed_metrics = Counter()
    with seed.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            ids = by_address[normalize_address(row["source_address"])]
            seed_metrics["rows"] += 1
            seed_metrics["any_address_candidate"] += bool(ids)
            seed_metrics["multiple_address_candidates"] += len(ids) > 1
            seed_metrics["any_text_parcel_accepted"] += any(
                text[key].status == "accepted" for key in ids
            )
            seed_metrics["any_spatial_parcel_accepted"] += any(
                spatial[key]["status"] == "accepted" for key in ids
            )
            seed_metrics["multiple_spatial_parcels_across_address_candidates"] += (
                len({pid for key in ids for pid in spatial[key]["parcel_ids"]}) > 1
            )

    return {
        "run_id": load_manifest(manifest).run_id,
        "published_baseline_unresolved": len(unresolved),
        "published_baseline_unresolved_missing_in_current_run": len(
            unresolved - spatial.keys()
        ),
        "published_baseline_unresolved_reasons": unresolved_reasons,
        "published_baseline_unresolved_text_diagnostics": unresolved_text,
        "same_snapshot_transitions": {
            f"{a} -> {b}": n for (a, b), n in sorted(transitions.items())
        },
        "accepted_by_both_different_parcel_sets": sum(
            text[key].status == row["status"] == "accepted"
            and set(text[key].parcel_ids) != set(row["parcel_ids"])
            for key, row in spatial.items()
        ),
        "hybrid_reasons": Counter(row["reason"] for row in spatial.values()),
        "hybrid_rows": len(spatial),
        "hybrid_rows_traced": traced,
        "seed": seed_metrics,
    }
