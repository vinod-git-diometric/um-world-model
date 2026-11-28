"""Score frozen independent labels against separately generated predictions."""

from __future__ import annotations

import json
from pathlib import Path

from .evaluate import wilson


def score_audit(reference: Path, predictions: Path) -> dict:
    labels = json.loads(reference.read_text(encoding="utf-8"))
    outputs = json.loads(predictions.read_text(encoding="utf-8"))
    by_id = {row["case_id"]: row for row in outputs}
    if len(by_id) != len(outputs) or len({row["case_id"] for row in labels}) != len(
        labels
    ):
        raise ValueError("Duplicate audit or prediction case ID")
    report = {}
    for target in ("address", "parcel"):
        correct = accepted = auditable = excluded = 0
        for row in labels:
            expected = row.get(target)
            if expected is None:
                excluded += 1
                continue
            if (
                not isinstance(expected, list)
                or not expected
                or not all(
                    isinstance(value, str) and value.strip() for value in expected
                )
                or not row.get(f"{target}_evidence")
            ):
                raise ValueError(
                    f"Expected nonempty audited {target} values and evidence"
                )
            auditable += 1
            observed = by_id.get(row["case_id"], {}).get(target) or []
            if not isinstance(observed, list) or not all(
                isinstance(value, str) and value.strip() for value in observed
            ):
                raise ValueError(f"Expected a list of {target} prediction values")
            if observed:
                accepted += 1
                correct += set(observed) == set(expected)
        report[target] = {
            "auditable": auditable,
            "excluded": excluded,
            "accepted": accepted,
            "correct": correct,
            "precision": correct / accepted if accepted else None,
            "precision_interval_95": wilson(correct, accepted),
            "recall": correct / auditable if auditable else None,
            "recall_interval_95": wilson(correct, auditable),
        }
    return report
