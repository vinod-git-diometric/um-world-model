from um_world_model import __version__
from um_world_model.sources import load_source_catalog, validate_ontology


def test_version():
    assert __version__ == "0.1.0"


def test_phase_zero_contracts():
    assert load_source_catalog()["town"] == "Stoneham"
    assert (
        validate_ontology()["constraints"]["address_parcel_cardinality"]
        == "many-to-many"
    )
