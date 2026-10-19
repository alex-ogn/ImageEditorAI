"""Minimal OpenRouter client (OpenAI-compatible chat completions API)."""

import base64
import io

import httpx
from PIL import Image

from image_editor_ai import APP_NAME
from image_editor_ai.config import Settings
from image_editor_ai.imaging import fit_size

# Longest side sent to the model; larger images are scaled down (ratio kept).
MAX_UPLOAD_SIDE = 1536


class OpenRouterError(RuntimeError):
    """Raised when the API answers without usable content."""


def prepare_for_upload(image: Image.Image, max_side: int = MAX_UPLOAD_SIDE) -> Image.Image:
    """Copy of the image in RGB, scaled down uniformly so it fits max_side."""
    prepared = image.convert("RGB")
    if max(prepared.size) > max_side:
        size = fit_size(*prepared.size, max_side, max_side)
        prepared = prepared.resize(size, Image.Resampling.LANCZOS)
    return prepared


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


def image_to_data_url(image: Image.Image, fmt: str = "PNG") -> str:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/{fmt.lower()};base64,{encoded}"


def build_image_message(prompt: str, image: Image.Image) -> dict:
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": image_to_data_url(prepare_for_upload(image), "JPEG")},
            },
        ],
    }


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

    def ask_about_image(self, prompt: str, image: Image.Image) -> str:
        return extract_content(self.chat([build_image_message(prompt, image)]))

    def close(self) -> None:
        self._http.close()


def describe_image(settings: Settings, image: Image.Image) -> str:
    """Ask the configured vision model for a description, using the prompt from .env."""
    client = OpenRouterClient(settings)
    try:
        return client.ask_about_image(settings.describe_prompt, image)
    finally:
        client.close()
