from um_world_model.evaluate import evaluate_reference, wilson
from um_world_model.models import Resolution


def test_missing_reference_is_explicitly_unmeasured():
    result = evaluate_reference(None, {})
    assert result["audited_cases"] == 0
    assert result["precision"] is None
    assert result["precision_status"] == "not_measured_no_independent_reference_labels"


def test_wilson_interval_has_nonzero_uncertainty():
    low, high = wilson(9, 10)
    assert low < 0.9 < high


def test_accepted_resolution_requires_evidence():
    try:
        Resolution(address_id="A", parcel_ids=["P"], status="accepted", method="exact")
    except ValueError as error:
        assert "evidence" in str(error)
    else:
        raise AssertionError("accepted result without evidence must fail validation")
