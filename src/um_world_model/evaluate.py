"""Auditable benchmark evaluation with explicit unknown/unmeasured outcomes."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .normalize import normalize_address
from .resolve import load_resolutions


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float] | None:
    if total == 0:
        return None
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total)
        / denominator
    )
    return max(0.0, centre - margin), min(1.0, centre + margin)


def split_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.replace(";", "|").split("|") if part.strip()}


def evaluate_reference(
    reference_path: Path | None, resolution_by_id: dict[str, Any]
) -> dict[str, Any]:
    if reference_path is None or not reference_path.exists():
        return {
            "reference_file": None,
            "audited_cases": 0,
            "precision": None,
            "recall": None,
            "precision_status": "not_measured_no_independent_reference_labels",
            "recall_status": "not_measured_no_independent_reference_labels",
        }
    with reference_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    audited = [
        row for row in rows if row.get("audit_status", "").casefold() == "audited"
    ]
    accepted = correct = resolved_correct = 0
    for row in audited:
        expected = split_ids(row.get("expected_parcel_ids"))
        prediction = resolution_by_id.get(row.get("address_id", ""))
        if prediction and prediction.status == "accepted":
            accepted += 1
            if set(prediction.parcel_ids) == expected:
                correct += 1
                resolved_correct += 1
    return {
        "reference_file": str(reference_path),
        "reference_rows": len(rows),
        "audited_cases": len(audited),
        "accepted_predictions": accepted,
        "correct_accepted_predictions": correct,
        "precision": correct / accepted if accepted else None,
        "precision_interval_95": wilson(correct, accepted),
        "recall": resolved_correct / len(audited) if audited else None,
        "recall_interval_95": wilson(resolved_correct, len(audited)),
        "precision_status": "measured"
        if accepted
        else "not_measured_no_accepted_predictions",
        "recall_status": "measured"
        if audited
        else "not_measured_no_independent_reference_labels",
    }


def exploratory_seed_metrics(
    seed_path: Path, address_path: Path, resolution_by_id: dict[str, Any]
) -> dict[str, Any]:
    with seed_path.open(newline="", encoding="utf-8") as handle:
        seeds = list(csv.DictReader(handle))
    addresses = pq.read_table(address_path).to_pylist()
    address_ids_by_value: dict[str, set[str]] = defaultdict(set)
    for address in addresses:
        address_ids_by_value[address["normalized_address"]].add(address["address_id"])
    found = chain_accepted = ambiguous = 0
    diagnostics: list[dict[str, Any]] = []
    for seed in seeds:
        normalized = normalize_address(seed.get("source_address"))
        address_ids = address_ids_by_value.get(normalized or "", set())
        if address_ids:
            found += 1
        accepted = [
            resolution_by_id[address_id]
            for address_id in address_ids
            if address_id in resolution_by_id
            and resolution_by_id[address_id].status == "accepted"
        ]
        if accepted:
            chain_accepted += 1
        if len(address_ids) > 1:
            ambiguous += 1
        diagnostics.append(
            {
                "business_name": seed.get("business_name"),
                "source_address": seed.get("source_address"),
                "normalized_address": normalized,
                "address_candidate_count": len(address_ids),
                "parcel_chain_status": "accepted"
                if accepted
                else ("address_only" if address_ids else "not_found"),
            }
        )
    return {
        "seed_rows": len(seeds),
        "seed_label_status": "discovery_input_not_ground_truth",
        "exact_address_found": found,
        "exact_address_coverage": found / len(seeds) if seeds else None,
        "parcel_chain_accepted": chain_accepted,
        "parcel_chain_coverage": chain_accepted / len(seeds) if seeds else None,
        "multi_candidate_addresses": ambiguous,
        "precision": None,
        "precision_status": "not_measured_seed_is_not_ground_truth",
        "diagnostics": diagnostics,
    }


def evaluate_run(
    address_path: Path,
    resolution_path: Path,
    seed_path: Path,
    output_dir: Path,
    reference_path: Path | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    resolutions = load_resolutions(resolution_path)
    by_id = {resolution.address_id: resolution for resolution in resolutions}
    statuses: dict[str, int] = defaultdict(int)
    provenance_complete = 0
    for resolution in resolutions:
        statuses[resolution.status] += 1
        if resolution.evidence and all(
            evidence.source_id
            and evidence.source_url
            and evidence.retrieved_at
            and evidence.raw_evidence_ref
            and evidence.raw_sha256
            and evidence.resolution_method
            for evidence in resolution.evidence
        ):
            provenance_complete += 1
    reference = evaluate_reference(reference_path, by_id)
    seed = exploratory_seed_metrics(seed_path, address_path, by_id)
    accepted = statuses["accepted"]
    gate_a_pass = bool(
        reference.get("audited_cases", 0) >= 50
        and reference.get("precision") is not None
        and reference["precision"] >= 0.95
        and reference.get("recall") is not None
        and reference["recall"] >= 0.90
        and provenance_complete == len(resolutions)
    )
    report = {
        "evaluation_protocol": "Gate A v1",
        "address_parcel_resolutions": len(resolutions),
        "status_counts": dict(sorted(statuses.items())),
        "accepted_coverage": accepted / len(resolutions) if resolutions else None,
        "provenance_complete": provenance_complete,
        "provenance_denominator": len(resolutions),
        "provenance_completeness": provenance_complete / len(resolutions)
        if resolutions
        else None,
        "independent_reference": reference,
        "exploratory_business_seed": seed,
        "gate_a": {
            "passed": gate_a_pass,
            "required_audited_cases": 50,
            "required_precision": 0.95,
            "required_recall": 0.90,
            "stop_for_review": True,
            "decision": "PASS" if gate_a_pass else "NOT_MET",
        },
        "limitations": [
            "The 16-row business seed is discovery input, not ground truth.",
            "Fuzzy address similarity creates candidates only and is never accepted automatically.",
            "Precision and recall remain unmeasured without independently audited labels.",
        ],
    }
    json_path = output_dir / "gate-a-results.json"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown = render_markdown(report)
    markdown_path = output_dir / "gate-a-report.md"
    markdown_path.write_text(markdown, encoding="utf-8")
    return markdown_path


def metric(value: float | None) -> str:
    return "not measured" if value is None else f"{value:.1%}"


def render_markdown(report: dict[str, Any]) -> str:
    ref = report["independent_reference"]
    seed = report["exploratory_business_seed"]
    gate = report["gate_a"]
    return f"""# Gate A benchmark report

