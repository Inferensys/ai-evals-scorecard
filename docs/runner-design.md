# Runner Design

This document outlines a decoupled evaluation runner that can execute against any model/backend.

## Pipeline Stages

1. `load_dataset`
2. `execute_case`
3. `compute_metrics`
4. `aggregate_scores`
5. `compare_baseline`
6. `emit_report`

## Interfaces

### Case Executor

```text
execute(case) -> {
  output_text,
  actions[],
  tool_calls[],
  latency_ms,
  token_usage
}
```

### Metric Evaluator

```text
evaluate(case, execution_result) -> {
  metric_name,
  value,
  passed,
  explanation
}
```

### Aggregator

```text
aggregate(metric_results, scorecard) -> {
  domain_scores,
  overall_score,
  failed_thresholds[]
}
```

## Failure Handling

- Executor errors should produce `case_status=error`, not silent skips.
- Timeouts are counted and surfaced in report metadata.
- Partial run reports must be tagged `incomplete=true`.

## CI Integration

- Block merge when `overall_score` falls below baseline delta budget.
- Always upload full report artifact for diff inspection.
- Run a small canary dataset on pull requests and full datasets nightly.
