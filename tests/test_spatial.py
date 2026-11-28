import json

import pytest

from um_world_model.audit import score_audit

pytest.importorskip("shapely")

from shapely.geometry import Point

from um_world_model.spatial import decide, esri_polygon


def test_polygon_hole_and_boundary():
    polygon = esri_polygon(
        [
            [(0, 0), (0, 5), (5, 5), (5, 0), (0, 0)],
            [(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)],
        ]
    )
    assert polygon.contains(Point(3, 3))
    assert not polygon.intersects(Point(1.5, 1.5))
    assert polygon.intersects(Point(0, 1)) and not polygon.contains(Point(0, 1))


@pytest.mark.parametrize(
    ("interior", "boundary", "text", "linked", "expected"),
    [
        ({"A"}, set(), {"A"}, set(), ("accepted", "interior_and_text")),
        ({"A", "B"}, set(), {"A"}, set(), ("abstained", "overlapping_parcels")),
        ({"A"}, {"B"}, set(), set(), ("abstained", "parcel_boundary")),
        ({"A"}, set(), {"B"}, set(), ("abstained", "spatial_text_conflict")),
        ({"A"}, set(), set(), {"B"}, ("abstained", "official_link_conflict")),
        (set(), set(), {"A"}, set(), ("abstained", "outside_mapped_parcels")),
    ],
)
def test_decisions(interior, boundary, text, linked, expected):
    assert decide(interior, boundary, text, linked) == expected


def test_multipoint_requires_corroboration_and_multi_property_abstains():
    assert decide({"A"}, set(), set(), set(), point_type="BMP")[0] == "abstained"
    assert decide({"A"}, set(), {"A"}, set(), point_type="BMP")[0] == "accepted"
    assert decide({"A"}, set(), {"A"}, set(), point_type="DBMP")[0] == "abstained"


def test_separate_audit_denominators(tmp_path):
    reference = tmp_path / "audit.json"
    predictions = tmp_path / "predictions.json"
    reference.write_text(
        json.dumps(
            [
                {
                    "case_id": "a",
                    "address": ["1 Main"],
                    "address_evidence": "record a",
                    "parcel": ["A", "B"],
                    "parcel_evidence": "map a",
                },
                {"case_id": "b", "address": ["2 Main"], "address_evidence": "record b"},
            ]
        )
    )
    predictions.write_text(
        json.dumps(
            [
                {"case_id": "a", "address": ["1 Main"], "parcel": ["A"]},
            ]
        )
    )
    result = score_audit(reference, predictions)
    assert result["address"]["precision"] == 1
    assert result["address"]["recall"] == 0.5
    assert result["parcel"]["precision"] == 0
    assert result["parcel"]["excluded"] == 1
