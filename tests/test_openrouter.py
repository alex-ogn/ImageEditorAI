import pytest

from image_editor_ai.ai.openrouter import OpenRouterError, extract_content


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
