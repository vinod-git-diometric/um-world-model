import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from um_world_model.resolve import load_resolutions, resolve_run


def evidence(source: str, record: str) -> str:
    return json.dumps(
        {
            "source_id": source,
            "source_record_id": record,
            "source_url": "https://example.test/layer/0",
            "retrieved_at": "2026-01-01T00:00:00Z",
            "source_vintage": "2026",
            "raw_evidence_ref": f"raw/{source}/page.json",
            "raw_sha256": "a" * 64,
            "resolution_method": "official_source_record",
        }
    )


def write_parquet(path: Path, rows: list[dict]):
    pq.write_table(pa.Table.from_pylist(rows), path)


def test_exact_shared_address_multiple_parcels_and_fuzzy_candidate(tmp_path):
    addresses = tmp_path / "addresses.parquet"
    parcels = tmp_path / "parcels.parquet"
    write_parquet(
        addresses,
        [
            {
                "address_id": "A1",
                "normalized_address": "10 MAIN ST",
                "evidence": evidence("addresses", "A1"),
            },
            {
                "address_id": "A2",
                "normalized_address": "10 MAIN ST",
                "evidence": evidence("addresses", "A2"),
            },
            {
                "address_id": "A3",
                "normalized_address": "12 MAINE ST",
                "evidence": evidence("addresses", "A3"),
            },
            {
                "address_id": "A4",
                "normalized_address": "999 ABSENT RD",
                "evidence": evidence("addresses", "A4"),
            },
        ],
    )
    write_parquet(
        parcels,
        [
            {
                "parcel_id": "P1",
                "normalized_address": "10 MAIN ST",
                "evidence": evidence("parcels", "P1"),
            },
            {
                "parcel_id": "P2",
                "normalized_address": "10 MAIN ST",
                "evidence": evidence("parcels", "P2"),
            },
        ],
    )
    output = resolve_run(addresses, parcels, candidate_threshold=70)
    results = {row.address_id: row for row in load_resolutions(output)}
    assert results["A1"].status == "accepted"
    assert results["A1"].parcel_ids == ["P1", "P2"]
    assert results["A2"].parcel_ids == ["P1", "P2"]
    assert results["A3"].status == "ambiguous"
    assert results["A3"].parcel_ids == []
    assert results["A3"].candidate_parcel_ids == ["P1", "P2"]
    assert results["A4"].status == "not_found"


def test_resolution_is_idempotent(tmp_path):
    addresses = tmp_path / "addresses.parquet"
    parcels = tmp_path / "parcels.parquet"
    write_parquet(
        addresses,
        [
            {
                "address_id": "A1",
                "normalized_address": "1 MAIN ST",
                "evidence": evidence("a", "A1"),
            }
        ],
    )
    write_parquet(
        parcels,
        [
            {
                "parcel_id": "P1",
                "normalized_address": "1 MAIN ST",
                "evidence": evidence("p", "P1"),
            }
        ],
    )
    output = resolve_run(addresses, parcels)
    first = output.read_bytes()
    resolve_run(addresses, parcels, output)
    assert output.read_bytes() == first
