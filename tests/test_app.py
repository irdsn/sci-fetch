from fastapi.testclient import TestClient
import httpx
from openai import AuthenticationError

from app import app

client = TestClient(app)


def test_run_endpoint_with_mock(monkeypatch):
    """The /run endpoint should proxy the agent result using the current API contract."""

    captured = {}

    def mock_run_agent(prompt, api_key):
        captured["prompt"] = prompt
        captured["api_key"] = api_key
        return {
            "summary": "mock summary",
            "articles": [{"title": "Paper"}],
            "html_preview": "<html><body>Preview</body></html>",
            "output_file": "C:/reports/mock_report.pdf",
        }

    monkeypatch.setattr("app.run_agent", mock_run_agent)

    response = client.post(
        "/run",
        json={
            "prompt": "cancer prevention",
            "api_key": "sk-test-key",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert captured == {
        "prompt": "cancer prevention",
        "api_key": "sk-test-key",
    }
    assert data["filename"] == "mock_report.pdf"
    assert data["output_file"].endswith("mock_report.pdf")
    assert data["html_preview"] == "<html><body>Preview</body></html>"
    assert data["download_url"] == "http://testserver/download/mock_report.pdf"


def test_run_endpoint_returns_clean_message_for_invalid_api_key(monkeypatch):
    """Authentication failures should be exposed as a clean 401 message."""

    def mock_run_agent(prompt, api_key):
        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        response = httpx.Response(status_code=401, request=request)
        raise AuthenticationError("bad key", response=response, body=None)

    monkeypatch.setattr("app.run_agent", mock_run_agent)

    response = client.post(
        "/run",
        json={
            "prompt": "cancer prevention",
            "api_key": "sk-invalid",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid OpenAI API key."
