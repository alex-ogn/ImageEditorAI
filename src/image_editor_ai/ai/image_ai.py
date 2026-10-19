"""AI features over images: upload preparation, descriptions and object detection."""

import base64
import io
import math
from dataclasses import dataclass

from PIL import Image

from image_editor_ai.ai.openrouter import OpenRouterClient, OpenRouterError
from image_editor_ai.config import Settings
from image_editor_ai.imaging import Box, fit_size

# Longest side sent to the model; larger images are scaled down (ratio kept).
MAX_UPLOAD_SIDE = 1536

# Jev image limits: every side 256..1568 px and 78,400..2,458,624 px in total.
JEV_MIN_SIDE = 256
JEV_MAX_SIDE = 1568
JEV_MIN_PIXELS = 78_400

# Question names in the Decisions request.
PRESENCE_QUESTION = "present"
BOX_QUESTION = "target"


@dataclass(frozen=True)
class Detection:
    found: bool
    presence: float  # probability that the asked-about object is in the image
    confidence: float  # Jev's confidence in the box
    box: Box | None  # None when the object is not found


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


def prepare_for_jev(image: Image.Image) -> Image.Image:
    """RGB copy scaled uniformly into Jev's size limits (down to MAX_UPLOAD_SIDE, or up)."""
    prepared = image.convert("RGB")
    w, h = prepared.size
    scale = min(1.0, MAX_UPLOAD_SIDE / max(w, h))
    scale = max(scale, JEV_MIN_SIDE / min(w, h), math.sqrt(JEV_MIN_PIXELS / (w * h)))
    if scale > 1:
        size = (math.ceil(w * scale), math.ceil(h * scale))
    elif scale < 1:
        size = fit_size(w, h, round(w * scale), round(h * scale))
    else:
        return prepared
    if max(size) > JEV_MAX_SIDE:
        raise ValueError(
            f"The image is {w}×{h} px; its aspect ratio is too extreme for object detection "
            f"(each side must fit {JEV_MIN_SIDE}–{JEV_MAX_SIDE} px after uniform scaling)."
        )
    return prepared.resize(size, Image.Resampling.LANCZOS)


def build_detection_request(
    description: str, question: str, image: Image.Image
) -> tuple[list, dict]:
    """Decisions `state` and `questions` asking Jev to locate what the question is about."""
    state = [
        f"Image description: {description}",
        f"User question: {question}",
        {
            "type": "image_url",
            "image_url": {"url": image_to_data_url(prepare_for_jev(image), "JPEG")},
        },
    ]
    questions = {
        PRESENCE_QUESTION: {
            "type": "noul",
            "instructions": "The image contains the object the user question asks about.",
        },
        # Box instructions describe the target rather than give a command.
        BOX_QUESTION: {
            "type": "box",
            "instructions": "the object in the image that the user question asks about",
        },
    }
    return state, questions


def _fraction(value: object) -> float:
    return min(1.0, max(0.0, float(value)))


def parse_detection(answers: dict, threshold: float) -> Detection:
    """Turn Jev's typed answers into a Detection; the box is kept only if the object is present."""
    try:
        presence = _fraction(answers[PRESENCE_QUESTION]["noul"])
        target = answers[BOX_QUESTION]
        edges = target["box"]
        confidence = _fraction(target.get("confidence", 0.0))
        left, right = sorted((_fraction(edges["left"]), _fraction(edges["right"])))
        top, bottom = sorted((_fraction(edges["top"]), _fraction(edges["bottom"])))
    except (KeyError, TypeError, ValueError) as exc:
        raise OpenRouterError("Unexpected object detection answer from the model.") from exc
    found = presence >= threshold
    return Detection(
        found=found,
        presence=presence,
        confidence=confidence,
        box=(left, top, right, bottom) if found else None,
    )


def format_detection(detection: Detection) -> str:
    """Result text for the user, always including the percentages."""
    if detection.found:
        return (
            f"Found — confidence {detection.confidence:.0%} "
            f"(object present: {detection.presence:.0%})"
        )
    return f"Not found — object present: {detection.presence:.0%}"


def detect_object(
    settings: Settings, image: Image.Image, description: str, question: str
) -> Detection:
    """Locate the object the question asks about, offloaded to the Jev Decisions model."""
    state, questions = build_detection_request(description, question, image)
    client = OpenRouterClient(settings)
    try:
        answers = client.decide(settings.detect_model, state, questions)
    finally:
        client.close()
    return parse_detection(answers, settings.detect_presence_threshold)
