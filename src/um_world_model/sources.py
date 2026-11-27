"""Source registry and ontology contract validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_EVIDENCE_FIELDS = {
    "source_id",
    "source_record_id",
    "source_url",
    "retrieved_at",
    "raw_evidence_ref",
    "resolution_method",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_source_catalog(path: Path | None = None) -> dict[str, Any]:
    source_path = path or repository_root() / "sources" / "stoneham-source-catalog.yaml"
    with source_path.open(encoding="utf-8") as handle:
        catalog = yaml.safe_load(handle)
    validate_source_catalog(catalog)
    return catalog


def validate_source_catalog(catalog: dict[str, Any]) -> None:
    if (
        not catalog.get("version")
        or not catalog.get("town")
        or not catalog.get("state")
    ):
        raise ValueError("source catalog requires version, town, and state")
    sources = catalog.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("source catalog must contain sources")
    ids = [source.get("id") for source in sources]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError("source IDs must be present and unique")
    for source in sources:
        if not source.get("url") or not isinstance(source.get("phase"), int):
            raise ValueError(f"invalid source registration: {source.get('id')}")


def validate_ontology(path: Path | None = None) -> dict[str, Any]:
    ontology_path = path or repository_root() / "ontology" / "ontology-v0.1.yaml"
    with ontology_path.open(encoding="utf-8") as handle:
        ontology = yaml.safe_load(handle)
    entities = ontology.get("entities", {})
    if not {"Address", "Parcel", "Evidence"}.issubset(entities):
        raise ValueError("ontology requires Address, Parcel, and Evidence")
    evidence_fields = set(entities["Evidence"].get("fields", []))
    if not REQUIRED_EVIDENCE_FIELDS.issubset(evidence_fields):
        missing = sorted(REQUIRED_EVIDENCE_FIELDS - evidence_fields)
        raise ValueError(f"Evidence contract missing fields: {missing}")
    if (
        ontology.get("constraints", {}).get("address_parcel_cardinality")
        != "many-to-many"
    ):
        raise ValueError("address/parcel cardinality must remain many-to-many")
    return ontology


def phase_sources(phase: int = 1) -> list[dict[str, Any]]:
    return [
        source
        for source in load_source_catalog()["sources"]
        if source["phase"] <= phase
    ]
