from fastapi.testclient import TestClient
import httpx
from openai import AuthenticationError
from pathlib import Path

import app as app_module
from app import app

client = TestClient(app)


def test_run_endpoint_with_mock(monkeypatch):
    """The /run endpoint should return preview data and queue PDF generation."""

    captured = {}

    def mock_build_report_payload(prompt, api_key):
        captured["prompt"] = prompt
        captured["api_key"] = api_key
        return {
            "report_id": "report1234",
            "summary": "mock summary",
            "articles": [{"title": "Paper"}],
            "html_preview": "<html><body>Preview</body></html>",
            "filename": "mock_report.pdf",
            "output_path": Path("outputs/mock_report.pdf"),
        }

    def mock_generate_pdf_in_background(report_id, rendered_html, output_path):
        return None

    monkeypatch.setattr("app._build_report_payload", mock_build_report_payload)
    monkeypatch.setattr("app._generate_pdf_in_background", mock_generate_pdf_in_background)

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
    assert data["output_file"] is None
    assert data["html_preview"] == "<html><body>Preview</body></html>"
    assert data["download_url"] == "http://testserver/download/mock_report.pdf"
    assert data["status_url"] == "http://testserver/reports/report1234/status"
    assert data["pdf_status"] == "pending"


def test_run_endpoint_returns_clean_message_for_invalid_api_key(monkeypatch):
    """Authentication failures should be exposed as a clean 401 message."""

    def mock_build_report_payload(prompt, api_key):
        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        response = httpx.Response(status_code=401, request=request)
        raise AuthenticationError("bad key", response=response, body=None)

    monkeypatch.setattr("app._build_report_payload", mock_build_report_payload)

    response = client.post(
        "/run",
        json={
            "prompt": "cancer prevention",
            "api_key": "sk-invalid",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid OpenAI API key."


def test_report_status_endpoint_returns_ready_download(monkeypatch):
    """The status endpoint should expose a ready PDF artifact."""

    monkeypatch.setitem(
        app_module.REPORT_STATUS,
        "report1234",
        {
            "status": "ready",
            "output_file": str(Path("outputs/mock_report.pdf")),
            "pdf_warning": None,
        },
    )

    response = client.get("/reports/report1234/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["filename"] == "mock_report.pdf"
    assert data["download_url"] == "http://testserver/download/mock_report.pdf"
