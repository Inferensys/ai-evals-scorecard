# Azure Foundry Notes

## Environment

```bash
export AI_EVALS_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
export AZURE_OPENAI_API_KEY="<key>"
export AZURE_OPENAI_API_VERSION="2025-04-01-preview"
export AZURE_OPENAI_JUDGE_DEPLOYMENT="gpt-5.4"
```

The Azure backend is isolated to `src/ai_evals_scorecard/azure_backend.py`.

## Model Choice

- default judge tier: `gpt-5.4`
- cheaper smoke tier if you want to add one in CI: `gpt-5-mini`

This repo currently uses the stronger tier for the checked-in demo artifacts because semantic scoring quality matters more than marginal latency in this workflow.

## Portability Boundary

The portability seam is `EvaluationBackend.evaluate_case(...)`.

Any provider can be swapped in if it returns metric scores mapped to:

- `domain`
- `name`
- `value`
- `rationale`
- `source`

The score aggregation and report shape do not need to change.

Equivalent implementations:

- Vertex AI Gemini judge backend
- OpenAI API backend
- Anthropic tool-use backend
- internal rubric model behind an HTTP adapter
