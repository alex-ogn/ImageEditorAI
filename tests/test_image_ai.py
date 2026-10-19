import pytest
from PIL import Image

from image_editor_ai.ai.image_ai import (
    BOX_QUESTION,
    JEV_MAX_SIDE,
    JEV_MIN_PIXELS,
    JEV_MIN_SIDE,
    MAX_UPLOAD_SIDE,
    PRESENCE_QUESTION,
    Detection,
    build_detection_request,
    build_image_message,
    format_detection,
    parse_detection,
    prepare_for_jev,
    prepare_for_upload,
)
from image_editor_ai.ai.openrouter import OpenRouterError


def test_prepare_for_upload_downscales_keeping_ratio():
    prepared = prepare_for_upload(Image.new("RGBA", (4000, 2000)))
    assert prepared.mode == "RGB"
    assert prepared.size == (MAX_UPLOAD_SIDE, MAX_UPLOAD_SIDE // 2)


def test_prepare_for_upload_keeps_small_images():
    assert prepare_for_upload(Image.new("L", (300, 200))).size == (300, 200)


def test_build_image_message_payload():
    message = build_image_message("Describe.", Image.new("RGB", (10, 10)))
    text, image = message["content"]
    assert message["role"] == "user"
    assert text == {"type": "text", "text": "Describe."}
    assert image["image_url"]["url"].startswith("data:image/jpeg;base64,")


@pytest.mark.parametrize("size", [(4000, 3000), (100, 50), (20, 20), (1000, 200), (300, 300)])
def test_prepare_for_jev_fits_limits_and_keeps_ratio(size):
    w, h = prepare_for_jev(Image.new("RGBA", size)).size
    assert JEV_MIN_SIDE <= min(w, h) and max(w, h) <= JEV_MAX_SIDE
    assert w * h >= JEV_MIN_PIXELS
    assert abs(w / h - size[0] / size[1]) <= 0.02 * size[0] / size[1]


def test_prepare_for_jev_rejects_extreme_aspect_ratio():
    with pytest.raises(ValueError, match="aspect ratio"):
        prepare_for_jev(Image.new("RGB", (3000, 400)))


def test_build_detection_request():
    image = Image.new("RGB", (400, 300))
    state, questions = build_detection_request("A dog on grass.", "Where is the dog?", image)
    assert state[0] == "Image description: A dog on grass."
    assert state[1] == "User question: Where is the dog?"
    assert state[2]["type"] == "image_url"
    assert state[2]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert questions[PRESENCE_QUESTION]["type"] == "noul"
    assert questions[BOX_QUESTION]["type"] == "box"
    assert "criteria" not in questions[BOX_QUESTION]


def _answers(presence, box, confidence=0.9):
    return {
        PRESENCE_QUESTION: {"type": "noul", "noul": presence},
        BOX_QUESTION: {"type": "box", "box": box, "confidence": confidence},
    }


def test_parse_detection_found_orders_and_clamps_edges():
    box = {"top": 0.8, "bottom": 0.2, "left": -0.1, "right": 0.5}
    detection = parse_detection(_answers(0.92, box, 0.88), threshold=0.5)
    assert detection == Detection(
        found=True, presence=0.92, confidence=0.88, box=(0.0, 0.2, 0.5, 0.8)
    )


def test_parse_detection_not_found_has_no_box():
    box = {"top": 0.1, "bottom": 0.2, "left": 0.1, "right": 0.2}
    detection = parse_detection(_answers(0.12, box), threshold=0.5)
    assert not detection.found
    assert detection.box is None
    assert detection.presence == 0.12


def test_parse_detection_rejects_malformed_answers():
    with pytest.raises(OpenRouterError):
        parse_detection({PRESENCE_QUESTION: {"noul": 0.9}}, threshold=0.5)


def test_format_detection_always_shows_percentages():
    found = Detection(found=True, presence=0.92, confidence=0.876, box=(0, 0, 1, 1))
    missing = Detection(found=False, presence=0.12, confidence=0.4, box=None)
    assert format_detection(found) == "Found — confidence 88% (object present: 92%)"
    assert format_detection(missing) == "Not found — object present: 12%"
