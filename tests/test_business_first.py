import json

import pytest

pytest.importorskip("shapely")

from um_world_model.business_first import MerchantReview, evaluate, read_places


def test_places_uses_polygon_and_keeps_unknown_taxonomy(tmp_path):
    border = tmp_path / "boundary.json"
    border.write_text(
        json.dumps(
            {
                "features": [
                    {
                        "properties": {"TOWN_ID": 284},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [2, 0], [0, 2], [0, 0]]],
                        },
                    }
                ]
            }
        )
    )
    examples = [
        ("food", [0.5, 0.5], {"taxonomy": {"hierarchy": ["food_and_drink"]}}),
        ("neighbor", [1.5, 1.5], {"basic_category": "restaurant"}),
        ("park", [0.2, 0.2], {"basic_category": "park"}),
        ("review", [0.1, 0.1], {}),
    ]
    source = tmp_path / "places.jsonseq"
    source.write_text(
        "\n".join(
            json.dumps(
                {
                    "id": key,
                    "geometry": {"type": "Point", "coordinates": xy},
                    "properties": props,
                }
            )
            for key, xy, props in examples
        )
    )
    rows, report = read_places(source, border)
    assert [r["id"] for r in rows] == ["food", "park", "review"]
    assert report["counts"] == {
        "in_town": 3,
        "business_candidate": 1,
        "category_review": 1,
        "noncommercial": 1,
        "outside_town": 1,
    }
    assert report["missing_in_town_fields"]["websites"] == 3


def test_merchant_website_does_not_confirm_occupancy():
    graph = {
        "businesses": [{"id": "b", "name": "Example Books", "observations": ["o"]}],
        "observations": [{"id": "o", "stale": False}],
        "occupancies": [{"business_id": "b", "civic": "1 MAIN ST"}],
    }
    physical = {
        "address_parcel_edges": [
            {
                "address_id": "a",
                "civic": "1 MAIN ST",
                "parcel_ids": ["p"],
                "unit": None,
            }
        ]
    }

    def field(label, value, site="https://merchant.test", lineage="merchant"):
        return {
            "field": label,
            "value": value,
            "source_url": site,
            "lineage": lineage,
            "observed_at": "2026-11-27T15:00:00Z",
            "sha256": "a" * 64,
            "snapshot": "test.txt",
        }

    fields = [
        field("identity", "Example Books"),
        field("official_website", "https://merchant.test/"),
        field("catalog", "public product listings"),
        field("premises", "1 Main Street"),
    ]

    def review(evidence):
        return MerchantReview.model_validate(
            {
                "business_id": "b",
                "status": "verified",
                "url": "https://merchant.test",
                "checked_at": "2026-11-27T15:00:00Z",
                "assessed_capabilities": True,
                "fields": evidence,
            }
        )

    result = evaluate(graph, physical, [review(fields)], None)
    assert result["counts"]["merchant_sites_verified"] == 1
    assert result["counts"]["corroborated"] == 0
    assert result["capabilities"] == {"official_website": 1, "catalog": 1}
    result = evaluate(
        graph,
        physical,
        [
            review(
                fields
                + [
                    field(
                        "premises",
                        "1 Main Street",
                        "https://directory.test",
                        "directory",
                    ),
                ]
            )
        ],
        None,
    )
    assert result["cases"][0]["status"] == "corroborated_advertised_premises"
    assert result["cases"][0]["physical"]["parcel_ids"] == ["p"]
    result = evaluate(
        graph,
        physical,
        [
            review(
                fields
                + [
                    field(
                        "premises",
                        "2 Main Street",
                        "https://directory.test",
                        "directory",
                    ),
                ]
            )
        ],
        None,
    )
    assert result["cases"][0]["status"] == "conflicting_or_stale"
    assert result["cases"][0]["physical"] is None
