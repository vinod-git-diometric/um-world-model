import json

from um_world_model import linkage_validation
from um_world_model.assessor_validation import metrics


def test_assessor_agreement_keeps_abstentions_in_recall():
    result = metrics([{"A"}, {"B"}, {"C", "D"}], [{"A"}, set(), {"C"}])
    assert result["accepted"] == 2
    assert result["correct"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 1 / 3
    assert result["precision_interval_95"][0] < 0.5


def test_official_linkage_keeps_vintage_gaps_separate(tmp_path, monkeypatch):
    export = tmp_path / "export.csv"
    export.write_text(
        "ADDRESS_ID,LOC_ID,ADDR_NUM,STREETNAME\n"
        "1,P1,1,MAIN STREET\n2,OLD,2,MAIN STREET\n3,P1,9,MAIN STREET\n",
        encoding="utf-8",
    )
    addresses = [
        {"address_id": str(i), "normalized_address": f"{i} MAIN ST"}
        for i in (1, 2, 3, 4)
    ]
    monkeypatch.setattr(
        linkage_validation,
        "read_rows",
        lambda path: (
            addresses if path.name == "addresses.parquet" else [{"loc_id": "P1"}]
        ),
    )
    (tmp_path / "spatial-resolutions.jsonl").write_text(
        "".join(
            json.dumps(
                {
                    "address_id": str(i),
                    "status": "accepted",
                    "parcel_ids": ["P1"],
                    "reason": "unique_interior",
                }
            )
            + "\n"
            for i in (1, 2, 3, 4)
        ),
        encoding="utf-8",
    )
    result = linkage_validation.compare_linkage(export, tmp_path)
    assert result["outcomes"] == {
        "exact_parcel_set_agreement": 1,
        "export_loc_id_absent_from_parcel_snapshot": 1,
        "shared_id_civic_text_mismatch": 1,
        "hybrid_id_absent_from_export": 1,
    }
