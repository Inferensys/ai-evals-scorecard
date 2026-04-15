# ai-evals-scorecard

Specification-first templates for evaluating LLM and agentic systems with reproducible datasets, explicit metric definitions, and machine-readable reports.

Unlike prompt spot-checking, this repository treats evaluation as a versioned artifact pipeline:
- dataset rows are immutable test cases
- metrics are typed and weighted
- reports are comparable across runs and models

## Scope

`ai-evals-scorecard` models four evaluation domains:

- `quality`: correctness, groundedness, policy compliance
- `execution`: tool success and workflow completion
- `latency`: end-to-end and per-stage timings
- `cost`: token + tool execution spend

The repo is intentionally framework-agnostic. You can plug it into any runner.

## Minimal Workflow

```bash
# 1) define your metric contract
cp examples/scorecard.yaml ./scorecard.yaml

# 2) prepare dataset rows
cp examples/dataset.support-workflow.jsonl ./datasets/support.jsonl

# 3) run your evaluator (implementation-specific)
evals run --dataset ./datasets/support.jsonl --scorecard ./scorecard.yaml --out ./reports/run-001.json

# 4) compare with baseline
evals compare --base ./reports/run-000.json --candidate ./reports/run-001.json
```

## Contracts in This Repository

- Scorecard contract: [`examples/scorecard.yaml`](examples/scorecard.yaml)
- Dataset row contract: [`docs/eval-schema.md`](docs/eval-schema.md)
- Report contract: [`examples/report.run-summary.json`](examples/report.run-summary.json)
- Runner architecture: [`docs/runner-design.md`](docs/runner-design.md)

## Scoring Model (Reference)

Default aggregate score:

```text
overall = 0.45 * quality + 0.25 * execution + 0.20 * latency + 0.10 * cost
```

Each domain is normalized to `[0, 100]`. Projects should tune these weights by risk profile.

## Example Use Cases

- release-gate checks for model or prompt updates
- nightly regression runs for RAG-backed support flows
- canary comparison of routing strategies
- incident backtesting with archived traces

## Reproducibility Rules

- Pin model version and runner commit in each report.
- Keep datasets append-only; never mutate historical rows.
- Store raw evaluator outputs alongside summarized metrics.
- Fail CI when critical metric thresholds regress.

## Demo and Visual Assets

- Step-by-step run: [docs/demo.md](docs/demo.md)
- Placeholder asset naming: [assets/README.md](assets/README.md)
