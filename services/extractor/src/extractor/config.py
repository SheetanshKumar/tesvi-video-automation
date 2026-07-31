"""Env-based config loader (12-factor)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    port: int
    database_url: str | None
    anthropic_api_key: str | None
    anthropic_model: str

    @classmethod
    def load(cls) -> Config:
        return cls(
            port=int(os.environ.get("PORT", "8080")),
            database_url=os.environ.get("DATABASE_URL"),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
            anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        )
