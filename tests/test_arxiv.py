import pytest

from apis.arXiv import ArxivClient, ArxivTool


class FakeResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


def test_arxiv_client_returns_results(monkeypatch):
    """ArxivClient should parse XML responses into the normalized article contract."""

    xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <title>Quantum Paper</title>
        <summary>Quantum abstract</summary>
        <id>https://arxiv.org/abs/1234.5678</id>
        <published>2024-01-15T00:00:00Z</published>
        <arxiv:doi>10.1000/xyz</arxiv:doi>
      </entry>
    </feed>
    """

    def fake_get(url, params):
        return FakeResponse(200, xml_payload)

    monkeypatch.setattr("apis.arXiv.requests.get", fake_get)

    results = ArxivClient().search(query="quantum", max_results=3)

    assert results == [
        {
            "title": "Quantum Paper",
            "abstract": "Quantum abstract",
            "doi": "10.1000/xyz",
            "source": "arXiv",
            "url": "https://arxiv.org/abs/1234.5678",
            "publication_date": "2024-01-15",
        }
    ]


def test_arxiv_tool_call_matches_client(monkeypatch):
    """ArxivTool should delegate to ArxivClient consistently."""

    monkeypatch.setattr(
        "apis.arXiv.ArxivClient.search",
        lambda self, query, max_results=10: [{"title": "Paper", "source": "arXiv"}],
    )

    tool = ArxivTool()
    results_call = tool("neural networks")
    results_run = tool._run("neural networks")

    assert results_call == results_run
    assert results_call == [{"title": "Paper", "source": "arXiv"}]


def test_arxiv_tool_arun_not_implemented():
    """The async shim should remain explicitly unsupported."""

    tool = ArxivTool()
    with pytest.raises(NotImplementedError):
        tool._arun("any query")
