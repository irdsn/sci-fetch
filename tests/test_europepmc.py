from apis.EuropePMC import EuropePMCClient, EuropePMCTool


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_europepmc_client_returns_results(monkeypatch):
    """EuropePMCClient should map JSON responses into normalized metadata."""

    payload = {
        "resultList": {
            "result": [
                {
                    "title": "Europe PMC Paper",
                    "abstractText": "Biomedical abstract",
                    "doi": "10.1000/europepmc",
                    "source": "MED",
                    "id": "123456",
                    "firstPublicationDate": "2024-03-10",
                }
            ]
        }
    }

    monkeypatch.setattr(
        "apis.EuropePMC.requests.get",
        lambda url, params: FakeResponse(200, payload),
    )

    results = EuropePMCClient().search(query="bioinformatics", max_results=3)

    assert results == [
        {
            "title": "Europe PMC Paper",
            "abstract": "Biomedical abstract",
            "doi": "10.1000/europepmc",
            "source": "EuropePMC",
            "url": "https://europepmc.org/article/MED/123456",
            "publication_date": "2024-03-10",
        }
    ]


def test_europepmc_tool_call_consistency(monkeypatch):
    """EuropePMCTool should delegate to the client implementation."""

    monkeypatch.setattr(
        "apis.EuropePMC.EuropePMCClient.search",
        lambda self, query, max_results=10: [{"title": "Paper", "source": "EuropePMC"}],
    )

    results = EuropePMCTool()("bioinformatics")

    assert results == [{"title": "Paper", "source": "EuropePMC"}]
