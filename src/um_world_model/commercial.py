"""Resolve public observations into a local commercial graph."""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from datetime import date
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from .normalize import normalize_address

DigitalKind = Literal[
    "official_website",
    "catalog",
    "ecommerce",
    "ordering_or_reservations",
    "third_party_marketplace",
]


class SourceEvidence(BaseModel):
    source: str
    source_record_id: str
    url: str
    retrieved_at: AwareDatetime
    vintage: str | None = None
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot: str


class Observation(BaseModel):
    evidence: SourceEvidence
    kind: Literal[
        "directory",
        "license",
        "authorization",
        "operating_site",
        "historical",
        "registration",
        "assessment",
    ]
    name: str
    civic_address: str | None = None
    unit: str | None = None
    legal_name: str | None = None
    category: str | None = None
    digital: dict[DigitalKind, list[str]] = Field(default_factory=dict)
    valid_from: date | None = None
    valid_to: date | None = None
    stale: bool = False


def name_key(value: str) -> str:
    return " ".join(re.findall(r"[^\W_]+", value.casefold()))


def business_key(obs: Observation) -> tuple[str, str, str]:
    return (
        name_key(obs.name),
        normalize_address(obs.civic_address) or "",
        name_key(obs.unit or ""),
    )


def stable_id(prefix: str, *values: str) -> str:
    payload = "\x1f".join(values).encode()
    return f"{prefix}:{hashlib.sha256(payload).hexdigest()[:24]}"


def link_physical(rows: list[dict], unit: str | None) -> dict:
    address_ids = sorted(row["address_id"] for row in rows)
    if unit:
        matching = [
            row for row in rows if name_key(row["unit"] or "") == name_key(unit)
        ]
        if not matching:
            return {
                "address_status": "unit_unverified",
                "candidate_address_ids": address_ids,
                "parcel_ids": [],
            }
        rows = matching
    if not rows:
        return {
            "address_status": "unknown",
            "candidate_address_ids": [],
            "parcel_ids": [],
        }
    sets = {tuple(row["parcel_ids"]) for row in rows}
    address_status = (
        "linked" if len(rows) == 1 and (unit or not rows[0]["unit"]) else "ambiguous"
    )
    return {
        "address_status": address_status,
        "address_ids": [rows[0]["address_id"]] if address_status == "linked" else [],
        "candidate_address_ids": address_ids,
        "parcel_ids": list(next(iter(sets))) if len(sets) == 1 else [],
    }


def is_historical(item: Observation) -> bool:
    return item.kind == "historical" or bool(
        item.valid_to and item.valid_to < item.evidence.retrieved_at.date()
    )


