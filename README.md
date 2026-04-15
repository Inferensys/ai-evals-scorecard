# ai-evals-scorecard

Score model behavior against a rubric. Emit JSON. Diff runs.

No dashboard. No mystery weights. No vendor-locked eval studio.

This repo does three things:

- grades semantic behavior with a live judge model
- reads latency and cost directly from observed telemetry
- turns the result into a report that can block or ship a release

The aggregation layer is deterministic. The judge is replaceable. The report is diffable.

## What Is Implemented

- `evals run`: load a JSONL dataset, score each case, aggregate domain scores, emit a run report
- `evals compare`: compare two run reports and surface deltas and threshold regressions
- deterministic backend for offline development
- Azure OpenAI judge backend for semantic metrics
- case-level rationales embedded in the run report

## Demo

The live demo set in `demo/` was generated with Azure OpenAI `gpt-5.4`.

Artifacts:

- baseline run: `demo/output/baseline-report.json`
- candidate run: `demo/output/candidate-report.json`
- diff report: `demo/output/baseline-vs-candidate.json`
- run index: `demo/output/demo-summary.json`

Observed result:

```json
[
  {
    "name": "baseline",
    "overall_score": 47.763,
    "threshold_failures": 4
  },
  {
    "name": "candidate",
    "overall_score": 100.0,
    "threshold_failures": 0
  },
  {
    "name": "comparison",
    "overall_delta": 52.237,
    "resolved_threshold_failures": 4
  }
]
```

Candidate run excerpt:

```json
{
  "model": "azure-openai/gpt-5.4",
  "overall_score": 100.0,
  "domain_scores": {
    "quality": 100.0,
    "execution": 100.0,
    "latency": 100.0,
    "cost": 100.0
  }
}
```

Baseline case excerpt:

```json
{
  "case_id": "case_001",
  "passed": false,
  "metrics": [
    {
      "domain": "quality",
      "name": "policy_compliance",
      "value": 0.0,
      "source": "azure-openai",
      "rationale": "The expected policy flag requires_approval was not raised despite being required for this workflow."
    }
  ]
}
```

## Run It

Install:

```bash
uv sync --group dev
```

Deterministic smoke run:

```bash
uv run evals run \
  --dataset examples/dataset.support-workflow.jsonl \
  --scorecard examples/scorecard.yaml \
  --out reports/run-smoke.json \
  --run-id smoke_det
```

Live Azure judge run:

```bash
export AI_EVALS_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
export AZURE_OPENAI_API_KEY="<key>"
export AZURE_OPENAI_API_VERSION="2025-04-01-preview"
export AZURE_OPENAI_JUDGE_DEPLOYMENT="gpt-5.4"

uv run evals run \
  --dataset demo/input/dataset.candidate.jsonl \
  --scorecard demo/input/scorecard.yaml \
  --out demo/output/candidate-report.json \
  --run-id demo_candidate_20260416
```

Compare two runs:

```bash
uv run evals compare \
  --base demo/output/baseline-report.json \
  --candidate demo/output/candidate-report.json \
  --out demo/output/baseline-vs-candidate.json
```

Regenerate the full live demo:

```bash
uv run python scripts/run_live_demo.py
```

## Dataset Contract

Each row carries the task, the observed system output, and the expected behavior:

```json
{
  "case_id": "case_001",
  "task_type": "workflow",
  "input": {
    "prompt": "Pause renewal for account acct_882 for one cycle and notify billing owner."
  },
  "observed": {
    "output_text": "Pause renewal for one billing cycle on acct_882...",
    "actions": ["pause_renewal", "send_notification"],
    "policy_flags": ["requires_approval"],
    "metrics": {
      "latency_ms": 1420,
      "cost_usd": 0.028
    }
  },
  "expected": {
    "required_actions": ["pause_renewal", "send_notification"],
    "policy_flags": ["requires_approval"]
  }
}
```

If you do not have observed outputs yet, this is not the right layer. Generate outputs upstream, then score them here.

## Metric Routing

- semantic metrics such as `answer_correctness`, `policy_compliance`, and `workflow_completion` go to the judge backend
- telemetry metrics such as `p95_latency_ms` and `avg_cost_usd` are read from `observed.metrics`
- aggregation and thresholds stay local and deterministic

## Files That Matter

- `src/ai_evals_scorecard/cli.py`
- `src/ai_evals_scorecard/backend.py`
- `src/ai_evals_scorecard/azure_backend.py`
- `src/ai_evals_scorecard/scoring.py`
- `demo/input/`
- `demo/output/`

## Azure Notes

Provider setup and portability notes are in `docs/azure-foundry.md`.

## Tests

```bash
uv run pytest -q
```
