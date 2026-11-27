"""Deterministic, evidence-preserving address-to-parcel spatial resolution."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import LinearRing, MultiPolygon, Point, Polygon
from shapely.strtree import STRtree

from .ingest import load_manifest, verify_snapshots
from .normalize import iter_features, normalize_address
from .resolve import parse_evidence, read_rows


def esri_polygon(rings):
    """Convert clockwise ArcGIS shells and counterclockwise holes."""
    shells, holes = [], []
    for coordinates in rings:
        if len(coordinates) < 4:
            return None
        ring = LinearRing(coordinates)
        (holes if ring.is_ccw else shells).append(ring)
    outlines = [Polygon(shell) for shell in shells]
    assigned = [[] for _ in shells]
    for hole in holes:
        matches = [i for i, shell in enumerate(outlines) if shell.covers(Polygon(hole))]
        if not matches:
            return None
        owner = min(matches, key=lambda i: outlines[i].area)
        assigned[owner].append(hole)
    polygons = [
        Polygon(shell, interiors)
        for shell, interiors in zip(shells, assigned, strict=True)
    ]
    geometry = MultiPolygon(polygons)
    return geometry if not geometry.is_empty and geometry.is_valid else None


def decide(
    interior: set[str],
    boundary: set[str],
    text: set[str],
    linked: set[str],
    *,
    point_type: str | None = None,
) -> tuple[str, str]:
    if linked and not linked <= interior:
        return "abstained", "official_link_conflict"
    if boundary:
        return "abstained", "parcel_boundary"
    if len(interior) > 1:
        return "abstained", "overlapping_parcels"
    if not interior:
        return "abstained", "outside_mapped_parcels"
    if text and text != interior:
        return "abstained", "spatial_text_conflict"
    if point_type == "DBMP":
        return "abstained", "documented_multi_property_point"
    if point_type == "BMP" and not (text or linked):
        return "abstained", "building_multipoint_without_corroboration"
    if linked:
        return "accepted", "official_link_and_interior"
    return "accepted", "interior_and_text" if text else "unique_interior"


def _page_crs(manifest_path: Path) -> None:
    for snapshot in load_manifest(manifest_path).snapshots:
        if snapshot.page is None:
            continue
        page = json.loads((manifest_path.parent / snapshot.path).read_bytes())
        sr = page.get("spatialReference") or {}
        if sr.get("latestWkid", sr.get("wkid")) != 4326:
            raise ValueError(f"Expected EPSG:4326 in {snapshot.path}; got {sr}")


def civic_key(normalized: str | None) -> tuple[str, str] | None:
    number, _, street = (normalized or "").partition(" ")
    if number and number[0].isdigit() and street:
        return number, street
    return None


def resolve_spatial(manifest_path: Path) -> Path:
    verify_snapshots(manifest_path)
    _page_crs(manifest_path)
    normalized = manifest_path.parent / "normalized"
    parcel_rows = read_rows(normalized / "parcels.parquet")
    parcels = {
        parse_evidence(row["evidence"]).source_record_id: row for row in parcel_rows
    }
    by_text: dict[tuple[str, str], set[str]] = defaultdict(set)
    by_parcel: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in parcel_rows:
        if key := civic_key(row["normalized_address"]):
            by_text[key].add(row["parcel_id"])
        by_parcel[row["parcel_id"]].append(row)
    geometries, geometry_parcels = [], []
    invalid_parcels: set[str] = set()
    polygon_types = {}
    for feature, _ in iter_features(manifest_path, "massgis_parcels"):
        row = parcels[str(feature["attributes"]["OBJECTID"])]
        polygon_types[str(feature["attributes"]["OBJECTID"])] = feature[
            "attributes"
        ].get("POLY_TYPE")
        rings = (feature.get("geometry") or {}).get("rings")
        polygon = esri_polygon(rings) if rings else None
        if polygon is None:
            invalid_parcels.add(row["parcel_id"])
            continue
        geometries.append(polygon)
        geometry_parcels.append(row["parcel_id"])
    if not geometries:
        raise ValueError("Parcel geometry is required; ingest with --parcel-geometry")
    index = STRtree(geometries)

    address_rows = {
        row["address_id"]: row for row in read_rows(normalized / "addresses.parquet")
    }
    parcel_streets = {street for _, street in by_text}
    output = normalized / "spatial-resolutions.jsonl"
    with output.open("w", encoding="utf-8") as handle:
        for feature, _ in iter_features(manifest_path, "massgis_addresses"):
            attrs = feature["attributes"]
            address_id = str(attrs["MASTER_ADDRESS_ID"])
            if address_id not in address_rows:
                continue
            row = address_rows[address_id]
            interior, boundary = set(), set()
            civic = " ".join(
                part for part in (row["house_number"], row["street_name"]) if part
            )
            key = civic_key(normalize_address(civic))
            text = by_text.get(key, set())
            text_diagnostic = (
                "exact_civic_address"
                if text
                else "missing_structured_address"
                if key is None
                else "street_present_number_unmatched"
                if key[1] in parcel_streets
                else "street_unmatched"
            )
            loc_id = attrs.get("LOC_ID")
            linked = {str(loc_id)} if loc_id else set()
            has_point = row["longitude"] is not None and row["latitude"] is not None
            if has_point:
                point = Point(row["longitude"], row["latitude"])
                for i in index.query(point, predicate="intersects"):
                    target = interior if geometries[i].contains(point) else boundary
                    target.add(geometry_parcels[i])
            status, reason = decide(
                interior, boundary, text, linked, point_type=attrs.get("POINT_TYPE")
            )
            if not has_point:
                status, reason = "abstained", "missing_address_geometry"
            elif not interior and (text | linked) & invalid_parcels:
                status, reason = "abstained", "candidate_geometry_unusable"
            candidates = sorted(interior | boundary | text | linked)
            handle.write(
                json.dumps(
                    {
                        "address_id": address_id,
                        "unit": row["unit"],
                        "unit_type": attrs.get("UNIT_TYPE"),
                        "point_type": attrs.get("POINT_TYPE"),
                        "site_id": attrs.get("SITE_ID"),
                        "status": status,
                        "reason": reason,
                        "crs": "EPSG:4326",
                        "parcel_ids": sorted(interior) if status == "accepted" else [],
                        "interior": sorted(interior),
                        "boundary": sorted(boundary),
                        "text": sorted(text),
                        "text_diagnostic": text_diagnostic,
                        "official_loc_id": loc_id,
                        "candidate_parcel_ids": candidates,
                        "tax_rows": [
                            {
                                "parcel_id": candidate,
                                "prop_id": parcel["prop_id"],
                                "map_par_id": parcel["map_par_id"],
                                "polygon_type": polygon_types.get(
                                    json.loads(parcel["evidence"])["source_record_id"]
                                ),
                                "object_id": json.loads(parcel["evidence"])[
                                    "source_record_id"
                                ],
                            }
                            for candidate in candidates
                            for parcel in by_parcel.get(candidate, [])
                        ],
                        "evidence": [json.loads(row["evidence"])]
                        + [
                            json.loads(parcel["evidence"])
                            for candidate in candidates
                            for parcel in by_parcel.get(candidate, [])
                        ],
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    return output
