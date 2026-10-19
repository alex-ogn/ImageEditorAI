import pytest

from image_editor_ai.config import (
    DEFAULT_BASE_URL,
    DEFAULT_DECISIONS_URL,
    DEFAULT_DESCRIBE_PROMPT,
    DEFAULT_MODEL,
    ConfigError,
    load_settings,
)


def test_load_settings_from_env_file(tmp_path, monkeypatch):
    for var in ("OPENROUTER_API_KEY", "OPENROUTER_MODEL", "OPENROUTER_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY=test-key\nOPENROUTER_MODEL=some/model\n")

    settings = load_settings(env)
    assert settings.require_api_key() == "test-key"
    assert settings.require_model() == "some/model"
    assert settings.base_url == DEFAULT_BASE_URL


def test_missing_key_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    settings = load_settings(tmp_path / "missing.env")
    with pytest.raises(ConfigError):
        settings.require_api_key()


def test_describe_defaults(tmp_path, monkeypatch):
    for var in ("OPENROUTER_MODEL", "DESCRIBE_PROMPT"):
        monkeypatch.delenv(var, raising=False)
    settings = load_settings(tmp_path / "missing.env")
    assert settings.model == DEFAULT_MODEL == "qwen/qwen3-vl-8b-instruct"
    assert settings.describe_prompt == DEFAULT_DESCRIBE_PROMPT


def test_describe_prompt_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("DESCRIBE_PROMPT", raising=False)
    env = tmp_path / ".env"
    env.write_text('DESCRIBE_PROMPT="Describe it briefly."\n')
    assert load_settings(env).describe_prompt == "Describe it briefly."


def test_detect_defaults_and_overrides(tmp_path, monkeypatch):
    for var in ("DETECT_MODEL", "OPENROUTER_DECISIONS_URL", "DETECT_PRESENCE_THRESHOLD"):
        monkeypatch.delenv(var, raising=False)
    defaults = load_settings(tmp_path / "missing.env")
    assert defaults.detect_model == "typesafe/jev-1.14"
    assert defaults.decisions_url == DEFAULT_DECISIONS_URL
    assert defaults.detect_presence_threshold == 0.5

    env = tmp_path / ".env"
    env.write_text("DETECT_MODEL=other/model\nDETECT_PRESENCE_THRESHOLD=0.7\n")
    settings = load_settings(env)
    assert settings.detect_model == "other/model"
    assert settings.detect_presence_threshold == 0.7


def test_invalid_threshold_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("DETECT_PRESENCE_THRESHOLD", raising=False)
    env = tmp_path / ".env"
    env.write_text("DETECT_PRESENCE_THRESHOLD=high\n")
    with pytest.raises(ConfigError):
        load_settings(env)
