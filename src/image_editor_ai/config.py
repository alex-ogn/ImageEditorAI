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
DEFAULT_DETECT_MODEL = "typesafe/jev-1.14"
DEFAULT_DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_DETECT_PRESENCE_THRESHOLD = 0.5
DEFAULT_EDIT_MODEL = "meta/muse-image"
# "{request}" is replaced by the user's modification request.
DEFAULT_EDIT_PROMPT = (
    "Edit the provided image as follows: {request} "
    "Keep everything else in the image unchanged, including the composition, framing, "
    "subjects and style."
)


class ConfigError(RuntimeError):
    """Raised when a required setting is missing."""


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str | None
    base_url: str
    describe_prompt: str = DEFAULT_DESCRIBE_PROMPT
    detect_model: str = DEFAULT_DETECT_MODEL
    decisions_url: str = DEFAULT_DECISIONS_URL
    detect_presence_threshold: float = DEFAULT_DETECT_PRESENCE_THRESHOLD
    edit_model: str = DEFAULT_EDIT_MODEL
    edit_prompt: str = DEFAULT_EDIT_PROMPT

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


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        raise ConfigError(f"{name} must be a number, got {value!r}.") from None


def load_settings(env_file: Path | None = None) -> Settings:
    load_dotenv(env_file or PROJECT_ROOT / ".env")
    return Settings(
        api_key=os.getenv("OPENROUTER_API_KEY") or None,
        model=os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL,
        base_url=os.getenv("OPENROUTER_BASE_URL") or DEFAULT_BASE_URL,
        describe_prompt=os.getenv("DESCRIBE_PROMPT") or DEFAULT_DESCRIBE_PROMPT,
        detect_model=os.getenv("DETECT_MODEL") or DEFAULT_DETECT_MODEL,
        decisions_url=os.getenv("OPENROUTER_DECISIONS_URL") or DEFAULT_DECISIONS_URL,
        detect_presence_threshold=_float_env(
            "DETECT_PRESENCE_THRESHOLD", DEFAULT_DETECT_PRESENCE_THRESHOLD
        ),
        edit_model=os.getenv("EDIT_MODEL") or DEFAULT_EDIT_MODEL,
        edit_prompt=os.getenv("EDIT_PROMPT") or DEFAULT_EDIT_PROMPT,
    )
