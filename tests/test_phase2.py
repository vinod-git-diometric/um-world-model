from um_world_model.commercial import (
    Observation,
    SourceEvidence,
    build_commercial_graph,
)
from um_world_model.physical_graph import select_link


def test_authoritative_parcel_integrity_and_hybrid_fallback():
    assert select_link({"A"}, {"A", "B"}, set()) == ("accepted", "official_link", ["A"])
    assert select_link({"A"}, {"B"}, {"B"}) == (
        "unavailable",
        "official_parcel_missing",
        [],
    )
    assert select_link({"A"}, {"A", "B"}, {"B"}) == (
        "ambiguous",
        "official_hybrid_conflict",
        [],
    )
    assert select_link({"A"}, {"A"}, {"A"}, comparable=False)[0] == "ambiguous"
    assert select_link({"A", "B"}, {"A", "B"}, set())[0] == "ambiguous"
    assert select_link(set(), {"B"}, {"B"}) == ("accepted", "hybrid_fallback", ["B"])


def observation(i, kind, **values):
    return Observation(
        evidence=SourceEvidence(
            source="fixture",
            source_record_id=str(i),
            url="https://example.test/observation",
            retrieved_at="2026-11-27T14:00:00Z",
            sha256="1" * 64,
            snapshot="fixture",
        ),
        kind=kind,
        **values,
    )


def test_business_graph_keeps_tenants_and_registration_separate():
    physical = {
        "schema_version": "physical-1.0",
        "source_manifest": "fixture",
        "address_parcel_edges": [
            {"address_id": "A", "civic": "1 MAIN ST", "unit": "1", "parcel_ids": ["P"]},
            {"address_id": "B", "civic": "1 MAIN ST", "unit": "2", "parcel_ids": ["P"]},
        ],
    }
    observations = [
        observation(
            1,
            "license",
            name="Retail",
            civic_address="1 Main St",
            unit="1",
            legal_name="Holding LLC",
        ),
        observation(
            2,
            "operating_site",
            name="Retail",
            civic_address="1 MAIN STREET",
            unit="1",
            digital={
                "official_website": ["https://example.test/"],
                "ecommerce": ["https://example.test/shop"],
            },
        ),
        observation(
            3,
            "historical",
            name="Retail",
            civic_address="1 Main St",
            unit="1",
            valid_to="2020-12-31",
        ),
        observation(4, "license", name="Other tenant", civic_address="1 Main St"),
        observation(
            5,
            "registration",
            name="Holding LLC",
            civic_address="1 Main St",
            legal_name="Holding LLC",
        ),
        observation(6, "assessment", name="Example owner", civic_address="1 Main St"),
    ]
    result = build_commercial_graph(observations, physical)
    assert result["counts"]["business_site_candidates"] == 2
    assert result["counts"]["occupancy_statuses"] == {
        "candidate": 1,
        "confirmed": 1,
        "historical": 1,
    }
    assert result["counts"]["occupancy_address_statuses"] == {
        "ambiguous": 1,
        "linked": 2,
    }
    assert result["counts"]["occupancies_with_parcels"] == 3
    assert result["counts"]["businesses_with_verified_digital"] == 1
    assert len(result["legal_entities"]) == 1
    assert len(result["observations"]) == 6
    assert len(result["digital_properties"]) == 2
