from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import typer

from ai_evals_scorecard.compare import compare_reports
from ai_evals_scorecard.mock_backend import evaluate_metric
from ai_evals_scorecard.models import DatasetRow, MetricConfig, Scorecard
from ai_evals_scorecard.parsers import load_dataset, load_report, load_scorecard
from ai_evals_scorecard.reporting import create_run_report, write_report
from ai_evals_scorecard.scoring import aggregate_scores, evaluate_threshold

app = typer.Typer(help="Deterministic evaluation toolkit for scorecard-based model/system evaluation.")


@app.command("run")
def run_command(
    dataset: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False, help="JSONL dataset path"),
    scorecard: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False, help="YAML scorecard path"),
    out: Path = typer.Option(..., help="Output report JSON path"),
    run_id: str = typer.Option("", help="Run identifier"),
    model: str = typer.Option("mock/deterministic-v1", help="Model/backend label for report metadata"),
    runner_commit: str = typer.Option("unknown", help="Runner commit hash"),
) -> None:
    rows = load_dataset(dataset)
    card = load_scorecard(scorecard)
    resolved_run_id = run_id or _generated_run_id()

    metric_values, per_case_passed = execute_cases(rows, card)
    aggregation = aggregate_scores(card, metric_values)
    report = create_run_report(
        run_id=resolved_run_id,
        dataset_id=dataset.stem,
        model=model,
        runner_commit=runner_commit,
        aggregation=aggregation,
        per_case_passed=per_case_passed,
    )
    write_report(out, report)

    typer.echo(f"run_id={report.run_id}")
    typer.echo(f"overall_score={report.overall_score}")
    typer.echo(f"threshold_failures={len(report.threshold_failures)}")
    typer.echo(f"report={out}")


@app.command("compare")
def compare_command(
    base: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False, help="Baseline report JSON path"),
    candidate: Path = typer.Option(..., exists=True, file_okay=True, dir_okay=False, help="Candidate report JSON path"),
    out: Path = typer.Option(None, help="Optional output comparison JSON path"),
) -> None:
    base_report = load_report(base)
    candidate_report = load_report(candidate)
    comparison = compare_reports(base_report, candidate_report)

    typer.echo(f"base={comparison.base_run_id}")
    typer.echo(f"candidate={comparison.candidate_run_id}")
    typer.echo(f"overall_delta={comparison.overall_delta}")
    typer.echo(f"new_threshold_failures={len(comparison.newly_failed_thresholds)}")
    typer.echo(f"resolved_threshold_failures={len(comparison.resolved_thresholds)}")

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(comparison.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        typer.echo(f"comparison={out}")


def execute_cases(rows: List[DatasetRow], scorecard: Scorecard) -> tuple[Dict[str, Dict[str, List[float]]], List[bool]]:
    metric_values: Dict[str, Dict[str, List[float]]] = {
        domain_name: {metric.name: [] for metric in domain_cfg.metrics}
        for domain_name, domain_cfg in scorecard.domains.items()
    }
    per_case_passed: List[bool] = []

    for row in rows:
        case_passed = True
        for domain_name, domain_cfg in scorecard.domains.items():
            for metric in domain_cfg.metrics:
                value = evaluate_metric(row, metric.name)
                metric_values[domain_name][metric.name].append(value)
                if not evaluate_threshold(value, metric.operator, metric.threshold):
                    case_passed = False
        per_case_passed.append(case_passed)

    return metric_values, per_case_passed


def _generated_run_id() -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{now}"


def main() -> None:
    app()
