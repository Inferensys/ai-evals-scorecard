# Demo: Baseline vs Candidate Run

This walkthrough shows a two-run comparison using the sample scorecard and dataset.

## Inputs

- scorecard: [`examples/scorecard.yaml`](../examples/scorecard.yaml)
- dataset: [`examples/dataset.support-workflow.jsonl`](../examples/dataset.support-workflow.jsonl)

## Run Sequence

```bash
evals run --dataset examples/dataset.support-workflow.jsonl --scorecard examples/scorecard.yaml --out reports/run-baseline.json
evals run --dataset examples/dataset.support-workflow.jsonl --scorecard examples/scorecard.yaml --out reports/run-candidate.json
evals compare --base reports/run-baseline.json --candidate reports/run-candidate.json
```

## Expected Outputs

- candidate report contains domain scores and weighted aggregate
- compare output highlights per-domain deltas
- threshold failures are listed with metric names and case IDs

Sample report shape: [`examples/report.run-summary.json`](../examples/report.run-summary.json)
