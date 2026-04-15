from __future__ import annotations

import hashlib
import random

from ai_evals_scorecard.models import DatasetRow


def evaluate_metric(case: DatasetRow, metric_name: str) -> float:
    rng = random.Random(_seed_for(case.case_id, case.task_type, metric_name))

    if "latency" in metric_name:
        return round(1200.0 + rng.random() * 1600.0, 3)
    if "cost" in metric_name and metric_name.endswith("_usd"):
        return round(0.015 + rng.random() * 0.06, 6)
    if metric_name == "policy_compliance":
        return round(0.9 + rng.random() * 0.1, 4)
    if metric_name == "workflow_completion":
        return round(0.75 + rng.random() * 0.25, 4)
    if metric_name == "answer_correctness":
        return round(0.7 + rng.random() * 0.3, 4)
    return round(rng.random(), 4)


def _seed_for(case_id: str, task_type: str, metric_name: str) -> int:
    key = f"{case_id}|{task_type}|{metric_name}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    return int(digest[:16], 16)
