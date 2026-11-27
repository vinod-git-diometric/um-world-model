import pytest

from um_world_model.normalize import normalize_address


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
