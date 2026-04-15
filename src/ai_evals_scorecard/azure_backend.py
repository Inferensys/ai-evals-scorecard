from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import AzureOpenAI

from ai_evals_scorecard.config import Settings
from ai_evals_scorecard.models import CaseMetricResult, DatasetRow, MetricRequest
from ai_evals_scorecard.scoring import evaluate_threshold


class AzureJudgeBackend:
    def __init__(self, settings: Settings) -> None:
        settings.validate_for_live_mode()
        self._settings = settings
        self._client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            max_retries=2,
            timeout=90.0,
        )

    def evaluate_case(self, row: DatasetRow, metrics: List[MetricRequest]) -> List[CaseMetricResult]:
        telemetry_metrics: List[CaseMetricResult] = []
        semantic_metrics: List[MetricRequest] = []

        for metric in metrics:
            telemetry_value = _telemetry_value(row, metric.name)
            if telemetry_value is None:
                semantic_metrics.append(metric)
                continue
            telemetry_metrics.append(
                CaseMetricResult(
                    domain=metric.domain,
                    name=metric.name,
                    operator=metric.operator,
                    threshold=metric.threshold,
                    value=telemetry_value,
                    passed=evaluate_threshold(telemetry_value, metric.operator, metric.threshold),
                    source="telemetry",
                    rationale="Value read from observed telemetry.",
                )
            )

        if not semantic_metrics:
            return telemetry_metrics

        if not row.observed:
            raise RuntimeError(
                f"Case '{row.case_id}' does not include observed output required for semantic evaluation."
            )

        response = self._client.chat.completions.create(
            model=self._settings.azure_openai_judge_deployment,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an evaluation judge for LLM and agent outputs. "
                        "Score only the requested metrics on a 0.0 to 1.0 scale. "
                        "Use 1.0 only when the case fully satisfies the expected behavior. "
                        "Use lower scores when requirements are partially met, forbidden content is present, "
                        "or workflow steps are missing. "
                        "Do not reward style when the expected behavior is absent. "
                        "Return scores only through the provided tool."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "case_id": row.case_id,
                            "task_type": row.task_type,
                            "input": row.input,
                            "observed": row.observed,
                            "expected": row.expected,
                            "requested_metrics": [
                                {
                                    "domain": metric.domain,
                                    "name": metric.name,
                                    "threshold": metric.threshold,
                                    "operator": metric.operator,
                                }
                                for metric in semantic_metrics
                            ],
                        },
                        ensure_ascii=True,
                    ),
                },
            ],
            tools=[_judge_schema()],
            tool_choice={"type": "function", "function": {"name": "submit_metric_scores"}},
        )

        tool_calls = response.choices[0].message.tool_calls or []
        if not tool_calls:
            raise RuntimeError(f"Azure judge returned no tool call for case '{row.case_id}'.")

        payload = json.loads(tool_calls[0].function.arguments)
        returned = {
            f"{item['domain']}.{item['name']}": item
            for item in payload.get("scores", [])
        }

        results = list(telemetry_metrics)
        for metric in semantic_metrics:
            item = returned.get(metric.key)
            if item is None:
                raise RuntimeError(f"Azure judge omitted metric '{metric.key}' for case '{row.case_id}'.")
            value = _clamp_score(float(item["score"]))
            results.append(
                CaseMetricResult(
                    domain=metric.domain,
                    name=metric.name,
                    operator=metric.operator,
                    threshold=metric.threshold,
                    value=value,
                    passed=evaluate_threshold(value, metric.operator, metric.threshold),
                    source="azure-openai",
                    rationale=str(item.get("rationale", "")) or None,
                )
            )
        return results


def _judge_schema() -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "submit_metric_scores",
            "description": "Return metric scores for the evaluated case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scores": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "domain": {"type": "string"},
                                "name": {"type": "string"},
                                "score": {"type": "number"},
                                "rationale": {"type": "string"},
                            },
                            "required": ["domain", "name", "score", "rationale"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["scores"],
                "additionalProperties": False,
            },
        },
    }


def _telemetry_value(row: DatasetRow, metric_name: str) -> float | None:
    observed_metrics = row.observed.get("metrics", {}) if isinstance(row.observed, dict) else {}
    candidates = [
        metric_name,
        "latency_ms" if "latency" in metric_name else None,
        "cost_usd" if metric_name.endswith("_usd") else None,
    ]
    for key in candidates:
        if key is None:
            continue
        value = observed_metrics.get(key)
        if value is None:
            value = row.observed.get(key) if isinstance(row.observed, dict) else None
        if value is not None:
            return float(value)
    return None


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))
