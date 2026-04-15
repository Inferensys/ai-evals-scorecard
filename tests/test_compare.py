from ai_evals_scorecard.compare import compare_reports
from ai_evals_scorecard.models import (
    CaseSummary,
    MetricSummary,
    RunReport,
    ThresholdFailure,
)


def test_report_comparison_deltas_and_failures() -> None:
    base = RunReport(
        run_id="base_001",
        dataset_id="dataset_a",
        model="mock/v1",
        runner_commit="aaa111",
        domain_scores={"quality": 90.0, "latency": 80.0},
        overall_score=86.0,
        threshold_failures=[
            ThresholdFailure(
                domain="cost",
                metric="avg_cost_usd",
                operator="<=",
                threshold=0.04,
                actual=0.05,
            )
        ],
        case_summary=CaseSummary(total=2, passed=2, failed=0, errors=0),
        created_at="2026-04-15T00:00:00Z",
        metric_summaries=[
            MetricSummary(
                domain="quality",
                name="answer_correctness",
                operator=">=",
                threshold=0.85,
                value=0.91,
                normalized_score=100.0,
                passed=True,
            )
        ],
    )
    candidate = RunReport(
        run_id="cand_001",
        dataset_id="dataset_a",
        model="mock/v1",
        runner_commit="bbb222",
        domain_scores={"quality": 86.0, "latency": 78.0},
        overall_score=82.0,
        threshold_failures=[
            ThresholdFailure(
                domain="quality",
                metric="policy_compliance",
                operator=">=",
                threshold=1.0,
                actual=0.96,
            )
        ],
        case_summary=CaseSummary(total=2, passed=1, failed=1, errors=0),
        created_at="2026-04-15T01:00:00Z",
        metric_summaries=[
            MetricSummary(
                domain="quality",
                name="answer_correctness",
                operator=">=",
                threshold=0.85,
                value=0.86,
                normalized_score=100.0,
                passed=True,
            )
        ],
    )

    comparison = compare_reports(base, candidate)
    assert comparison.overall_delta == -4.0
    assert comparison.domain_deltas == {"latency": -2.0, "quality": -4.0}
    assert comparison.metric_deltas["quality.answer_correctness"] == -0.05
    assert len(comparison.newly_failed_thresholds) == 1
    assert comparison.newly_failed_thresholds[0].metric == "policy_compliance"
    assert len(comparison.resolved_thresholds) == 1
    assert comparison.resolved_thresholds[0].metric == "avg_cost_usd"
