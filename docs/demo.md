# Demo

The repo includes a live baseline-vs-candidate walkthrough.

Inputs:

- `demo/input/scorecard.yaml`
- `demo/input/dataset.baseline.jsonl`
- `demo/input/dataset.candidate.jsonl`

Outputs:

- `demo/output/baseline-report.json`
- `demo/output/candidate-report.json`
- `demo/output/baseline-vs-candidate.json`
- `demo/output/demo-summary.json`

Run it:

```bash
export AI_EVALS_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
export AZURE_OPENAI_API_KEY="<key>"
export AZURE_OPENAI_JUDGE_DEPLOYMENT="gpt-5.4"
uv run python scripts/run_live_demo.py
```

What the demo shows:

- the baseline output misses required workflow steps and omits a required policy flag
- the candidate output clears all semantic thresholds
- latency and cost stay separate from judge scoring
- the comparison report resolves four threshold failures
