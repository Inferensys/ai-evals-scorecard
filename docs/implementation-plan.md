# Implementation Plan

## Objective

Turn `ai-evals-scorecard` from a contract-only repository into a runnable, deterministic evaluation toolkit that can be executed locally with Python 3.9 and `uv`.

The first slice must support:

- Loading JSONL datasets and YAML scorecards.
- Running deterministic local evaluations without external APIs.
- Aggregating metrics into domain and overall scores.
- Enforcing thresholds with explicit failure reporting.
- Comparing two reports for regression analysis.

## Runtime and Packaging

- Python: `>=3.9,<4.0`
- Package manager: `uv`
- CLI: `Typer`
- Test runner: `pytest`
- Serialization: `json`, `yaml` (PyYAML)

## Module Layout

```
src/ai_evals_scorecard/
  __init__.py
  __main__.py
  cli.py
  models.py
  parsers.py
  mock_backend.py
  scoring.py
  reporting.py
  compare.py
```

Responsibilities:

- `models.py`: Typed dataclasses for dataset rows, scorecards, metric summaries, reports, and comparisons.
- `parsers.py`: Parsing and validation for JSONL datasets and YAML scorecards.
- `mock_backend.py`: Deterministic evaluator that produces metric values from case data + metric config.
- `scoring.py`: Metric aggregation, threshold checks, domain scoring, weighted overall score.
- `reporting.py`: Report construction and JSON serialization.
- `compare.py`: Base/candidate report diff logic.
- `cli.py`: `evals run` and `evals compare` command surfaces.

## Command Contracts

### `evals run`

Inputs:

- `--dataset PATH` (JSONL)
- `--scorecard PATH` (YAML)
- `--out PATH` (report JSON)
- `--run-id STRING` (optional; deterministic fallback to UTC timestamp)
- `--model STRING` (default mock backend label)

Flow:

1. Parse dataset rows and scorecard.
2. Execute each case via deterministic mock backend.
3. Aggregate metric values and compute threshold pass/fail.
4. Build report with metric/domain/overall summaries and case summary.
5. Write report JSON.

Output:

- Machine-readable JSON report consumable by `evals compare`.

### `evals compare`

Inputs:

- `--base PATH`
- `--candidate PATH`
- `--out PATH` (optional)

Flow:

1. Parse both reports.
2. Compute overall and per-domain deltas.
3. Compute metric-level deltas.
4. Identify newly introduced threshold failures and resolved failures.

Output:

- Human-readable stdout summary.
- Optional JSON comparison artifact when `--out` is provided.

## Scoring Rules (First Slice)

- Per-case metric values are produced by the mock backend.
- Aggregation rule:
  - Default: arithmetic mean of per-case values.
  - `p95_*` metrics: p95 percentile.
- Threshold operators supported: `>=`, `<=`, `>`, `<`, `==`.
- Metric score normalization to `[0, 100]`:
  - For `>=`/`>`: `min(100, value / threshold * 100)` (bounded at 0).
  - For `<=`/`<`: `min(100, threshold / value * 100)` (bounded at 0; zero-value handling).
  - For `==`: `100` if equal else `0`.
- Domain score: mean of metric normalized scores in domain.
- Overall score: weighted mean of domain scores.

## Deterministic Mock Evaluator

Design goals:

- No network calls.
- Stable outputs across machines and repeated runs.
- Metric-aware value ranges.

Implementation rule:

- Seed derivation uses stable SHA-256 hash of `case_id`, `metric_name`, and `task_type`.
- Metric family behaviors:
  - `p95_latency_ms`: bounded ms range.
  - `avg_cost_usd`: bounded USD range.
  - Other metrics: `[0, 1]` range.

## Testing Strategy

Unit tests:

- `test_scoring.py`
  - Domain/overall aggregation with known fixture values.
  - Threshold failure detection for both `>=` and `<=`.
- `test_compare.py`
  - Correct delta calculations.
  - Correct detection of newly failed vs resolved thresholds.

Integration-style CLI test coverage (first slice):

- Use parser/scoring/report modules directly for deterministic assertions.

## Milestone: First Working Slice

1. Add package config and installable CLI entrypoint.
2. Implement typed models and parsers.
3. Implement deterministic mock evaluator.
4. Implement scoring, reporting, comparison.
5. Implement `evals run` and `evals compare`.
6. Add tests and ensure local run passes.
7. Update README to concrete, runnable commands and outputs.
