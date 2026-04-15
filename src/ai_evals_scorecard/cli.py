from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import typer

from ai_evals_scorecard.backend import build_backend
from ai_evals_scorecard.compare import compare_reports
from ai_evals_scorecard.config import Settings
from ai_evals_scorecard.models import CaseEvaluation, DatasetRow, MetricRequest, Scorecard
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
    provider: str = typer.Option("", help="Evaluation provider: deterministic or azure"),
    runner_commit: str = typer.Option("unknown", help="Runner commit hash"),
) -> None:
    rows = load_dataset(dataset)
    card = load_scorecard(scorecard)
    resolved_run_id = run_id or _generated_run_id()
    settings = Settings.from_env()
    provider_mode = (provider or settings.provider_mode).strip().lower()
    settings = Settings(
        provider_mode=provider_mode,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_key=settings.azure_openai_api_key,
        azure_openai_api_version=settings.azure_openai_api_version,
        azure_openai_judge_deployment=settings.azure_openai_judge_deployment,
        azure_openai_smoke_deployment=settings.azure_openai_smoke_deployment,
    )
    backend = build_backend(settings)
    resolved_model = model
    if model == "mock/deterministic-v1" and provider_mode == "azure":
        resolved_model = f"azure-openai/{settings.azure_openai_judge_deployment}"

    metric_values, case_evaluations = execute_cases(rows, card, backend)
    aggregation = aggregate_scores(card, metric_values)
    report = create_run_report(
        run_id=resolved_run_id,
        dataset_id=dataset.stem,
        model=resolved_model,
        runner_commit=runner_commit,
        aggregation=aggregation,
        case_evaluations=case_evaluations,
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


def execute_cases(
    rows: List[DatasetRow],
    scorecard: Scorecard,
    backend,
) -> tuple[Dict[str, Dict[str, List[float]]], List[CaseEvaluation]]:
    metric_values: Dict[str, Dict[str, List[float]]] = {
        domain_name: {metric.name: [] for metric in domain_cfg.metrics}
        for domain_name, domain_cfg in scorecard.domains.items()
    }
    case_evaluations: List[CaseEvaluation] = []
    metric_requests = _metric_requests(scorecard)

    for row in rows:
        case_passed = True
        case_metrics = backend.evaluate_case(row, metric_requests)
        by_key = {metric.key: metric for metric in case_metrics}

        for request in metric_requests:
            case_metric = by_key.get(request.key)
            if case_metric is None:
                raise ValueError(f"Missing metric result for {row.case_id}: {request.key}")
            metric_values[request.domain][request.name].append(case_metric.value)
            if not case_metric.passed:
                case_passed = False

        case_evaluations.append(
            CaseEvaluation(
                case_id=row.case_id,
                task_type=row.task_type,
                passed=case_passed,
                metrics=case_metrics,
            )
        )

    return metric_values, case_evaluations


def _generated_run_id() -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{now}"


def _metric_requests(scorecard: Scorecard) -> List[MetricRequest]:
    requests: List[MetricRequest] = []
    for domain_name, domain_cfg in scorecard.domains.items():
        for metric in domain_cfg.metrics:
            requests.append(
                MetricRequest(
                    domain=domain_name,
                    name=metric.name,
                    threshold=metric.threshold,
                    operator=metric.operator,
                )
            )
    return requests


def main() -> None:
    app()
