# ai-evals-scorecard

Deterministic, framework-agnostic evaluation toolkit for LLM and agentic workflows.

The repository provides:

- Typed scorecard and dataset parsing.
- Local deterministic evaluator backend (no external API dependency).
- Score aggregation with threshold checks.
- JSON run reports and baseline/candidate comparison reports.

## Setup

Python `3.9+` and `uv` are required.

```bash
uv sync --group dev
```

## CLI

### Run an evaluation

```bash
uv run evals run \
  --dataset examples/dataset.support-workflow.jsonl \
  --scorecard examples/scorecard.yaml \
  --out reports/run-001.json \
  --run-id run_001 \
  --model mock/deterministic-v1
```

Expected stdout:

```text
run_id=run_001
overall_score=...
threshold_failures=...
report=reports/run-001.json
```

### Compare two reports

```bash
uv run evals compare \
  --base reports/run-000.json \
  --candidate reports/run-001.json \
  --out reports/compare-000-001.json
```

Expected stdout:

```text
base=run_000
candidate=run_001
overall_delta=...
new_threshold_failures=...
resolved_threshold_failures=...
comparison=reports/compare-000-001.json
```

## Report Shape

A run report includes:

- `domain_scores` (normalized `0-100` per domain)
- `overall_score` (weighted across domains)
- `metric_summaries` (aggregate value, threshold, pass/fail)
- `threshold_failures` (machine-readable regression surface)
- `case_summary` (passed/failed/error counts)

See example contracts:

- [examples/scorecard.yaml](examples/scorecard.yaml)
- [examples/dataset.support-workflow.jsonl](examples/dataset.support-workflow.jsonl)
- [examples/report.run-summary.json](examples/report.run-summary.json)

## Development

Run tests:

```bash
uv run pytest
```

Implementation details are captured in:

- [docs/implementation-plan.md](docs/implementation-plan.md)
- [docs/runner-design.md](docs/runner-design.md)
