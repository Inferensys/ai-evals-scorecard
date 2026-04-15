from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

from ai_evals_scorecard.models import (
    CaseEvaluation,
    CaseMetricResult,
    CaseSummary,
    DatasetRow,
    DomainConfig,
    MetricConfig,
    MetricSummary,
    RunReport,
    Scorecard,
    SUPPORTED_OPERATORS,
    ThresholdFailure,
)


def load_dataset(path: Path) -> List[DatasetRow]:
    rows: List[DatasetRow] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        payload = json.loads(raw)
        _validate_dataset_row(payload, line_no=line_no)
        rows.append(
            DatasetRow(
                case_id=payload["case_id"],
                task_type=payload["task_type"],
                input=payload.get("input", {}),
                observed=payload.get("observed", {}),
                expected=payload.get("expected", {}),
                metadata=payload.get("metadata", {}),
            )
        )
    if not rows:
        raise ValueError(f"Dataset is empty: {path}")
    return rows


def load_scorecard(path: Path) -> Scorecard:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Scorecard must be a mapping")
    version = int(payload.get("version", 0))
    domains_obj = payload.get("domains")
    if not isinstance(domains_obj, dict) or not domains_obj:
        raise ValueError("Scorecard requires non-empty domains")

    domains: Dict[str, DomainConfig] = {}
    for domain_name, domain_payload in domains_obj.items():
        if not isinstance(domain_payload, dict):
            raise ValueError(f"Domain payload must be mapping: {domain_name}")
        weight = float(domain_payload.get("weight", 0.0))
        metrics_payload = domain_payload.get("metrics")
        if not isinstance(metrics_payload, list) or not metrics_payload:
            raise ValueError(f"Domain must define non-empty metrics list: {domain_name}")
        metrics: List[MetricConfig] = []
        for metric in metrics_payload:
            if not isinstance(metric, dict):
                raise ValueError(f"Invalid metric in domain {domain_name}")
            operator = metric.get("operator", ">=")
            if operator not in SUPPORTED_OPERATORS:
                raise ValueError(f"Unsupported operator {operator} for {domain_name}")
            metrics.append(
                MetricConfig(
                    name=str(metric["name"]),
                    threshold=float(metric["threshold"]),
                    operator=str(operator),
                )
            )
        domains[domain_name] = DomainConfig(weight=weight, metrics=metrics)

    return Scorecard(version=version, domains=domains)


def load_report(path: Path) -> RunReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    threshold_failures = [
        ThresholdFailure(
            domain=str(item["domain"]),
            metric=str(item["metric"]),
            operator=str(item["operator"]),
            threshold=float(item["threshold"]),
            actual=float(item["actual"]),
        )
        for item in payload.get("threshold_failures", [])
    ]
    metric_summaries = [
        MetricSummary(
            domain=str(item["domain"]),
            name=str(item["name"]),
            operator=str(item["operator"]),
            threshold=float(item["threshold"]),
            value=float(item["value"]),
            normalized_score=float(item["normalized_score"]),
            passed=bool(item["passed"]),
        )
        for item in payload.get("metric_summaries", [])
    ]
    case_evaluations = [
        CaseEvaluation(
            case_id=str(item["case_id"]),
            task_type=str(item["task_type"]),
            passed=bool(item["passed"]),
            metrics=[
                CaseMetricResult(
                    domain=str(metric["domain"]),
                    name=str(metric["name"]),
                    operator=str(metric["operator"]),
                    threshold=float(metric["threshold"]),
                    value=float(metric["value"]),
                    passed=bool(metric["passed"]),
                    source=str(metric.get("source", "unknown")),
                    rationale=(
                        None if metric.get("rationale") is None else str(metric.get("rationale"))
                    ),
                )
                for metric in item.get("metrics", [])
            ],
        )
        for item in payload.get("case_evaluations", [])
    ]
    case_payload = payload.get("case_summary", {})
    case_summary = CaseSummary(
        total=int(case_payload.get("total", 0)),
        passed=int(case_payload.get("passed", 0)),
        failed=int(case_payload.get("failed", 0)),
        errors=int(case_payload.get("errors", 0)),
    )
    return RunReport(
        run_id=str(payload["run_id"]),
        dataset_id=str(payload["dataset_id"]),
        model=str(payload["model"]),
        runner_commit=str(payload.get("runner_commit", "unknown")),
        domain_scores={k: float(v) for k, v in payload["domain_scores"].items()},
        overall_score=float(payload["overall_score"]),
        threshold_failures=threshold_failures,
        case_summary=case_summary,
        created_at=str(payload["created_at"]),
        metric_summaries=metric_summaries,
        case_evaluations=case_evaluations,
    )


def _validate_dataset_row(payload: Dict[str, Any], line_no: int) -> None:
    for key in ("case_id", "task_type"):
        if key not in payload:
            raise ValueError(f"Dataset row line {line_no} missing key: {key}")
    if not isinstance(payload.get("case_id"), str) or not payload["case_id"]:
        raise ValueError(f"Dataset row line {line_no} has invalid case_id")
    if not isinstance(payload.get("task_type"), str) or not payload["task_type"]:
        raise ValueError(f"Dataset row line {line_no} has invalid task_type")
