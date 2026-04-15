from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    provider_mode: str = "deterministic"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str = "2025-04-01-preview"
    azure_openai_judge_deployment: str = "gpt-5.4"
    azure_openai_smoke_deployment: str = "gpt-5-mini"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            provider_mode=os.getenv("AI_EVALS_PROVIDER", "deterministic").strip().lower(),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_API_KEY"),
            azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
            azure_openai_judge_deployment=os.getenv(
                "AZURE_OPENAI_JUDGE_DEPLOYMENT",
                "gpt-5.4",
            ),
            azure_openai_smoke_deployment=os.getenv(
                "AZURE_OPENAI_SMOKE_DEPLOYMENT",
                "gpt-5-mini",
            ),
        )

    @property
    def live_provider_enabled(self) -> bool:
        return self.provider_mode == "azure"

    def validate_for_live_mode(self) -> None:
        missing = []
        if not self.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if missing:
            raise RuntimeError(
                "Azure judge mode is enabled but missing environment variables: "
                + ", ".join(missing)
            )
