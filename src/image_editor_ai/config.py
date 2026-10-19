"""Application settings loaded from the project's .env file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "qwen/qwen3-vl-8b-instruct"
DEFAULT_DESCRIBE_PROMPT = (
    "Describe this image in detail. Cover the main subject, setting, composition, "
    "colors, lighting, mood and any visible text. Write clear, well-structured prose "
    "in a few short paragraphs, without preamble."
)


class ConfigError(RuntimeError):
    """Raised when a required setting is missing."""


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str | None
    base_url: str
    describe_prompt: str = DEFAULT_DESCRIBE_PROMPT

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
        model=os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL,
        base_url=os.getenv("OPENROUTER_BASE_URL") or DEFAULT_BASE_URL,
        describe_prompt=os.getenv("DESCRIBE_PROMPT") or DEFAULT_DESCRIBE_PROMPT,
    )
