from ai_evals_scorecard.models import DomainConfig, MetricConfig, Scorecard
from ai_evals_scorecard.scoring import aggregate_metric_values, aggregate_scores


def test_aggregation_and_threshold_failures() -> None:
    scorecard = Scorecard(
        version=1,
        domains={
            "quality": DomainConfig(
                weight=0.7,
                metrics=[
                    MetricConfig(name="answer_correctness", threshold=0.8, operator=">="),
                    MetricConfig(name="policy_compliance", threshold=1.0, operator=">="),
                ],
            ),
            "latency": DomainConfig(
                weight=0.3,
                metrics=[MetricConfig(name="p95_latency_ms", threshold=2200, operator="<=")],
            ),
        },
    )
    values = {
        "quality": {
            "answer_correctness": [0.9, 0.7],
            "policy_compliance": [1.0, 0.95],
        },
        "latency": {"p95_latency_ms": [1000, 1900, 2100, 2500]},
    }

    aggregation = aggregate_scores(scorecard, values)

    assert aggregation.domain_scores["quality"] == 98.75
    assert aggregation.domain_scores["latency"] == 88.0
    assert aggregation.overall_score == 95.525

    failure_keys = {f"{item.domain}.{item.metric}" for item in aggregation.threshold_failures}
    assert failure_keys == {"quality.policy_compliance", "latency.p95_latency_ms"}


def test_p95_aggregation_rule() -> None:
    assert aggregate_metric_values([100, 200, 300, 400, 500], "p95_latency_ms") == 500
