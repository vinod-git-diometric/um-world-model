"""Normalize MassGIS records into stable Address and Parcel contracts."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .ingest import load_manifest, verify_snapshots
from .models import Evidence, NormalizedAddress, NormalizedParcel, Snapshot

SUFFIXES = {
    "STREET": "ST",
    "ST": "ST",
    "AVENUE": "AVE",
    "AVE": "AVE",
    "ROAD": "RD",
    "RD": "RD",
    "BOULEVARD": "BLVD",
    "BLVD": "BLVD",
    "DRIVE": "DR",
    "DR": "DR",
    "LANE": "LN",
    "LN": "LN",
    "COURT": "CT",
    "CT": "CT",
    "PLACE": "PL",
    "PL": "PL",
    "PARKWAY": "PKWY",
    "PKWY": "PKWY",
    "HIGHWAY": "HWY",
    "HWY": "HWY",
    "SQUARE": "SQ",
    "SQ": "SQ",
}
UNIT_RE = re.compile(
    r"\s+(?:APT|APARTMENT|UNIT|STE|SUITE|#)\s*[A-Z0-9-]+\s*$", re.IGNORECASE
)

ADDRESS_ID_FIELDS = [
    "ADDRESS_ID",
    "ADDRESSID",
    "ADDR_ID",
    "MASTER_ADDRESS_ID",
    "OBJECTID",
]
FULL_ADDRESS_FIELDS = [
    "FULL_ADDRESS",
    "FULLADDRESS",
    "FULL_ADDR",
    "ADDR_FULL",
    "SITE_ADDR",
    "ADDRESS",
]
HOUSE_FIELDS = [
    "FULL_NUMBER_STANDARDIZED",
    "HOUSE_NUMBER",
    "HOUSENUMBER",
    "FULL_NUMBER",
    "ADDR_NUM",
    "ST_NUM",
    "STREET_NO",
]
STREET_FIELDS = ["STREET_NAME", "ST_NAME", "STREET", "ROAD_NAME"]
UNIT_FIELDS = ["UNIT", "UNIT_NUMBER", "UNIT_NUM", "UNITNO", "SUB_ADDRESS"]
ZIP_FIELDS = ["POSTAL_CODE", "POSTCODE", "ZIP", "ZIPCODE"]
PARCEL_ID_FIELDS = ["LOC_ID", "PROP_ID", "MAP_PAR_ID", "PARCEL_ID", "OBJECTID"]


def clean_scalar(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text and text.casefold() not in {"none", "null", "nan"} else None


def first(attributes: dict[str, Any], candidates: list[str]) -> str | None:
    lookup = {key.upper(): value for key, value in attributes.items()}
    for candidate in candidates:
        value = clean_scalar(lookup.get(candidate.upper()))
        if value is not None:
            return value
    return None


def normalize_address(value: str | None) -> str | None:
    if not value:
        return None
    text = value.upper().replace("&", " AND ")
    text = UNIT_RE.sub("", text)
    text = re.sub(r"[^A-Z0-9\s-]", " ", text)
    tokens = text.split()
    tokens = [SUFFIXES.get(token, token) for token in tokens]
    return " ".join(tokens) or None


def compose_address(
    attributes: dict[str, Any],
) -> tuple[str | None, str | None, str | None, str | None]:
    full = first(attributes, FULL_ADDRESS_FIELDS)
    house = first(attributes, HOUSE_FIELDS)
    street = first(attributes, STREET_FIELDS)
    unit = first(attributes, UNIT_FIELDS)
    if not full and house and street:
        full = f"{house} {street}"
    return full, house, street, unit


def iter_features(
    manifest_path: Path, source_id: str
) -> Iterable[tuple[dict[str, Any], Snapshot]]:
    manifest = load_manifest(manifest_path)
    for snapshot in manifest.snapshots:
        if snapshot.source_id != source_id or snapshot.page is None:
            continue
        payload = json.loads(
            (manifest_path.parent / snapshot.path).read_text(encoding="utf-8")
        )
        for feature in payload.get("features", []):
            yield feature, snapshot


def geometry_coordinates(feature: dict[str, Any]) -> tuple[float | None, float | None]:
    geometry = feature.get("geometry") or {}
    x, y = geometry.get("x"), geometry.get("y")
    try:
        return (float(x), float(y)) if x is not None and y is not None else (None, None)
    except (TypeError, ValueError):
        return None, None


def evidence_for(
    source: dict[str, Any],
    source_id: str,
    snapshot: Snapshot,
    source_record_id: str | None,
) -> Evidence:
    return Evidence(
        source_id=source_id,
        source_record_id=source_record_id,
        source_url=source["layer_url"],
        retrieved_at=snapshot.retrieved_at,
        source_vintage=clean_scalar(source.get("source_vintage")),
        raw_evidence_ref=snapshot.path,
        raw_sha256=snapshot.sha256,
        resolution_method="official_source_record",
    )


def normalize_run(
    manifest_path: Path, output_dir: Path | None = None
) -> tuple[Path, Path]:
    verify_snapshots(manifest_path)
    manifest = load_manifest(manifest_path)
    target = output_dir or manifest_path.parent / "normalized"
    target.mkdir(parents=True, exist_ok=True)

    addresses: list[dict[str, Any]] = []
    for feature, snapshot in iter_features(manifest_path, "massgis_addresses"):
        attributes = feature.get("attributes", {})
        record_id = first(attributes, ADDRESS_ID_FIELDS)
        if record_id is None:
            raise ValueError("address record has no stable identifier")
        canonical, house, street, unit = compose_address(attributes)
        normalized = normalize_address(canonical)
        if not canonical or not normalized:
            continue
        longitude, latitude = geometry_coordinates(feature)
        model = NormalizedAddress(
            address_id=record_id,
            canonical_address=canonical,
            normalized_address=normalized,
            house_number=house,
            street_name=street,
            unit=unit,
            municipality=manifest.town,
            postal_code=first(attributes, ZIP_FIELDS),
            longitude=longitude,
            latitude=latitude,
            evidence=evidence_for(
                manifest.sources["massgis_addresses"],
                "massgis_addresses",
                snapshot,
                record_id,
            ),
        )
        row = model.model_dump(mode="json")
        row["evidence"] = json.dumps(row["evidence"], sort_keys=True)
        addresses.append(row)

    parcels: list[dict[str, Any]] = []
    for feature, snapshot in iter_features(manifest_path, "massgis_parcels"):
        attributes = feature.get("attributes", {})
        record_id = first(attributes, PARCEL_ID_FIELDS)
        if record_id is None:
            raise ValueError("parcel record has no stable identifier")
        site_address = first(attributes, FULL_ADDRESS_FIELDS)
        model = NormalizedParcel(
            parcel_id=record_id,
            loc_id=first(attributes, ["LOC_ID"]),
            prop_id=first(attributes, ["PROP_ID"]),
            map_par_id=first(attributes, ["MAP_PAR_ID"]),
            site_address=site_address,
            normalized_address=normalize_address(site_address),
            municipality=manifest.town,
            use_code=first(attributes, ["USE_CODE", "USECODE", "PROP_CLASS"]),
            source_vintage=first(attributes, ["FY", "FISCAL_YEAR", "YEAR"]),
            evidence=evidence_for(
                manifest.sources["massgis_parcels"],
                "massgis_parcels",
                snapshot,
                first(attributes, ["OBJECTID"]) or record_id,
            ),
        )
        row = model.model_dump(mode="json")
        row["evidence"] = json.dumps(row["evidence"], sort_keys=True)
        parcels.append(row)

    address_path = target / "addresses.parquet"
    parcel_path = target / "parcels.parquet"
    pq.write_table(pa.Table.from_pylist(addresses), address_path, compression="zstd")
    pq.write_table(pa.Table.from_pylist(parcels), parcel_path, compression="zstd")
    summary = {
        "run_id": manifest.run_id,
        "address_input_count": manifest.sources["massgis_addresses"]["observed_count"],
        "address_output_count": len(addresses),
        "parcel_input_count": manifest.sources["massgis_parcels"]["observed_count"],
        "parcel_output_count": len(parcels),
    }
    (target / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return address_path, parcel_path
