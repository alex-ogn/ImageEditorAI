from PIL import Image

from image_editor_ai.ai.image_ai import MAX_UPLOAD_SIDE, build_image_message, prepare_for_upload


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
