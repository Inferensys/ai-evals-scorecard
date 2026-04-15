from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Mapping

from ai_evals_scorecard.models import MetricSummary, Scorecard, ThresholdFailure


@dataclass(frozen=True)
class AggregationResult:
    metric_summaries: List[MetricSummary]
    domain_scores: Dict[str, float]
    overall_score: float
    threshold_failures: List[ThresholdFailure]


def aggregate_scores(
    scorecard: Scorecard, metric_values: Mapping[str, Mapping[str, List[float]]]
) -> AggregationResult:
    metric_summaries: List[MetricSummary] = []
    threshold_failures: List[ThresholdFailure] = []
    domain_scores: Dict[str, float] = {}

    for domain_name, domain_cfg in scorecard.domains.items():
        metric_scores: List[float] = []
        domain_values = metric_values.get(domain_name, {})
        for metric in domain_cfg.metrics:
            values = domain_values.get(metric.name, [])
            if not values:
                raise ValueError(f"No values found for metric {domain_name}.{metric.name}")
            aggregate_value = aggregate_metric_values(values, metric.name)
            passed = evaluate_threshold(aggregate_value, metric.operator, metric.threshold)
            normalized = normalize_score(aggregate_value, metric.operator, metric.threshold)
            metric_scores.append(normalized)
            summary = MetricSummary(
                domain=domain_name,
                name=metric.name,
                operator=metric.operator,
                threshold=metric.threshold,
                value=round(aggregate_value, 6),
                normalized_score=round(normalized, 3),
                passed=passed,
            )
            metric_summaries.append(summary)
            if not passed:
                threshold_failures.append(
                    ThresholdFailure(
                        domain=domain_name,
                        metric=metric.name,
                        operator=metric.operator,
                        threshold=metric.threshold,
                        actual=round(aggregate_value, 6),
                    )
                )
        domain_scores[domain_name] = round(mean(metric_scores), 3)

    total_weight = sum(domain.weight for domain in scorecard.domains.values())
    if total_weight <= 0:
        raise ValueError("Total scorecard domain weight must be > 0")
    weighted_sum = sum(
        domain_scores[domain_name] * scorecard.domains[domain_name].weight
        for domain_name in domain_scores
    )
    overall = round(weighted_sum / total_weight, 3)

    return AggregationResult(
        metric_summaries=metric_summaries,
        domain_scores=domain_scores,
        overall_score=overall,
        threshold_failures=threshold_failures,
    )


def aggregate_metric_values(values: List[float], metric_name: str) -> float:
    if not values:
        raise ValueError("Cannot aggregate empty metric values")
    if metric_name.startswith("p95_"):
        return percentile(values, 95)
    return mean(values)


def evaluate_threshold(value: float, operator: str, threshold: float) -> bool:
    if operator == ">=":
        return value >= threshold
    if operator == "<=":
        return value <= threshold
    if operator == ">":
        return value > threshold
    if operator == "<":
        return value < threshold
    if operator == "==":
        return value == threshold
    raise ValueError(f"Unsupported operator: {operator}")


def normalize_score(value: float, operator: str, threshold: float) -> float:
    if operator in {">=", ">"}:
        if threshold == 0:
            return 100.0 if value >= 0 else 0.0
        return clamp((value / threshold) * 100.0, 0.0, 100.0)
    if operator in {"<=", "<"}:
        if value <= 0:
            return 100.0
        return clamp((threshold / value) * 100.0, 0.0, 100.0)
    if operator == "==":
        return 100.0 if value == threshold else 0.0
    raise ValueError(f"Unsupported operator: {operator}")


def percentile(values: List[float], p: int) -> float:
    if not values:
        raise ValueError("Cannot compute percentile on empty list")
    if p < 0 or p > 100:
        raise ValueError("Percentile p must be in [0, 100]")
    ordered = sorted(values)
    rank = int(math.ceil((p / 100.0) * len(ordered)))
    index = max(0, min(rank - 1, len(ordered) - 1))
    return ordered[index]


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
