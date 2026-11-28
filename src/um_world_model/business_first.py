"""Pinned Places extraction and conservative Phase 2.1 evidence evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import AwareDatetime, BaseModel, Field
from shapely.geometry import shape

from .commercial import link_physical, name_key
from .normalize import normalize_address
from .physical_graph import digest

RELEASE = "2026-11-18.0"
CATALOG = "https://stac.overturemaps.org"
BUCKET = "https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/"
BOUNDARY_URL = (
    "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/"
    "Massachusetts_Municipalities/FeatureServer/1/query"
)
COMMERCIAL_ROOTS = {
    "food_and_drink",
    "shopping",
    "retail",
    "services_and_business",
    "lifestyle_services",
    "health_care",
    "lodging",
    "automotive",
    "financial_services",
}
NONCOMMERCIAL = {
    "park",
    "playground",
    "cemetery",
    "public_library",
    "place_of_worship",
    "government_office",
    "public_school",
    "natural_feature",
    "mountain_peak",
}
CAPABILITIES = {
    "official_website",
    "catalog",
    "online_ordering",
    "ecommerce_checkout",
    "booking",
    "inquiry_form",
    "marketplace_link",
    "social_presence",
}


class FieldEvidence(BaseModel):
    field: str
    value: str = Field(min_length=1)
    source_url: str
    observed_at: AwareDatetime
    snapshot: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    lineage: str = Field(min_length=1)


class MerchantReview(BaseModel):
    business_id: str
    url: str
    checked_at: AwareDatetime
    status: Literal["policy_blocked", "unavailable", "verified", "identity_unverified"]
    diagnostic: str | None = None
    # This attests to a scoped page review, including checking for each capability.
    assessed_capabilities: bool = False
    fields: list[FieldEvidence] = Field(default_factory=list)


def boundary(path: Path):
    features = json.loads(path.read_bytes())["features"]
    if len(features) != 1 or features[0]["properties"]["TOWN_ID"] != 284:
        raise ValueError("Expected one official Stoneham boundary feature")
    geometry = shape(features[0]["geometry"])
    if (
        geometry.geom_type not in {"Polygon", "MultiPolygon"}
        or not geometry.is_valid
        or geometry.is_empty
    ):
        raise ValueError("Invalid Stoneham boundary")
    return geometry


def acquire_places(boundary_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    # Keep the managed HTTPS settings for the preflight. Do not use an alternate
    # transport to work around catalog or bucket access policy.
    bounds = ",".join(map(str, boundary(boundary_path).bounds))
    with httpx.Client(timeout=15) as client:
        for url, params in (
            (f"{CATALOG}/catalog.json", {}),
            (
                BUCKET,
                {
                    "list-type": "2",
                    "prefix": f"release/{RELEASE}/theme=places/type=place/",
                    "max-keys": "1",
                },
            ),
        ):
            try:
                client.get(url, params=params).raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(
                    f"Overture preflight failed for {url}: {exc}"
                ) from exc
    # The temporary output never becomes a valid snapshot on partial download.
    partial = output.with_suffix(".partial")
    if partial.exists():
        raise FileExistsError(partial)
    subprocess.run(
        [
            "overturemaps",
            "download",
            "--bbox",
            bounds,
            "--type",
            "place",
            "--release",
            RELEASE,
            "-f",
            "geojsonseq",
            "-o",
            str(partial),
        ],
        check=True,
    )
    partial.rename(output)


def place_scope(props: dict) -> str:
    hierarchy = (props.get("taxonomy") or {}).get("hierarchy") or []
    basic = props.get("basic_category")
    if {basic, *hierarchy} & NONCOMMERCIAL:
        return "noncommercial"
    if {basic, *hierarchy} & COMMERCIAL_ROOTS or basic in {
        "restaurant",
        "cafe",
        "bookstore",
        "grocery_store",
        "pharmacy",
    }:
        return "business_candidate"
    return "category_review"


def read_places(path: Path, boundary_path: Path) -> tuple[list[dict], dict]:
    town = boundary(boundary_path)
    rows = []
    counts: Counter = Counter()
    missing: Counter = Counter()
    seen = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not (line := line.strip("\x1e \t")):
            continue
        feature = json.loads(line)
        props = feature.get("properties") or {}
        place_id = feature.get("id") or props.get("id")
        if not place_id or place_id in seen:
            raise ValueError("Missing or duplicated Overture place ID")
        seen.add(place_id)
        point = shape(feature["geometry"]) if feature.get("geometry") else None
        if (
            point is None
            or point.geom_type != "Point"
            or point.is_empty
            or not point.is_valid
        ):
            counts["invalid_geometry"] += 1
            continue
        if not town.covers(point):
            counts["outside_town"] += 1
            continue
        counts["in_town"] += 1
        disposition = place_scope(props)
        if (
            disposition == "business_candidate"
            and props.get("operating_status") == "permanently_closed"
        ):
            disposition = "reported_closed_review"
        counts[disposition] += 1
        primary_name = (props.get("names") or {}).get("primary")
        record = {
            "id": place_id,
            "name": primary_name,
            "coordinates": [point.x, point.y],
            "basic_category": props.get("basic_category"),
            "taxonomy": props.get("taxonomy"),
            "addresses": props.get("addresses"),
            "websites": props.get("websites"),
            "sources": props.get("sources"),
            "confidence": props.get("confidence"),
            "operating_status": props.get("operating_status"),
            "disposition": disposition,
        }
        for key, value in record.items():
            if value is None or value == [] or value == "" or value == {}:
                missing[key] += 1
        rows.append(record)
    return rows, {
        "release": RELEASE,
        "sha256": digest(path),
        "boundary_sha256": digest(boundary_path),
        "counts": dict(counts),
        "missing_in_town_fields": dict(missing),
    }


def validate_review_snapshots(reviews: list[MerchantReview], root: Path) -> None:
    root = root.resolve()
    hashes = {}
    for field in (field for review in reviews for field in review.fields):
        file = (root / field.snapshot).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            raise ValueError("Field evidence must point to a retained review snapshot")
        if file not in hashes:
            hashes[file] = digest(file)
        if hashes[file] != field.sha256:
            raise ValueError("Merchant field evidence snapshot SHA-256 mismatch")


def place_key(place: dict) -> tuple[str, str] | None:
    addresses = {
        civic
        for address in place["addresses"] or []
        if address.get("country", "US") in {"US", None}
        and address.get("region", "MA") in {"MA", "US-MA", None}
        and (civic := normalize_address(address.get("freeform")))
    }
    if place["name"] and len(addresses) == 1:
        return name_key(place["name"]), next(iter(addresses))
    return None


def evaluate(
    commercial: dict,
    physical: dict,
    reviews: list[MerchantReview],
    places: list[dict] | None,
):
    observations = {o["id"]: o for o in commercial["observations"]}
    by_business = defaultdict(list)
    for review in reviews:
        by_business[review.business_id].append(review)
    occupancies = defaultdict(list)
    for row in commercial["occupancies"]:
        occupancies[row["business_id"]].append(row)
    geography = defaultdict(list)
    for edge in physical["address_parcel_edges"]:
        geography[edge["civic"]].append(edge)
    cases, index, site_counts = [], defaultdict(list), Counter()
    counts: Counter = Counter()
    distributions: Counter = Counter()
    for business in commercial["businesses"]:
        occs = occupancies[business["id"]]
        for row in occs:
            index[(name_key(business["name"]), row["civic"])].append(
                (business["id"], row.get("unit"))
            )
    if set(by_business) - (
        {b["id"] for b in commercial["businesses"]}
        | {"overture:" + place["id"] for place in places or []}
    ):
        raise ValueError("Review refers to an unknown business")
    candidate_rows = [(b, b["id"], None) for b in commercial["businesses"]]
    overlap_leads = defaultdict(list)
    net_new_keys = set()
    for place in places or []:
        if place["disposition"] != "business_candidate":
            continue
        key = place_key(place)
        matching = index.get(key, []) if key else []
        if len(matching) == 1 and not matching[0][1]:
            site_counts["exact_baseline_overlap"] += 1
            overlap_leads[matching[0][0]].append(place)
            continue
        site_counts[
            "ambiguous_overlap"
            if matching
            else (
                "nonoverlap_civic_candidate" if key else "unresolved_identity_or_civic"
            )
        ] += 1
        candidate_rows.append((None, "overture:" + place["id"], place))
        if key and not matching:
            net_new_keys.add(key)
    if places is not None:
        site_counts["distinct_nonoverlap_civic_candidate_keys"] = len(net_new_keys)
    for business, business_id, place in candidate_rows:
        source = (
            [observations[key] for key in business["observations"]] if business else []
        )
        assessed = by_business[business_id]
        fields = [
            field
            for review in assessed
            if review.status == "verified"
            for field in review.fields
        ]
        capabilities = {field.field for field in fields} & CAPABILITIES
        site_name = name_key((business["name"] if business else place["name"]) or "")
        website_reviews = [
            review
            for review in assessed
            if review.status == "verified"
            and any(
                f.field == "identity" and name_key(f.value) == site_name
                for f in review.fields
            )
            and any(f.field == "official_website" for f in review.fields)
        ]
        verified = bool(website_reviews)
        digital_assessed = any(
            review.assessed_capabilities for review in website_reviews
        )
        capabilities = {
            field.field
            for review in assessed
            if review.status == "verified"
            for field in review.fields
            if field.field in CAPABILITIES
            and (field.field != "official_website" or review in website_reviews)
        }
        civic_claims = defaultdict(set)
        for field in fields:
            if field.field == "premises" and (key := normalize_address(field.value)):
                host = urlsplit(field.source_url).hostname
                if host:
                    civic_claims[key].add((field.lineage, host.removeprefix("www.")))
        baseline_keys = {row["civic"] for row in occupancies[business_id]}
        corroborated = len(civic_claims) == 1 and any(
            len({lineage for lineage, _ in v}) >= 2
            and len({host for _, host in v}) >= 2
            for v in civic_claims.values()
        )
        conflict = len(civic_claims) > 1 or bool(
            civic_claims and baseline_keys and civic_claims.keys() != baseline_keys
        )
        if conflict:
            status = "conflicting_or_stale"
        elif corroborated and any(
            f.field == "merchant_confirmed_occupancy" for f in fields
        ):
            status = "merchant_confirmed_occupancy"
        elif corroborated and any(_recent_operation(f) for f in fields):
            status = "recently_evidenced_operation"
        elif corroborated:
            status = "corroborated_advertised_premises"
        elif source and all(o["stale"] for o in source):
            status = "conflicting_or_stale"
        else:
            status = "listed_business" if source or place else "unknown"
        link = None
        if corroborated and not conflict:
            unit_claims = {f.value for f in fields if f.field == "unit"}
            unit_claims.update(
                row["unit"] for row in occupancies[business_id] if row.get("unit")
            )
            if len(unit_claims) <= 1:
                link = link_physical(
                    geography[next(iter(civic_claims))], next(iter(unit_claims), None)
                )
        counts["evaluated"] += 1
        counts["merchant_sites_verified"] += verified
        counts["capability_assessments_completed"] += digital_assessed
        counts["corroborated"] += corroborated and not conflict
        counts["corroborated_with_parcels"] += bool(link and link["parcel_ids"])
        counts["cases_with_source_or_place_reference"] += bool(source or place)
        counts[status] += 1
        distributions.update(capabilities)
        cases.append(
            {
                "business_id": business_id,
                "status": status,
                "source_observation_ids": business["observations"] if business else [],
                "overture_id": place["id"] if place else None,
                "review_status": (
                    "verified"
                    if verified
                    else (assessed[-1].status if assessed else "no_verified_url_lead")
                ),
                "overture_overlap_ids": [p["id"] for p in overlap_leads[business_id]],
                "merchant_reviews": [r.model_dump(mode="json") for r in assessed],
                "capabilities": sorted(capabilities),
                "physical": link,
            }
        )
    return {
        "counts": dict(counts),
        "capabilities": dict(distributions),
        "overture_overlap": dict(site_counts) if places is not None else None,
        "cases": cases,
    }


def _recent_operation(field: FieldEvidence) -> bool:
    if field.field != "recent_operation":
        return False
    try:
        event = date.fromisoformat(field.value)
    except ValueError:
        return False
    return 0 <= (field.observed_at.date() - event).days <= 90


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boundary", type=Path)
    parser.add_argument("--fetch", type=Path)
    parser.add_argument("--places", type=Path)
    parser.add_argument("--graphs", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.fetch:
        acquire_places(args.boundary, args.fetch)
        return
    if not (args.graphs and args.output):
        parser.error("evaluation requires --graphs and --output")
    boundary(args.boundary)
    rows, metadata = (
        read_places(args.places, args.boundary) if args.places else (None, None)
    )

    def graph(filename):
        return json.loads((args.graphs / filename).read_bytes())

    reviews = (
        [
            MerchantReview.model_validate(r)
            for r in json.loads(args.reviews.read_bytes())
        ]
        if args.reviews
        else []
    )
    if args.reviews:
        validate_review_snapshots(reviews, args.reviews.parent)
    result = evaluate(
        graph("commercial-1.0.json"), graph("physical-1.0.json"), reviews, rows
    )
    result["overture"] = metadata
    result["places"] = rows
    result["boundary"] = {
        "url": BOUNDARY_URL,
        "sha256": digest(args.boundary),
        "town_id": 284,
    }
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in {"cases", "places"}}, indent=2
        )
    )


if __name__ == "__main__":
    main()