def build_commercial_graph(observations: list[Observation], physical: dict) -> dict:
    by_civic = defaultdict(list)
    for row in physical["address_parcel_edges"]:
        if row["civic"]:
            by_civic[row["civic"]].append(row)
    groups = defaultdict(list)
    source_businesses = defaultdict(set)
    source_rows = []
    legal = {}
    for item in observations:
        src = item.evidence
        obs_id = stable_id("obs", src.source, src.source_record_id, src.sha256)
        source_rows.append({"id": obs_id, **item.model_dump(mode="json")})
        if item.kind not in {"registration", "assessment"} and all(
            business_key(item)[:2]
        ):
            groups[business_key(item)].append((obs_id, item))
            source_businesses[src.source].add(business_key(item))
        if item.legal_name:
            # Names are source-scoped without a verified registry crosswalk.
            key = stable_id("legal", src.source, name_key(item.legal_name))
            node = legal.setdefault(
                key,
                {
                    "id": key,
                    "name": item.legal_name,
                    "jurisdiction": None,
                    "evidence": [],
                },
            )
            node["evidence"].append(obs_id)
    businesses, occupancies, digital, categories = [], [], [], {}
    groups_by_civic = defaultdict(list)
    for key, entries in sorted(groups.items()):
        business_id = stable_id("business", *key)
        civic = key[1]
        groups_by_civic[civic].append(business_id)
        businesses.append(
            {
                "id": business_id,
                "name": entries[0][1].name,
                "resolution_method": "same_normalized_name_civic_and_unit",
                "observations": [obs_id for obs_id, _ in entries],
            }
        )
        for obs_id, item in entries:
            if item.legal_name:
                businesses[-1].setdefault("legal_entity_claims", []).append(
                    {
                        "id": stable_id(
                            "legal", item.evidence.source, name_key(item.legal_name)
                        ),
                        "evidence": obs_id,
                    }
                )
            if item.category:
                category_id = stable_id(
                    "category", item.evidence.source, name_key(item.category)
                )
                categories[category_id] = {
                    "id": category_id,
                    "label": item.category,
                    "taxonomy": item.evidence.source,
                }
                businesses[-1].setdefault("categories", []).append(
                    {"id": category_id, "evidence": obs_id}
                )
            for feature, urls in item.digital.items():
                for url in urls:
                    digital.append(
                        {
                            "id": stable_id("digital", business_id, feature, url),
                            "business_id": business_id,
                            "kind": feature,
                            "url": url,
                            "evidence": obs_id,
                        }
                    )
        for historical in (False, True):
            relevant = [(i, v) for i, v in entries if is_historical(v) == historical]
            if not relevant:
                continue
            status = (
                "historical"
                if historical
                else (
                    "confirmed"
                    if any(
                        v.kind == "operating_site" and not v.stale for _, v in relevant
                    )
                    else "candidate"
                )
            )
            occupancies.append(
                {
                    "id": stable_id("occupancy", business_id, status),
                    "business_id": business_id,
                    "civic": civic,
                    "unit": entries[0][1].unit,
                    "status": status,
                    "evidence": [i for i, _ in relevant],
                    "period_claims": [
                        {
                            "evidence": i,
                            "valid_from": v.valid_from.isoformat()
                            if v.valid_from
                            else None,
                            "valid_to": v.valid_to.isoformat() if v.valid_to else None,
                        }
                        for i, v in relevant
                        if v.valid_from or v.valid_to
                    ],
                    **link_physical(by_civic[civic], entries[0][1].unit),
                }
            )
    digital_ids = {node["business_id"] for node in digital}
    for node in businesses:
        node["digital_status"] = (
            "observed" if node["id"] in digital_ids else "no_verified_digital_presence"
        )
    return {
        "schema_version": "commercial-1.0",
        "physical_graph_version": physical["schema_version"],
        "source_manifest": physical["source_manifest"],
        "source_manifest_sha256": physical.get("source_manifest_sha256"),
        "observations": source_rows,
        "businesses": businesses,
        "occupancies": occupancies,
        "legal_entities": list(legal.values()),
        "digital_properties": digital,
        "business_categories": list(categories.values()),
        "shared_civic_candidates": [
            {
                "civic": civic,
                "business_ids": keys,
                "status": "multiple_businesses_or_aliases",
            }
            for civic, keys in groups_by_civic.items()
            if len(keys) > 1
        ],
        "counts": {
            "observations": len(source_rows),
            "observations_by_source": dict(
                Counter(row["evidence"]["source"] for row in source_rows)
            ),
            "distinct_business_site_keys_by_source": {
                src: len(keys) for src, keys in source_businesses.items()
            },
            "business_site_candidates": len(businesses),
            "occupancy_statuses": dict(Counter(row["status"] for row in occupancies)),
            "occupancy_address_statuses": dict(
                Counter(row["address_status"] for row in occupancies)
            ),
            "occupancies_with_parcels": sum(
                bool(row["parcel_ids"]) for row in occupancies
            ),
            "stale_observations": sum(row["stale"] for row in source_rows),
            "historical_observations": sum(
                row["kind"] == "historical" for row in source_rows
            ),
            "businesses_with_verified_digital": len(digital_ids),
            "shared_civic_groups": sum(
                len(keys) > 1 for keys in groups_by_civic.values()
            ),
        },
    }
