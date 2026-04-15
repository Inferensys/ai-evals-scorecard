from __future__ import annotations

import json
import os
from pathlib import Path

from ai_evals_scorecard.backend import build_backend
from ai_evals_scorecard.cli import execute_cases
from ai_evals_scorecard.compare import compare_reports
from ai_evals_scorecard.config import Settings
from ai_evals_scorecard.parsers import load_dataset, load_scorecard
from ai_evals_scorecard.reporting import create_run_report, write_report
from ai_evals_scorecard.scoring import aggregate_scores


ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "demo" / "input"
OUTPUT_DIR = ROOT / "demo" / "output"


def main() -> None:
    os.environ.setdefault("AI_EVALS_PROVIDER", "azure")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    settings = Settings.from_env()
    backend = build_backend(settings)
    scorecard_path = INPUT_DIR / "scorecard.yaml"
    scorecard = load_scorecard(scorecard_path)

    runs = [
        ("baseline", INPUT_DIR / "dataset.baseline.jsonl"),
        ("candidate", INPUT_DIR / "dataset.candidate.jsonl"),
    ]

    report_paths: dict[str, Path] = {}
    summary: list[dict[str, object]] = []

    for name, dataset_path in runs:
        rows = load_dataset(dataset_path)
        metric_values, case_evaluations = execute_cases(rows, scorecard, backend)
        aggregation = aggregate_scores(scorecard, metric_values)
        report = create_run_report(
            run_id=f"demo_{name}_20260416",
            dataset_id=dataset_path.stem,
            model=f"azure-openai/{settings.azure_openai_judge_deployment}",
            runner_commit="live-demo",
            aggregation=aggregation,
            case_evaluations=case_evaluations,
        )
        path = OUTPUT_DIR / f"{name}-report.json"
        write_report(path, report)
        report_paths[name] = path
        summary.append(
            {
                "name": name,
                "overall_score": report.overall_score,
                "threshold_failures": len(report.threshold_failures),
                "model": report.model,
                "passed_cases": report.case_summary.passed,
                "failed_cases": report.case_summary.failed,
            }
        )

    comparison = compare_reports(
        base=load_report(report_paths["baseline"]),
        candidate=load_report(report_paths["candidate"]),
    )
    comparison_path = OUTPUT_DIR / "baseline-vs-candidate.json"
    comparison_path.write_text(json.dumps(comparison.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    summary.append(
        {
            "name": "comparison",
            "overall_delta": comparison.overall_delta,
            "new_threshold_failures": len(comparison.newly_failed_thresholds),
            "resolved_threshold_failures": len(comparison.resolved_thresholds),
        }
    )
    (OUTPUT_DIR / "demo-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def load_report(path: Path):
    from ai_evals_scorecard.parsers import load_report as _load_report

    return _load_report(path)


if __name__ == "__main__":
    main()
