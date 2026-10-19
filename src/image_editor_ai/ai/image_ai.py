"""AI features over images: upload preparation, vision payloads and descriptions."""

import base64
import io

from PIL import Image

from image_editor_ai.ai.openrouter import OpenRouterClient
from image_editor_ai.config import Settings
from image_editor_ai.imaging import fit_size

# Longest side sent to the model; larger images are scaled down (ratio kept).
MAX_UPLOAD_SIDE = 1536


def prepare_for_upload(image: Image.Image, max_side: int = MAX_UPLOAD_SIDE) -> Image.Image:
    """Copy of the image in RGB, scaled down uniformly so it fits max_side."""
    prepared = image.convert("RGB")
    if max(prepared.size) > max_side:
        size = fit_size(*prepared.size, max_side, max_side)
        prepared = prepared.resize(size, Image.Resampling.LANCZOS)
    return prepared


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


def ask_about_image(client: OpenRouterClient, prompt: str, image: Image.Image) -> str:
    return client.complete([build_image_message(prompt, image)])


def describe_image(settings: Settings, image: Image.Image) -> str:
    """Ask the configured vision model for a description, using the prompt from .env."""
    client = OpenRouterClient(settings)
    try:
        return ask_about_image(client, settings.describe_prompt, image)
    finally:
        client.close()
