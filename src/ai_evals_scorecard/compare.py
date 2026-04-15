from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from ai_evals_scorecard.models import ComparisonReport, RunReport, ThresholdFailure


def compare_reports(base: RunReport, candidate: RunReport) -> ComparisonReport:
    domain_keys = sorted(set(base.domain_scores.keys()) | set(candidate.domain_scores.keys()))
    domain_deltas = {
        key: round(candidate.domain_scores.get(key, 0.0) - base.domain_scores.get(key, 0.0), 3)
        for key in domain_keys
    }

    base_metrics = {item.key: item for item in base.metric_summaries}
    candidate_metrics = {item.key: item for item in candidate.metric_summaries}
    metric_keys = sorted(set(base_metrics.keys()) | set(candidate_metrics.keys()))
    metric_deltas = {
        key: round(candidate_metrics.get(key).value - base_metrics.get(key).value, 6)
        for key in metric_keys
        if key in base_metrics and key in candidate_metrics
    }

    base_failures = {failure.key: failure for failure in base.threshold_failures}
    candidate_failures = {failure.key: failure for failure in candidate.threshold_failures}

    newly_failed_keys = set(candidate_failures.keys()) - set(base_failures.keys())
    resolved_keys = set(base_failures.keys()) - set(candidate_failures.keys())

    newly_failed = [candidate_failures[key] for key in sorted(newly_failed_keys)]
    resolved = [base_failures[key] for key in sorted(resolved_keys)]

    return ComparisonReport(
        base_run_id=base.run_id,
        candidate_run_id=candidate.run_id,
        overall_delta=round(candidate.overall_score - base.overall_score, 3),
        domain_deltas=domain_deltas,
        metric_deltas=metric_deltas,
        newly_failed_thresholds=newly_failed,
        resolved_thresholds=resolved,
    )
