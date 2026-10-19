"""Minimal OpenRouter client (OpenAI-compatible chat completions API)."""

import httpx

from image_editor_ai import APP_NAME
from image_editor_ai.config import Settings


class OpenRouterError(RuntimeError):
    """Raised when the API answers without usable content."""


def extract_content(data: dict) -> str:
    """Text of the first choice of a chat completion response."""
    if "error" in data:
        message = data["error"].get("message", "unknown error")
        raise OpenRouterError(f"OpenRouter error: {message}")
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("Unexpected response from OpenRouter.") from exc
    if not content or not content.strip():
        raise OpenRouterError("The model returned an empty response.")
    return content.strip()


class OpenRouterClient:
    def __init__(self, settings: Settings, timeout: float = 120.0) -> None:
        self._model = settings.require_model()
        self._http = httpx.Client(
            base_url=settings.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {settings.require_api_key()}",
                "X-Title": APP_NAME,
            },
        )

    def chat(self, messages: list[dict], **extra) -> dict:
        response = self._http.post(
            "/chat/completions", json={"model": self._model, "messages": messages, **extra}
        )
        response.raise_for_status()
        return response.json()

    def complete(self, messages: list[dict], **extra) -> str:
        """Send a chat request and return the reply text."""
        return extract_content(self.chat(messages, **extra))

    def close(self) -> None:
        self._http.close()
