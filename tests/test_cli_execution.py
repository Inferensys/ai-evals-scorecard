from ai_evals_scorecard.backend import DeterministicEvaluationBackend
from ai_evals_scorecard.cli import execute_cases
from ai_evals_scorecard.models import DatasetRow, DomainConfig, MetricConfig, Scorecard


def test_execute_cases_returns_case_evaluations() -> None:
    rows = [
        DatasetRow(
            case_id="case_001",
            task_type="qa",
            input={"prompt": "Why was invoice higher?"},
            observed={"output_text": "Seat expansion increased the invoice.", "metrics": {"latency_ms": 980}},
            expected={"answer_contains": ["seat expansion"]},
            metadata={"difficulty": "easy"},
        )
    ]
    scorecard = Scorecard(
        version=1,
        domains={
            "quality": DomainConfig(
                weight=0.8,
                metrics=[MetricConfig(name="answer_correctness", threshold=0.5, operator=">=")],
            ),
            "latency": DomainConfig(
                weight=0.2,
                metrics=[MetricConfig(name="p95_latency_ms", threshold=2200, operator="<=")],
            ),
        },
    )

    metric_values, case_evaluations = execute_cases(
        rows,
        scorecard,
        DeterministicEvaluationBackend(),
    )

    assert list(metric_values["quality"].keys()) == ["answer_correctness"]
    assert case_evaluations[0].case_id == "case_001"
    assert len(case_evaluations[0].metrics) == 2
