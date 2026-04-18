import pytest

from apis.CrossRef import CrossRefClient, CrossRefTool, extract_crossref_date


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_extract_crossref_date_formats_parts():
    """CrossRef dates should be normalized from date-parts arrays."""

    date = extract_crossref_date(
        {"published-online": {"date-parts": [[2024, 6, 10]]}}
    )

    assert date == "2024-06-10"


def test_crossref_client_returns_results(monkeypatch):
    """CrossRefClient should clean abstracts and keep normalized metadata."""

    payload = {
        "message": {
            "items": [
                {
                    "title": ["CrossRef Paper"],
                    "abstract": "<jats:p>Useful abstract</jats:p>",
                    "DOI": "10.1000/crossref",
                    "published-online": {"date-parts": [[2024, 4, 1]]},
                }
            ]
        }
    }

    monkeypatch.setattr(
        "apis.CrossRef.requests.get",
        lambda url, params: FakeResponse(200, payload),
    )

    results = CrossRefClient().search(query="quantum computing", max_results=3)

    assert results == [
        {
            "title": "CrossRef Paper",
            "abstract": "Useful abstract",
            "doi": "10.1000/crossref",
            "source": "CrossRef",
            "url": "https://doi.org/10.1000/crossref",
            "publication_date": "2024-04-01",
        }
    ]


def test_crossref_tool_call_and_run_consistency(monkeypatch):
    """CrossRefTool sync entry points should remain consistent."""

    monkeypatch.setattr(
        "apis.CrossRef.CrossRefClient.search",
        lambda self, query, max_results=10: [{"title": "Paper", "source": "CrossRef"}],
    )

    tool = CrossRefTool()
    results_call = tool("deep learning")
    results_run = tool._run("deep learning")

    assert results_call == results_run
    assert results_call == [{"title": "Paper", "source": "CrossRef"}]


def test_crossref_tool_arun_not_implemented():
    """The async shim should remain unsupported."""

    tool = CrossRefTool()
    with pytest.raises(NotImplementedError):
        tool._arun("any query")
