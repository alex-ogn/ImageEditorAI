import json

import httpx
import pytest

from image_editor_ai.ai.openrouter import OpenRouterClient, OpenRouterError, extract_content
from image_editor_ai.config import DEFAULT_BASE_URL, DEFAULT_DECISIONS_URL, Settings


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


def _client(handler, monkeypatch) -> OpenRouterClient:
    settings = Settings(api_key="test-key", model="some/model", base_url=DEFAULT_BASE_URL)
    client = OpenRouterClient(settings)
    # Swap in a mock transport, keeping the client's base URL and headers.
    mock_http = httpx.Client(
        base_url=client._http.base_url,
        headers=client._http.headers,
        transport=httpx.MockTransport(handler),
    )
    monkeypatch.setattr(client, "_http", mock_http)
    return client


def test_decide_posts_to_decisions_api(monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"] == "Bearer test-key"
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"answers": {"q": {"type": "noul", "noul": 0.7}}})

    client = _client(handler, monkeypatch)
    answers = client.decide("typesafe/jev-1.14", ["state"], {"q": {"type": "noul"}})
    assert answers == {"q": {"type": "noul", "noul": 0.7}}
    assert seen["url"] == DEFAULT_DECISIONS_URL
    assert seen["auth"]
    assert seen["body"]["model"] == "typesafe/jev-1.14"
    assert seen["body"]["state"] == ["state"]


def test_decide_reports_api_error_message(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(413, json={"error": {"message": "Image too large"}})

    with pytest.raises(OpenRouterError, match="Image too large"):
        _client(handler, monkeypatch).decide("m", [], {})


def test_decide_raises_http_error_without_json(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="Bad gateway")

    with pytest.raises(httpx.HTTPStatusError):
        _client(handler, monkeypatch).decide("m", [], {})
