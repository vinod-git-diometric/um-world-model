"""Official MassGIS ingestion with raw snapshots, hashes, and count reconciliation."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .arcgis import (
    ArcGISClient,
    ArcGISError,
    choose_field,
    find_feature_layer_url,
    sql_string,
)
from .models import IngestionManifest, Snapshot

ADDRESS_ITEM_ID = "c33281538f854507a90351760c3468fc"
ARCGIS_ITEM_URL = f"https://www.arcgis.com/sharing/rest/content/items/{ADDRESS_ITEM_ID}"
PARCEL_LAYER_URL = (
    "https://services1.arcgis.com/hGdibHYSPO59RG1h/ArcGIS/rest/services/"
    "Massachusetts_Property_Tax_Parcels/FeatureServer/0"
)
STONEHAM_TOWN_ID = 284

TOWN_FIELDS = ["MUNICIPALITY", "MUNI", "TOWN", "CITY", "CITY_TOWN", "LOC_CITY"]
TOWN_ID_FIELDS = [
    "GEOGRAPHIC_TOWN_ID",
    "TOWN_ID",
    "TOWNID",
    "MUNI_ID",
    "MUNICIPALITY_ID",
]


def utc_now() -> datetime:
    return datetime.now(UTC)


def json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()


def write_snapshot(
    root: Path,
    source_id: str,
    name: str,
    payload: dict[str, Any],
    *,
    url: str,
    retrieved_at: datetime,
    record_count: int,
    page: int | None = None,
) -> Snapshot:
    directory = root / "raw" / source_id
    directory.mkdir(parents=True, exist_ok=True)
    content = json_bytes(payload)
    digest = hashlib.sha256(content).hexdigest()
    path = directory / name
    path.write_bytes(content)
    return Snapshot(
        source_id=source_id,
        url=url,
        path=str(path.relative_to(root)),
        sha256=digest,
        retrieved_at=retrieved_at,
        record_count=record_count,
        page=page,
    )


def field_type(metadata: dict[str, Any], field_name: str) -> str:
    for field in metadata.get("fields", []):
        if str(field.get("name", "")).upper() == field_name.upper():
            return str(field.get("type", ""))
    return ""


def town_filter(metadata: dict[str, Any], town: str) -> tuple[str, str]:
    town_id_field = choose_field(metadata, TOWN_ID_FIELDS, required=False)
    if town_id_field:
        if "String" in field_type(metadata, town_id_field):
            return (
                town_id_field,
                f"{town_id_field}={sql_string(str(STONEHAM_TOWN_ID))}",
            )
        return town_id_field, f"{town_id_field}={STONEHAM_TOWN_ID}"
    town_name_field = choose_field(metadata, TOWN_FIELDS, required=False)
    if town_name_field:
        return town_name_field, f"UPPER({town_name_field}) = {sql_string(town.upper())}"
    raise ArcGISError("layer exposes no recognized municipality field")


def _ingest_layer(
    client: ArcGISClient,
    root: Path,
    source_id: str,
    layer_url: str,
    town: str,
    snapshots: list[Snapshot],
) -> dict[str, Any]:
    metadata_time = utc_now()
    metadata = client.layer_metadata(layer_url)
    snapshots.append(
        write_snapshot(
            root,
            source_id,
            "layer-metadata.json",
            metadata,
            url=layer_url,
            retrieved_at=metadata_time,
            record_count=len(metadata.get("fields", [])),
        )
    )
    town_field, where = town_filter(metadata, town)
    expected = client.count(layer_url, where)
    observed = 0
    page_count = 0
    query_options = {}
    if source_id == "massgis_parcels":
        wanted = {
            "MAP_PAR_ID",
            "LOC_ID",
            "PROP_ID",
            "SITE_ADDR",
            "USE_CODE",
            "FY",
            "TOWN_ID",
        }
        wanted.add(metadata.get("objectIdField") or metadata.get("objectIdFieldName"))
        query_options["out_fields"] = ",".join(
            field["name"] for field in metadata["fields"] if field["name"] in wanted
        )
        query_options["return_geometry"] = False
    for page_count, page in enumerate(
        client.pages(layer_url, where, **query_options), start=1
    ):
        retrieved_at = utc_now()
        observed += len(page.features)
        snapshots.append(
            write_snapshot(
                root,
                source_id,
                f"page-{page_count:05d}.json",
                page.response,
                url=f"{layer_url}/query",
                retrieved_at=retrieved_at,
                record_count=len(page.features),
                page=page_count,
            )
        )
    if observed != expected:
        raise ArcGISError(
            f"{source_id}: expected {expected} records, received {observed}"
        )
    return {
        "layer_url": layer_url,
        "layer_name": metadata.get("name"),
        "service_description": metadata.get("serviceDescription"),
        "current_version": metadata.get("currentVersion"),
        "copyright": metadata.get("copyrightText"),
        "object_id_field": metadata.get("objectIdField")
        or metadata.get("objectIdFieldName"),
        "town_field": town_field,
        "where": where,
        "expected_count": expected,
        "observed_count": observed,
        "page_count": page_count,
        "fields": [field.get("name") for field in metadata.get("fields", [])],
        "status": "complete",
    }


def ingest_town(data_dir: Path, town: str = "Stoneham", state: str = "MA") -> Path:
    """Ingest both official Phase 1 layers and return the manifest path."""
    if town.casefold() != "stoneham" or state.upper() != "MA":
        raise ValueError("Phase 1 is scoped to Stoneham, MA")
    started = utc_now()
    run_id = started.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    run_root = data_dir / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    snapshots: list[Snapshot] = []
    sources: dict[str, dict[str, Any]] = {}
    with ArcGISClient() as client:
        item_time = utc_now()
        item = client.get_json(ARCGIS_ITEM_URL, {"f": "json"})
        snapshots.append(
            write_snapshot(
                run_root,
                "massgis_addresses",
                "arcgis-item.json",
                item,
                url=ARCGIS_ITEM_URL,
                retrieved_at=item_time,
                record_count=1,
            )
        )
        try:
            address_layer = find_feature_layer_url(item, {})
        except ArcGISError:
            item_data = client.get_json(f"{ARCGIS_ITEM_URL}/data", {"f": "json"})
            snapshots.append(
                write_snapshot(
                    run_root,
                    "massgis_addresses",
                    "arcgis-item-data.json",
                    item_data,
                    url=f"{ARCGIS_ITEM_URL}/data",
                    retrieved_at=utc_now(),
                    record_count=1,
                )
            )
            address_layer = find_feature_layer_url(item, item_data)
        sources["massgis_addresses"] = _ingest_layer(
            client, run_root, "massgis_addresses", address_layer, town, snapshots
        )
        sources["massgis_addresses"]["arcgis_item_id"] = ADDRESS_ITEM_ID
        sources["massgis_parcels"] = _ingest_layer(
            client, run_root, "massgis_parcels", PARCEL_LAYER_URL, town, snapshots
        )
    manifest = IngestionManifest(
        run_id=run_id,
        town=town,
        state=state,
        started_at=started,
        completed_at=utc_now(),
        sources=sources,
        snapshots=snapshots,
    )
    manifest_path = run_root / "manifest.json"
    manifest_path.write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    latest = data_dir / "latest-run.txt"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(run_id + "\n", encoding="utf-8")
    return manifest_path


def load_manifest(path: Path) -> IngestionManifest:
    return IngestionManifest.model_validate_json(path.read_text(encoding="utf-8"))


def verify_snapshots(manifest_path: Path) -> None:
    manifest = load_manifest(manifest_path)
    root = manifest_path.parent
    for snapshot in manifest.snapshots:
        path = root / snapshot.path
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != snapshot.sha256:
            raise ValueError(f"snapshot hash mismatch: {path}")
