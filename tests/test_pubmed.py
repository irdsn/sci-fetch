from apis.PubMed import PubMedClient, PubMedTool


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


def test_pubmed_search_returns_ids(monkeypatch):
    """PubMed search should parse the returned identifier list."""

    def fake_get(url, params):
        return FakeResponse(200, {"esearchresult": {"idlist": ["1", "2", "3"]}})

    monkeypatch.setattr("apis.PubMed.requests.get", fake_get)

    ids = PubMedClient().search("cancer", max_results=3)

    assert ids == ["1", "2", "3"]


def test_pubmed_fetch_details_returns_articles(monkeypatch):
    """PubMed metadata fetch should normalize the XML payload into article dictionaries."""

    xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>12345</PMID>
          <Article>
            <ArticleTitle>Genome Study</ArticleTitle>
            <Abstract>
              <AbstractText>Important findings</AbstractText>
            </Abstract>
            <ArticleDate>
              <Year>2024</Year>
              <Month>05</Month>
              <Day>09</Day>
            </ArticleDate>
            <Journal>
              <JournalIssue>
                <PubDate>
                  <MedlineDate>2024 May 09</MedlineDate>
                </PubDate>
              </JournalIssue>
            </Journal>
          </Article>
        </MedlineCitation>
        <PubmedData>
          <ArticleIdList>
            <ArticleId IdType="doi">10.1000/genome</ArticleId>
          </ArticleIdList>
        </PubmedData>
        <ELocationID EIdType="doi">10.1000/genome</ELocationID>
      </PubmedArticle>
    </PubmedArticleSet>
    """

    def fake_get(url, params):
        return FakeResponse(200, text=xml_payload)

    monkeypatch.setattr("apis.PubMed.requests.get", fake_get)

    articles = PubMedClient().fetch_details(["12345"])

    assert articles == [
        {
            "title": "Genome Study",
            "abstract": "Important findings",
            "doi": "10.1000/genome",
            "source": "PubMed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345",
            "publication_date": "2024-05-09",
        }
    ]


def test_pubmed_tool_call_returns_valid_data(monkeypatch):
    """PubMedTool should compose search and fetch into the normalized contract."""

    monkeypatch.setattr("apis.PubMed.PubMedClient.search", lambda self, query, max_results=10: ["42"])
    monkeypatch.setattr(
        "apis.PubMed.PubMedClient.fetch_details",
        lambda self, ids: [{"title": "Paper", "source": "PubMed"}],
    )

    results = PubMedTool()("machine learning")

    assert results == [{"title": "Paper", "source": "PubMed"}]
