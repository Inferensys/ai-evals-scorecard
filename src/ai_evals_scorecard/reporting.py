from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Mapping

from ai_evals_scorecard.models import CaseEvaluation, CaseSummary, RunReport
from ai_evals_scorecard.scoring import AggregationResult


def create_run_report(
    run_id: str,
    dataset_id: str,
    model: str,
    runner_commit: str,
    aggregation: AggregationResult,
    case_evaluations: List[CaseEvaluation],
) -> RunReport:
    total = len(case_evaluations)
    passed = sum(1 for case in case_evaluations if case.passed)
    failed = total - passed
    case_summary = CaseSummary(total=total, passed=passed, failed=failed, errors=0)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return RunReport(
        run_id=run_id,
        dataset_id=dataset_id,
        model=model,
        runner_commit=runner_commit,
        domain_scores=aggregation.domain_scores,
        overall_score=aggregation.overall_score,
        threshold_failures=aggregation.threshold_failures,
        case_summary=case_summary,
        created_at=created_at,
        metric_summaries=aggregation.metric_summaries,
        case_evaluations=case_evaluations,
    )


def write_report(path: Path, report: RunReport) -> None:
    payload = report.to_dict()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def report_brief(report: RunReport) -> Mapping[str, float]:
    return {
        "overall_score": report.overall_score,
        "threshold_failures": float(len(report.threshold_failures)),
        "cases_total": float(report.case_summary.total),
    }
