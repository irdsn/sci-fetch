from apis.OpenAlex import OpenAlexClient, OpenAlexTool


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_openalex_client_returns_results(monkeypatch):
    """OpenAlexClient should decode the inverted abstract and return normalized metadata."""

    payload = {
        "results": [
            {
                "title": "OpenAlex Paper",
                "doi": "10.1000/openalex",
                "id": "https://openalex.org/W123",
                "publication_date": "2024-02-20",
                "abstract_inverted_index": {
                    "deep": [0],
                    "learning": [1],
                    "works": [2],
                },
            }
        ]
    }

    monkeypatch.setattr(
        "apis.OpenAlex.requests.get",
        lambda url, params: FakeResponse(200, payload),
    )

    results = OpenAlexClient().search("neural networks", max_results=3)

    assert results == [
        {
            "title": "OpenAlex Paper",
            "abstract": "deep learning works",
            "doi": "10.1000/openalex",
            "source": "OpenAlex",
            "url": "https://openalex.org/W123",
            "publication_date": "2024-02-20",
        }
    ]


def test_openalex_tool_call_consistency(monkeypatch):
    """OpenAlexTool should delegate to the client implementation."""

    monkeypatch.setattr(
        "apis.OpenAlex.OpenAlexClient.search",
        lambda self, query, max_results=10: [{"title": "Paper", "source": "OpenAlex"}],
    )

    results = OpenAlexTool()("machine learning")

    assert results == [{"title": "Paper", "source": "OpenAlex"}]


def test_decode_abstract_logic():
    """Abstract decoding should reconstruct the original word order."""

    client = OpenAlexClient()
    mock_item = {
        "abstract_inverted_index": {
            "deep": [0],
            "learning": [1],
            "models": [2],
            "are": [3],
            "powerful": [4],
        }
    }

    decoded = client.decode_abstract(mock_item)
    assert decoded == "deep learning models are powerful"
