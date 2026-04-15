from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

SUPPORTED_OPERATORS = {">=", "<=", ">", "<", "=="}


@dataclass(frozen=True)
class MetricConfig:
    name: str
    threshold: float
    operator: str = ">="


@dataclass(frozen=True)
class DomainConfig:
    weight: float
    metrics: List[MetricConfig]


@dataclass(frozen=True)
class Scorecard:
    version: int
    domains: Dict[str, DomainConfig]


@dataclass(frozen=True)
class DatasetRow:
    case_id: str
    task_type: str
    input: Dict[str, Any]
    expected: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class MetricSummary:
    domain: str
    name: str
    operator: str
    threshold: float
    value: float
    normalized_score: float
    passed: bool

    @property
    def key(self) -> str:
        return f"{self.domain}.{self.name}"


@dataclass(frozen=True)
class ThresholdFailure:
    domain: str
    metric: str
    operator: str
    threshold: float
    actual: float

    @property
    def key(self) -> str:
        return f"{self.domain}.{self.metric}|{self.operator}|{self.threshold}"


@dataclass(frozen=True)
class CaseSummary:
    total: int
    passed: int
    failed: int
    errors: int


@dataclass(frozen=True)
class RunReport:
    run_id: str
    dataset_id: str
    model: str
    runner_commit: str
    domain_scores: Dict[str, float]
    overall_score: float
    threshold_failures: List[ThresholdFailure]
    case_summary: CaseSummary
    created_at: str
    metric_summaries: List[MetricSummary]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "model": self.model,
            "runner_commit": self.runner_commit,
            "domain_scores": self.domain_scores,
            "overall_score": self.overall_score,
            "threshold_failures": [
                {
                    "domain": f.domain,
                    "metric": f.metric,
                    "operator": f.operator,
                    "threshold": f.threshold,
                    "actual": f.actual,
                }
                for f in self.threshold_failures
            ],
            "case_summary": {
                "total": self.case_summary.total,
                "passed": self.case_summary.passed,
                "failed": self.case_summary.failed,
                "errors": self.case_summary.errors,
            },
            "created_at": self.created_at,
            "metric_summaries": [
                {
                    "domain": m.domain,
                    "name": m.name,
                    "operator": m.operator,
                    "threshold": m.threshold,
                    "value": m.value,
                    "normalized_score": m.normalized_score,
                    "passed": m.passed,
                }
                for m in self.metric_summaries
            ],
        }


@dataclass(frozen=True)
class ComparisonReport:
    base_run_id: str
    candidate_run_id: str
    overall_delta: float
    domain_deltas: Dict[str, float]
    metric_deltas: Dict[str, float]
    newly_failed_thresholds: List[ThresholdFailure]
    resolved_thresholds: List[ThresholdFailure]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_run_id": self.base_run_id,
            "candidate_run_id": self.candidate_run_id,
            "overall_delta": self.overall_delta,
            "domain_deltas": self.domain_deltas,
            "metric_deltas": self.metric_deltas,
            "newly_failed_thresholds": [
                {
                    "domain": f.domain,
                    "metric": f.metric,
                    "operator": f.operator,
                    "threshold": f.threshold,
                    "actual": f.actual,
                }
                for f in self.newly_failed_thresholds
            ],
            "resolved_thresholds": [
                {
                    "domain": f.domain,
                    "metric": f.metric,
                    "operator": f.operator,
                    "threshold": f.threshold,
                    "actual": f.actual,
                }
                for f in self.resolved_thresholds
            ],
        }
