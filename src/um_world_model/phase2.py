"""Build Phase 2 artifacts locally from scoped, retained source snapshots."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from .commercial import Observation, SourceEvidence, build_commercial_graph
from .physical_graph import build_physical_graph, digest

ABCC = "https://www.mass.gov/doc/abcc-active-{}-licenses/download"
SNAP = "https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0"
CARE_ROOT = "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services"
LAYERS = {
    "usda_snap": (
        SNAP,
        "City",
        "Record_ID",
        "Store_Name",
        "Store_Street_Address",
        "Store_Type",
        "authorization",
    ),
    "ma_child_care": (
        f"{CARE_ROOT}/Licensed_Child_Care_Programs/FeatureServer/0",
        "CITY",
        "PROV_NUM",
        "PROG_NAME",
        "ADDRESS",
        "PROG_TYPE",
        "license",
    ),
    "ma_long_term_care": (
        f"{CARE_ROOT}/Long_Term_Care_Residences/FeatureServer/0",
        "MAIL_CITY",
        "OBJECTID",
        "FAC_NAME",
        "ADDRESS",
        "FAC_TYPE",
        "directory",
    ),
}


def evidence(path: Path, source: str, url: str, vintage: str | None = None):
    acquired = datetime.fromtimestamp(path.stat().st_mtime, UTC)
    return {
        "source": source,
        "url": url,
        "vintage": vintage,
        "retrieved_at": acquired,
        "snapshot": path.name,
        "sha256": digest(path),
    }


def _text(value):
    return str(value or "").strip()


def _explicit_unit(*values):
    for value in values:
        match = re.search(
            r"(?:^|\s)(?:suite|ste\.?|unit|#)\s*([a-z0-9-]+)\s*$",
            _text(value),
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
    return None


def _workbook_rows(path: Path, *, retail: bool):
    if retail:
        import xlrd

        sheet = xlrd.open_workbook(path).sheet_by_index(0)
        header = sheet.row_values(1)
        for index in range(2, sheet.nrows):
            yield dict(zip(header, sheet.row_values(index), strict=True))
    else:
        from openpyxl import load_workbook

        book = load_workbook(path, read_only=True, data_only=True)
        try:
            rows = iter(book.active.values)
            next(rows)
            header = next(rows)
            for row in rows:
                yield dict(zip(header, row, strict=True))
        finally:
            book.close()


def load_abcc(path: Path, *, retail: bool) -> list[Observation]:
    table = "retail" if retail else "state"
    receipt = evidence(path, f"abcc_{table}", ABCC.format(table), "2026-11-20")
    result = []
    for row in _workbook_rows(path, retail=retail):
        town = row.get("MUNICIPALITY" if retail else "G7_CITY")
        if _text(town).casefold() != "stoneham":
            continue
        street = _text(row["ADDRESS1" if retail else "G7_ADDRESS1"])
        number = _text(row["ST_NO" if retail else "STREET_NO"])
        civic = (
            street if street.split()[:1] == [number] else f"{number} {street}".strip()
        )
        label = _text(row.get("DBA")) or _text(row.get("BUSINESS_NAME"))
        structure = _text(row.get("LEGAL_STRUCTURE")).casefold()
        holder = (
            _text(row.get("BUSINESS_NAME"))
            if structure in {"corporation", "llc", "limited liability company"}
            else None
        )
        result.append(
            Observation(
                evidence=SourceEvidence(
                    **receipt, source_record_id=_text(row["LICENSE_NO"])
                ),
                name=label,
                kind="license",
                civic_address=civic,
                unit=_explicit_unit(
                    civic, row.get("ADDRESS2" if retail else "G7_ADDRESS2")
                ),
                category=_text(row.get("LICENSE_TYPE")) or None,
                legal_name=holder,
            )
        )
    return result


def load_layer(source: str, base: Path) -> list[Observation]:
    layer, town, record_id, name, address, category, kind = LAYERS[source]
    path = base / f"{source}.json"
    rows = json.loads(path.read_bytes())
    meta = json.loads((base / f"{source}.metadata.json").read_bytes())
    if "features" not in rows or rows.get("exceededTransferLimit"):
        raise ValueError(f"Incomplete {source} layer snapshot")
    epoch = meta.get("editingInfo", {}).get("dataLastEditDate")
    vintage = datetime.fromtimestamp(epoch / 1000, UTC).date() if epoch else None
    receipt = evidence(
        path, source, f"{layer}/query", vintage.isoformat() if vintage else None
    )
    result = []
    for feature in rows["features"]:
        row = feature["attributes"]
        if _text(row[town]).casefold() != "stoneham" or (
            source == "usda_snap" and row["State"] != "MA"
        ):
            raise ValueError(f"Out-of-scope {source} record")
        if source == "ma_child_care" and (
            row["PROG_TYPE"] != "Center-based Care"
            or row["LICENSED_STATUS"] != "Current"
        ):
            continue
        result.append(
            Observation(
                evidence=SourceEvidence(
                    **receipt, source_record_id=_text(row[record_id])
                ),
                name=_text(row[name]),
                kind=kind,
                civic_address=_text(row[address]),
                unit=_explicit_unit(row[address], row.get("Additonal_Address")),
                category=_text(row[category]),
                stale=bool(
                    vintage and (receipt["retrieved_at"].date() - vintage).days > 180
                ),
            )
        )
    return result


def load_seed(path: Path) -> list[Observation]:
    # This is a legacy discovery lead. The current snapshot is a repository CSV.
    receipt = evidence(
        path,
        "legacy_directory_seed",
        "https://github.com/vinod-git-diometric/um-world-model/blob/2d5097a/evaluation/benchmark-businesses.csv",
    )
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            Observation(
                evidence=SourceEvidence(**receipt, source_record_id=str(i)),
                name=row["business_name"],
                civic_address=row["source_address"],
                kind="directory",
                stale=True,
            )
            for i, row in enumerate(csv.DictReader(handle), start=2)
        ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "export_csv", "archive", "snapshot_dir", "seed", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--export-vintage", required=True)
    args = parser.parse_args()
    physical = build_physical_graph(
        args.manifest,
        args.export_csv,
        args.archive,
        export_vintage=args.export_vintage,
        export_retrieved_at=datetime.fromtimestamp(
            args.archive.stat().st_mtime, UTC
        ).isoformat(),
    )
    data = args.snapshot_dir
    observations = [
        *load_abcc(data / "abcc-retail-20261120.xls", retail=True),
        *load_abcc(data / "abcc-state-20261120.xlsx", retail=False),
        *load_seed(args.seed),
    ]
    for source in LAYERS:
        observations.extend(load_layer(source, data))
    graph = build_commercial_graph(observations, physical)
    args.output.mkdir(parents=True, exist_ok=False)
    for file, artifact in (
        ("physical-1.0.json", physical),
        ("commercial-1.0.json", graph),
    ):
        with (args.output / file).open("x", encoding="utf-8") as handle:
            json.dump(artifact, handle, sort_keys=True)
    print(
        json.dumps(
            {"physical": physical["counts"], "commercial": graph["counts"]}, indent=2
        )
    )


if __name__ == "__main__":
    main()