## Decision

**{gate["decision"]}**. Work stops at Gate A for architectural review.

## Official-source resolution

- Address records evaluated: {report["address_parcel_resolutions"]}
- Accepted address-to-parcel coverage: {metric(report["accepted_coverage"])}
- Provenance completeness: {report["provenance_complete"]}/{report["provenance_denominator"]} ({metric(report["provenance_completeness"])})
- Status counts: `{json.dumps(report["status_counts"], sort_keys=True)}`

## Independently audited benchmark

- Audited cases: {ref["audited_cases"]} (minimum required: 50)
- Precision: {metric(ref.get("precision"))}
- Recall: {metric(ref.get("recall"))}
- Precision status: `{ref["precision_status"]}`
- Recall status: `{ref["recall_status"]}`

The acceptance thresholds are precision >= 95%, recall >= 90%, and provenance = 100%. The thresholds are not treated as passed when a metric is unmeasured.

## Exploratory seed (not ground truth)

- Rows: {seed["seed_rows"]}
- Exact address coverage: {seed["exact_address_found"]}/{seed["seed_rows"]} ({metric(seed["exact_address_coverage"])})
- Accepted parcel-chain coverage: {seed["parcel_chain_accepted"]}/{seed["seed_rows"]} ({metric(seed["parcel_chain_coverage"])})
- Precision: not measured; agreement with an input source is not an independent audit.

## Limitations

""" + "".join(f"- {item}\n" for item in report["limitations"])
