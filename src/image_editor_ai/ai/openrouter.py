"""Minimal OpenRouter client: chat completions, the Decisions API and the Image API."""

import base64
import binascii

import httpx

from image_editor_ai import APP_NAME
from image_editor_ai.config import Settings


class OpenRouterError(RuntimeError):
    """Raised when the API answers without usable content."""


def _raise_api_error(data: dict) -> None:
    """Raise the error message an OpenRouter response body carries, if any."""
    if "error" in data:
        error = data["error"]
        message = error.get("message", "unknown error") if isinstance(error, dict) else error
        raise OpenRouterError(f"OpenRouter error: {message}")


def _json_body(response: httpx.Response) -> dict:
    """Response JSON; HTTP errors without an OpenRouter error body raise HTTPStatusError."""
    try:
        data = response.json()
    except ValueError:  # body is not JSON
        data = {}
    if response.is_error and "error" not in data:
        response.raise_for_status()
    return data


def extract_content(data: dict) -> str:
    """Text of the first choice of a chat completion response."""
    _raise_api_error(data)
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("Unexpected response from OpenRouter.") from exc
    if not content or not content.strip():
        raise OpenRouterError("The model returned an empty response.")
    return content.strip()


def extract_answers(data: dict) -> dict:
    """Typed answers of a Decisions API response, keyed by question name."""
    _raise_api_error(data)
    answers = data.get("answers")
    if not isinstance(answers, dict) or not answers:
        raise OpenRouterError("Unexpected response from the OpenRouter Decisions API.")
    return answers


def extract_images(data: dict) -> list[bytes]:
    """Decoded image files of an Image API response."""
    _raise_api_error(data)
    try:
        images = [base64.b64decode(item["b64_json"], validate=True) for item in data["data"]]
    except (KeyError, TypeError, binascii.Error) as exc:
        raise OpenRouterError("Unexpected response from the OpenRouter Image API.") from exc
    if not images:
        raise OpenRouterError("The model returned no image.")
    return images


class OpenRouterClient:
    def __init__(self, settings: Settings, timeout: float = 120.0) -> None:
        self._model = settings.require_model()
        self._decisions_url = settings.decisions_url
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
        return _json_body(response)

    def complete(self, messages: list[dict], **extra) -> str:
        """Send a chat request and return the reply text."""
        return extract_content(self.chat(messages, **extra))

    def decide(self, model: str, state: list, questions: dict) -> dict:
        """Ask a Decisions model typed questions about `state`; returns its answers."""
        # An absolute URL bypasses base_url, so the same auth headers are reused.
        response = self._http.post(
            self._decisions_url, json={"model": model, "state": state, "questions": questions}
        )
        return extract_answers(_json_body(response))

    def generate_images(
        self, model: str, prompt: str, input_references: list[str] | None = None
    ) -> list[bytes]:
        """Generate (or, with reference image data URLs, edit) images; returns image files."""
        payload: dict = {"model": model, "prompt": prompt}
        if input_references:
            payload["input_references"] = [
                {"type": "image_url", "image_url": {"url": url}} for url in input_references
            ]
        response = self._http.post("/images", json=payload)
        return extract_images(_json_body(response))

    def close(self) -> None:
        self._http.close()
