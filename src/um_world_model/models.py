"""Validated data contracts for the Phase 0/1 pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ResolutionStatus = Literal[
    "accepted",
    "ambiguous",
    "not_found",
    "unknown",
    "not_applicable",
    "source_unavailable",
]


class Evidence(BaseModel):
    source_id: str
    source_record_id: str | None = None
    source_url: str
    retrieved_at: datetime
    source_vintage: str | None = None
    raw_evidence_ref: str
    raw_sha256: str
    resolution_method: str


class Snapshot(BaseModel):
    source_id: str
    url: str
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieved_at: datetime
    record_count: int = Field(ge=0)
    page: int | None = Field(default=None, ge=0)


class IngestionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    run_id: str
    town: str
    state: str
    started_at: datetime
    completed_at: datetime
    sources: dict[str, dict[str, Any]]
    snapshots: list[Snapshot]


class NormalizedAddress(BaseModel):
    address_id: str
    canonical_address: str
    normalized_address: str
    house_number: str | None = None
    street_name: str | None = None
    unit: str | None = None
    municipality: str
    postal_code: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    evidence: Evidence


class NormalizedParcel(BaseModel):
    parcel_id: str
    loc_id: str | None = None
    prop_id: str | None = None
    map_par_id: str | None = None
    site_address: str | None = None
    normalized_address: str | None = None
    municipality: str
    use_code: str | None = None
    source_vintage: str | None = None
    evidence: Evidence


class Resolution(BaseModel):
    address_id: str
    parcel_ids: list[str] = Field(default_factory=list)
    status: ResolutionStatus
    method: str
    score: float | None = Field(default=None, ge=0, le=100)
    candidate_parcel_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def accepted_requires_parcel_and_evidence(self) -> Resolution:
        if self.status == "accepted" and (not self.parcel_ids or not self.evidence):
            raise ValueError("accepted resolutions require parcel IDs and evidence")
        if self.status != "accepted" and self.parcel_ids:
            raise ValueError(
                "only accepted resolutions may contain resolved parcel IDs"
            )
        return self
