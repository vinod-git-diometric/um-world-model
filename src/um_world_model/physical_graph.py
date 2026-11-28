"""Versioned physical graph over the frozen MassGIS snapshots."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

from .ingest import load_manifest, verify_snapshots
from .normalize import normalize_address
from .resolve import read_rows

EXPORT_URL = (
    "https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/"
    "shapefiles/mad/town_exports/addr_pts/AddressPts_M284.zip"
)


def select_link(official, available, hybrid, *, comparable=True):
    """Return disposition, method, and accepted parcel identifiers."""
    if official:
        if not comparable:
            return "ambiguous", "official_identity_or_vintage_conflict", []
        if official - available:
            return "unavailable", "official_parcel_missing", []
        if hybrid and hybrid != official:
            return "ambiguous", "official_hybrid_conflict", []
        if len(official) > 1:
            return "ambiguous", "multiple_official_parcels", []
        return "accepted", "official_link", sorted(official)
    if hybrid and hybrid <= available:
        return "accepted", "hybrid_fallback", sorted(hybrid)
    return "unknown", "no_accepted_link", []


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_physical_graph(
    manifest_path: Path,
    export_csv: Path,
    archive: Path,
    *,
    export_vintage: str,
    export_retrieved_at: str,
) -> dict:
    vintage = date.fromisoformat(export_vintage)
    retrieved = datetime.fromisoformat(export_retrieved_at)
    if retrieved.tzinfo is None or vintage > retrieved.date():
        raise ValueError(
            "Export vintage and zoned retrieval timestamp are inconsistent"
        )
    verify_snapshots(manifest_path)
    manifest = load_manifest(manifest_path)
    norm = manifest_path.parent / "normalized"
    addresses = {r["address_id"]: r for r in read_rows(norm / "addresses.parquet")}
    parcel_rows = read_rows(norm / "parcels.parquet")
    parcels = defaultdict(list)
    for row in parcel_rows:
        parcels[row["parcel_id"]].append(row)
    available = set(parcels)
    hybrid_file = norm / "spatial-resolutions.jsonl"
    with hybrid_file.open(encoding="utf-8") as handle:
        hybrid = {
            row["address_id"]: row for line in handle if (row := json.loads(line))
        }
    export = defaultdict(list)
    non_geographic_rows = 0
    with export_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("GEOTOWN_ID") != "284":
                non_geographic_rows += 1
                continue
            if row["ADDRESS_ID"].strip() not in {"", "0"}:
                export[row["ADDRESS_ID"]].append(row)
    edges = []
    for address_id in sorted(addresses.keys() | export.keys()):
        records = export.get(address_id, [])
        address = addresses.get(address_id)
        spatial = hybrid.get(address_id, {})
        civic = {
            value
            for r in records
            if (value := normalize_address(f"{r['ADDR_NUM']} {r['STREETNAME']}"))
        }
        explicit = {r["LOC_ID"].strip() for r in records if r["LOC_ID"].strip()}
        # An address point dated after the export cannot be verified by this export.
        # Any older parcel vintage is retained on the target rows and exposed to readers.
        comparable = len(civic) == 1 and (
            address is None or address["normalized_address"] in civic
        )
        comparable &= all(
            not r.get("EDIT_DATE")
            or date.fromisoformat(r["EDIT_DATE"].replace("/", "-")) <= vintage
            for r in records
        )
        status, method, accepted = select_link(
            explicit,
            available,
            set(spatial.get("parcel_ids", [])),
            comparable=comparable,
        )
        edges.append(
            {
                "address_id": address_id,
                "civic": address["normalized_address"]
                if address
                else (next(iter(civic)) if len(civic) == 1 else None),
                "unit": address["unit"]
                if address
                else next(
                    (record["UNIT"] for record in records if record["UNIT"]), None
                ),
                "status": status,
                "method": method,
                "parcel_ids": accepted,
                "official_candidates": sorted(explicit),
                "missing_parcel_ids": sorted(explicit - available),
                "official_record_ids": sorted(r["ADDR_PT_ID"] for r in records),
                "hybrid_candidates": spatial.get("candidate_parcel_ids", []),
                "hybrid_reason": spatial.get("reason"),
                "address_evidence": json.loads(address["evidence"])
                if address
                else None,
            }
        )
    return {
        "schema_version": "physical-1.0",
        "source_manifest": manifest.run_id,
        "source_manifest_sha256": digest(manifest_path),
        "hybrid_sha256": digest(hybrid_file),
        "official_export": {
            "url": EXPORT_URL,
            "vintage": export_vintage,
            "retrieved_at": export_retrieved_at,
            "archive_sha256": digest(archive),
            "attributes_sha256": digest(export_csv),
            "out_of_scope_geographic_rows": non_geographic_rows,
        },
        "parcel_assessor_rows": dict(parcels),
        "address_parcel_edges": edges,
        "counts": dict(Counter(edge["method"] for edge in edges)),
    }
