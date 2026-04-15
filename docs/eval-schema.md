# Evaluation Schema

## Dataset Row

```json
{
  "case_id": "string",
  "task_type": "qa|workflow|tool_call|classification",
  "input": {
    "prompt": "string",
    "context": {}
  },
  "observed": {
    "output_text": "string",
    "actions": ["string"],
    "policy_flags": ["string"],
    "metrics": {
      "latency_ms": 0,
      "cost_usd": 0.0
    }
  },
  "expected": {
    "answer_contains": ["string"],
    "forbidden_terms": ["string"],
    "required_actions": ["string"],
    "policy_flags": ["string"]
  },
  "metadata": {
    "difficulty": "easy|medium|hard",
    "tenant_tier": "free|pro|enterprise",
    "labels": ["string"]
  }
}
```

## Scorecard

```yaml
version: 1
domains:
  quality:
    weight: 0.45
    metrics:
      - name: answer_correctness
        threshold: 0.80
      - name: policy_compliance
        threshold: 0.90
  execution:
    weight: 0.25
    metrics:
      - name: workflow_completion
        threshold: 0.85
  latency:
    weight: 0.20
    metrics:
      - name: p95_latency_ms
        threshold: 1800
        operator: "<="
  cost:
    weight: 0.10
    metrics:
      - name: avg_cost_usd
        threshold: 0.035
        operator: "<="
```

## Run Report

```json
{
  "run_id": "demo_candidate_20260416",
  "dataset_id": "dataset.candidate",
  "model": "azure-openai/gpt-5.4",
  "domain_scores": {
    "quality": 100.0,
    "execution": 100.0,
    "latency": 100.0,
    "cost": 100.0
  },
  "overall_score": 100.0,
  "metric_summaries": [],
  "case_evaluations": [],
  "threshold_failures": []
}
```

## Metric Sources

- semantic metrics come from the judge backend
- telemetry metrics come from `observed.metrics`
- thresholding and normalization are always local
