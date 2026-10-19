import pytest
from PIL import Image

from image_editor_ai.ai.openrouter import (
    MAX_UPLOAD_SIDE,
    OpenRouterError,
    build_image_message,
    extract_content,
    prepare_for_upload,
)


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


def test_extract_content():
    data = {"choices": [{"message": {"content": "  A cat on a sofa.\n"}}]}
    assert extract_content(data) == "A cat on a sofa."


@pytest.mark.parametrize(
    "data",
    [
        {"error": {"message": "Invalid key"}},
        {"choices": []},
        {"choices": [{"message": {"content": "   "}}]},
    ],
)
def test_extract_content_errors(data):
    with pytest.raises(OpenRouterError):
        extract_content(data)
