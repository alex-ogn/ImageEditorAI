"""Minimal OpenRouter client (OpenAI-compatible chat completions API)."""

import base64
import io

import httpx
from PIL import Image

from image_editor_ai import APP_NAME
from image_editor_ai.config import Settings


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
            {"type": "image_url", "image_url": {"url": image_to_data_url(image)}},
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
        data = self.chat([build_image_message(prompt, image)])
        return data["choices"][0]["message"]["content"]

    def close(self) -> None:
        self._http.close()
