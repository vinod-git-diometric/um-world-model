import pytest

from um_world_model.ingest import town_filter
from um_world_model.normalize import compose_address, normalize_address


def test_live_massgis_address_schema():
    metadata = {
        "fields": [{"name": "GEOGRAPHIC_TOWN_ID", "type": "esriFieldTypeInteger"}]
    }
    assert town_filter(metadata, "Stoneham") == (
        "GEOGRAPHIC_TOWN_ID",
        "GEOGRAPHIC_TOWN_ID=284",
    )
    assert compose_address(
        {"FULL_NUMBER_STANDARDIZED": "12A", "STREET_NAME": "Example St", "UNIT": "2"}
    ) == ("12A Example St", "12A", "Example St", "2")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("263 Main Street", "263 MAIN ST"),
        ("263 Main St.", "263 MAIN ST"),
        ("380 Main Street Suite 2", "380 MAIN ST"),
        ("99D Main Street #4", "99D MAIN ST"),
        ("5 Central Square", "5 CENTRAL SQ"),
        (None, None),
        ("", None),
    ],
)
def test_normalize_address_suffixes_units_and_nulls(raw, expected):
    assert normalize_address(raw) == expected
