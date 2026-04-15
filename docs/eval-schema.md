# Evaluation Schema

This schema is intentionally compact and can be adapted to JSON Schema, Pydantic, or Protobuf.

## Dataset Row Shape

```json
{
  "case_id": "string",
  "task_type": "qa|workflow|tool_call|classification",
  "input": {
    "prompt": "string",
    "context": {},
    "tool_state": {}
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

## Scorecard Shape

```yaml
version: 1
domains:
  quality:
    weight: 0.45
    metrics:
      - name: answer_correctness
        threshold: 0.85
      - name: policy_compliance
        threshold: 1.00
  execution:
    weight: 0.25
  latency:
    weight: 0.20
  cost:
    weight: 0.10
```

## Run Report Shape

```json
{
  "run_id": "run_2026_04_15_001",
  "dataset_id": "support_v4",
  "model": "provider/model@version",
  "runner_commit": "git_sha",
  "domain_scores": {
    "quality": 88.1,
    "execution": 92.4,
    "latency": 81.0,
    "cost": 76.8
  },
  "overall_score": 86.1,
  "regressions": [],
  "created_at": "2026-04-15T12:05:00Z"
}
```

## Validation Rules

- `case_id` must be stable across runs.
- Missing domain scores fail the run.
- Unknown metric names are hard errors.
- Threshold checks are per metric and for weighted aggregate.
