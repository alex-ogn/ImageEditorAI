"""Application settings loaded from the project's .env file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class ConfigError(RuntimeError):
    """Raised when a required setting is missing."""


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str | None
    base_url: str

    def require_api_key(self) -> str:
        if not self.api_key:
            raise ConfigError(
                "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        return self.api_key

    def require_model(self) -> str:
        if not self.model:
            raise ConfigError("OPENROUTER_MODEL is not set in .env.")
        return self.model


def load_settings(env_file: Path | None = None) -> Settings:
    load_dotenv(env_file or PROJECT_ROOT / ".env")
    return Settings(
        api_key=os.getenv("OPENROUTER_API_KEY") or None,
        model=os.getenv("OPENROUTER_MODEL") or None,
        base_url=os.getenv("OPENROUTER_BASE_URL") or DEFAULT_BASE_URL,
    )
