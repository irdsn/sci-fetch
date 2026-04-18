from pathlib import Path

import pytest

from agents.scientific_fetcher import (
    build_summary_messages,
    build_search_queries,
    collect_articles,
    extract_relevant_articles,
    rank_articles_by_relevance,
    run_agent,
)


def test_collect_articles_deduplicates_and_ignores_source_failures(monkeypatch):
    """Collection should deduplicate overlapping results and tolerate per-source failures."""

    class ToolA:
        def __call__(self, query):
            return [
                {
                    "title": "Shared Paper",
                    "abstract": "A",
                    "doi": "10.1000/shared",
                    "source": "SourceA",
                    "url": "https://example.org/a",
                    "publication_date": "2024-01-01",
                }
            ]

    class ToolB:
        def __call__(self, query):
            return [
                {
                    "title": "Shared Paper Duplicate",
                    "abstract": "B",
                    "doi": "10.1000/shared",
                    "source": "SourceB",
                    "url": "https://example.org/b",
                    "publication_date": "2024-02-01",
                },
                {
                    "title": "Unique Paper",
                    "abstract": "C",
                    "doi": "",
                    "source": "SourceB",
                    "url": "https://example.org/unique",
                    "publication_date": "2024-03-01",
                },
            ]

    class ToolFail:
        def __call__(self, query):
            raise RuntimeError("temporary upstream failure")

    monkeypatch.setattr(
        "agents.scientific_fetcher.SOURCE_TOOLS",
        [ToolA, ToolB, ToolFail],
    )

    results = collect_articles("graph neural networks")

    assert len(results) == 2
    assert results[0]["title"] == "Unique Paper"
    assert any(article["doi"] == "10.1000/shared" for article in results)


def test_build_search_queries_translates_spanish_topic():
    """Search query generation should produce an English-friendly variant for Spanish topics."""

    queries = build_search_queries("Procesamiento de Lenguaje Natural para análisis de Sentimientos en textos políticos")

    assert queries
    assert any("natural language processing" in query.lower() for query in queries)
    assert any("sentiment analysis" in query.lower() for query in queries)


def test_rank_articles_by_relevance_prioritizes_topic_match():
    """Relevance ranking should beat recency when an article is clearly on-topic."""

    ranked = rank_articles_by_relevance(
        "Procesamiento de Lenguaje Natural para análisis de Sentimientos en textos políticos",
        [
            {
                "title": "Political institutions and fiscal decentralization",
                "abstract": "A public policy analysis with no NLP component.",
                "doi": "10.1000/irrelevant",
                "source": "CrossRef",
                "url": "https://example.org/irrelevant",
                "publication_date": "2025-01-01",
            },
            {
                "title": "Natural language processing for sentiment analysis in political texts",
                "abstract": "This study evaluates transformer models for political discourse classification.",
                "doi": "10.1000/relevant",
                "source": "OpenAlex",
                "url": "https://example.org/relevant",
                "publication_date": "2023-04-10",
            },
        ],
    )

    assert ranked[0]["doi"] == "10.1000/relevant"


def test_run_agent_returns_pdf_contract(monkeypatch, tmp_path):
    """run_agent should aggregate sources, summarize, render HTML, and persist a PDF path."""

    class FakeResponse:
        content = "Summary that references Shared Paper."

    class FakeLLM:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

        def invoke(self, messages):
            rendered_messages = "\n".join(message.content for message in messages)
            assert "Shared Paper" in rendered_messages
            assert "quantum computing" in rendered_messages
            return FakeResponse()

    monkeypatch.setattr(
        "agents.scientific_fetcher.collect_articles",
        lambda user_input: [
            {
                "title": "Shared Paper",
                "abstract": "Useful abstract",
                "doi": "10.1000/shared",
                "source": "PubMed",
                "url": "https://example.org/shared",
                "publication_date": "2024-01-01",
            }
        ],
    )
    monkeypatch.setattr("agents.scientific_fetcher.ChatOpenAI", FakeLLM)
    monkeypatch.setattr(
        "agents.scientific_fetcher.write_pdf_report",
        lambda rendered_html, output_path: Path(output_path).write_bytes(b"%PDF-1.4\n"),
    )
    monkeypatch.setattr("agents.scientific_fetcher.OUTPUT_DIR", tmp_path)

    result = run_agent("quantum computing", "sk-test-key")

    assert result["summary"] == "Summary that references Shared Paper."
    assert result["articles"][0]["title"] == "Shared Paper"
    assert result["html_preview"].startswith("<!DOCTYPE html>")
    assert result["output_file"].endswith(".pdf")
    assert Path(result["output_file"]).exists()


def test_run_agent_rejects_empty_inputs():
    """run_agent should fail fast on invalid empty inputs."""

    with pytest.raises(ValueError):
        run_agent("", "sk-test-key")

    with pytest.raises(ValueError):
        run_agent("valid prompt", "")


def test_build_summary_messages_loads_templates():
    """Prompt templates should be loaded and rendered with the user input."""

    messages = build_summary_messages(
        "cell therapy in oncology",
        [
            {
                "title": "CAR-T outcomes review",
                "abstract": "Review of major clinical outcomes.",
                "doi": "10.1000/cart",
                "source": "PubMed",
                "url": "https://example.org/cart",
                "publication_date": "2024-01-01",
            }
        ],
    )

    assert len(messages) == 2
    assert "SciFetch" in messages[0].content
    assert "cell therapy in oncology" in messages[1].content
    assert "Retrieved articles:" in messages[1].content


def test_extract_relevant_articles():
    """extract_relevant_articles should keep only titles mentioned in the summary."""

    summary = "The paper titled 'ABC Quantum' and 'XYZ Cryptography' are particularly relevant."
    articles = [
        {"title": "ABC Quantum", "abstract": "Quantum stuff", "doi": "abc/123", "url": "http://example.com/abc"},
        {"title": "XYZ Cryptography", "abstract": "Crypto stuff", "doi": "xyz/456", "url": "http://example.com/xyz"},
        {"title": "Unrelated Article", "abstract": "No relevance", "doi": "none/000", "url": "http://example.com/none"},
    ]

    relevant = extract_relevant_articles(summary, articles)

    assert len(relevant) == 2
    assert any(article["title"] == "ABC Quantum" for article in relevant)
    assert any(article["title"] == "XYZ Cryptography" for article in relevant)
