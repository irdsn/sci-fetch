##################################################################################################
#                                        SCIENTIFIC FETCHER                                      #
#                                                                                                #
# Scientific literature retrieval pipeline that queries multiple academic sources, aggregates     #
# results, synthesizes a summary with an OpenAI model, and renders an HTML/PDF report.           #
##################################################################################################

##################################################################################################
#                                            IMPORTS                                             #
##################################################################################################

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, Iterable, List
import unicodedata
from uuid import uuid4
from xml.sax.saxutils import escape

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apis.CrossRef import CrossRefTool
from apis.EuropePMC import EuropePMCTool
from apis.OpenAlex import OpenAlexTool
from apis.PubMed import PubMedTool
from apis.arXiv import ArxivTool
from utils.config import OUTPUT_DIR
from utils.logs_config import logger
from utils.name_sanitizer import slugify_filename

##################################################################################################
#                                        CONFIGURATION                                           #
##################################################################################################

load_dotenv()

SOURCE_TOOLS = [ArxivTool, PubMedTool, OpenAlexTool, EuropePMCTool, CrossRefTool]
SUMMARY_ARTICLE_LIMIT = 25
_LAST_REPORT_CONTEXT: Dict[str, Any] = {}
PROMPT_ENGINEERING_DIR = Path(__file__).resolve().parent.parent / "prompt-engineering"
SYSTEM_PROMPT_PATH = PROMPT_ENGINEERING_DIR / "system_prompt.txt"
USER_PROMPT_PATH = PROMPT_ENGINEERING_DIR / "user_prompt.txt"
MAX_SEARCH_QUERY_VARIANTS = 3
QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "con",
    "de",
    "del",
    "el",
    "en",
    "for",
    "in",
    "la",
    "las",
    "los",
    "of",
    "on",
    "or",
    "para",
    "por",
    "sobre",
    "the",
    "to",
    "un",
    "una",
    "y",
}
QUERY_TRANSLATION_GLOSSARY = {
    "procesamiento de lenguaje natural": "natural language processing",
    "lenguaje natural": "natural language",
    "analisis de sentimientos": "sentiment analysis",
    "análisis de sentimientos": "sentiment analysis",
    "mineria de opiniones": "opinion mining",
    "minería de opiniones": "opinion mining",
    "texto politico": "political text",
    "textos politicos": "political texts",
    "texto político": "political text",
    "textos políticos": "political texts",
    "discurso politico": "political discourse",
    "discurso político": "political discourse",
    "politica": "politics",
    "política": "politics",
    "politico": "political",
    "políticos": "political",
    "politico": "political",
    "sentimientos": "sentiment",
}

##################################################################################################
#                                        IMPLEMENTATION                                          #
##################################################################################################


def extract_relevant_articles(summary: str, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filters and returns the subset of articles whose titles are explicitly mentioned."""

    matched_titles = []
    for article in articles:
        title = article.get("title", "").lower()
        for line in summary.split("\n"):
            if title and title in line.lower():
                matched_titles.append(article)
                break
    return matched_titles


def _normalize_text(value: Any) -> str:
    """Normalizes optional metadata fields to strings."""

    if value is None:
        return ""
    text = str(value).replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)
    return text.strip()


def _normalize_query_text(value: str) -> str:
    """Normalizes user input into a search-friendly lowercase ASCII string."""

    text = unicodedata.normalize("NFKD", _normalize_text(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _translate_query_terms(normalized_query: str) -> str:
    """Applies a lightweight Spanish-to-English glossary for scientific search terms."""

    translated_query = normalized_query
    for source_text, target_text in sorted(QUERY_TRANSLATION_GLOSSARY.items(), key=lambda item: len(item[0]), reverse=True):
        translated_query = re.sub(
            rf"\b{re.escape(_normalize_query_text(source_text))}\b",
            target_text,
            translated_query,
        )
    return re.sub(r"\s+", " ", translated_query).strip()


def _stem_query_token(token: str) -> str:
    """Applies a lightweight stemmer to improve lexical matching across variants."""

    for suffix in ("ingly", "edly", "ing", "edly", "edly", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]
    return token


def _extract_query_terms(value: str) -> List[str]:
    """Extracts ranked content terms from a normalized query string."""

    terms = []
    for token in _normalize_query_text(value).split():
        if len(token) < 3 or token in QUERY_STOPWORDS:
            continue
        stemmed = _stem_query_token(token)
        if stemmed not in terms:
            terms.append(stemmed)
    return terms


def build_search_queries(user_input: str) -> List[str]:
    """Builds source-friendly query variants from the original user input."""

    original_query = _normalize_text(user_input)
    normalized_query = _normalize_query_text(user_input)
    translated_query = _translate_query_terms(normalized_query)
    keyword_query = " ".join(_extract_query_terms(translated_query)[:10])

    query_candidates = [original_query]
    if translated_query and translated_query != normalized_query:
        query_candidates.append(translated_query)
    if keyword_query and keyword_query not in query_candidates:
        query_candidates.append(keyword_query)

    deduplicated_queries = []
    seen = set()
    for query in query_candidates:
        compact_query = query.strip()
        normalized_candidate = _normalize_query_text(compact_query)
        if not compact_query or normalized_candidate in seen:
            continue
        seen.add(normalized_candidate)
        deduplicated_queries.append(compact_query)
    return deduplicated_queries[:MAX_SEARCH_QUERY_VARIANTS]


def _article_identity(article: Dict[str, Any]) -> str:
    """Builds a stable identity to deduplicate cross-source results."""

    doi = _normalize_text(article.get("doi")).lower()
    if doi:
        return f"doi:{doi}"

    url = _normalize_text(article.get("url")).lower()
    if url:
        return f"url:{url}"

    title = _normalize_text(article.get("title")).lower()
    source = _normalize_text(article.get("source")).lower()
    return f"title:{title}|source:{source}"


def _clean_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures all expected metadata fields exist with string values."""

    return {
        "title": _normalize_text(article.get("title")),
        "abstract": _normalize_text(article.get("abstract")),
        "doi": _normalize_text(article.get("doi")),
        "source": _normalize_text(article.get("source")),
        "url": _normalize_text(article.get("url")),
        "publication_date": _normalize_text(article.get("publication_date")),
    }


def _deduplicate_articles(articles: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicates articles while preserving first-seen order."""

    deduplicated = []
    seen = set()
    for article in articles:
        cleaned = _clean_article(article)
        identity = _article_identity(cleaned)
        if identity in seen:
            continue
        seen.add(identity)
        deduplicated.append(cleaned)
    return deduplicated


def _read_prompt_template(path: Path) -> str:
    """Loads a prompt template from disk and validates it is not empty."""

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Prompt template is empty: {path}")
    return content


def _format_article_context(articles: List[Dict[str, Any]]) -> str:
    """Formats retrieved articles into a compact LLM-readable context block."""

    article_lines = []
    for article in articles[:SUMMARY_ARTICLE_LIMIT]:
        title = article.get("title", "Untitled article")
        abstract = article.get("abstract", "")
        source = article.get("source", "Unknown source")
        publication_date = article.get("publication_date", "Unknown date")
        article_lines.append(
            (
                f"- Title: {title}\n"
                f"  Source: {source}\n"
                f"  Date: {publication_date}\n"
                f"  Abstract: {abstract[:750]}"
            )
        )
    return "\n".join(article_lines)


def _score_article_relevance(user_input: str, article: Dict[str, Any]) -> float:
    """Computes a lexical relevance score between the user input and an article."""

    translated_query = _translate_query_terms(_normalize_query_text(user_input))
    query_terms = _extract_query_terms(translated_query)
    if not query_terms:
        return 0.0

    title_text = _normalize_query_text(article.get("title", ""))
    abstract_text = _normalize_query_text(article.get("abstract", ""))
    combined_text = f"{title_text} {abstract_text}".strip()
    title_terms = set(_extract_query_terms(title_text))
    abstract_terms = set(_extract_query_terms(abstract_text))

    score = 0.0
    for term in query_terms:
        if term in title_terms:
            score += 3.0
        elif term in abstract_terms:
            score += 1.2

    for phrase in (translated_query, " ".join(query_terms[:4])):
        compact_phrase = phrase.strip()
        if len(compact_phrase) < 8:
            continue
        if compact_phrase in title_text:
            score += 5.0
        elif compact_phrase in combined_text:
            score += 2.5

    return score


def rank_articles_by_relevance(user_input: str, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ranks deduplicated articles by topical relevance and publication date."""

    scored_articles = []
    for article in articles:
        score = _score_article_relevance(user_input, article)
        scored_articles.append((score, article.get("publication_date", ""), article))

    if any(score > 0 for score, _, _ in scored_articles):
        scored_articles = [item for item in scored_articles if item[0] > 0]

    scored_articles.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [article for _, _, article in scored_articles]


def _fetch_articles_from_tool(tool_cls, query: str) -> List[Dict[str, Any]]:
    """Executes one source tool and returns normalized article dictionaries."""

    tool = tool_cls()
    source_name = getattr(tool, "name", tool_cls.__name__)
    try:
        logger.info(f"Launching retrieval from {source_name}...")
        results = tool(query)
        if not isinstance(results, list):
            logger.warning(f"{source_name} returned unexpected data; skipping source.")
            return []
        return [_clean_article(article) for article in results if isinstance(article, dict)]
    except Exception as exc:
        logger.warning(f"{source_name} failed during retrieval: {exc}")
        return []


def collect_articles(user_input: str) -> List[Dict[str, Any]]:
    """Collects articles from all configured sources in parallel and deduplicates them."""

    search_queries = build_search_queries(user_input)
    collected_articles: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(SOURCE_TOOLS) * len(search_queries)) as executor:
        futures = [
            executor.submit(_fetch_articles_from_tool, tool_cls, search_query)
            for tool_cls in SOURCE_TOOLS
            for search_query in search_queries
        ]
        for future in as_completed(futures):
            collected_articles.extend(future.result())

    articles = _deduplicate_articles(collected_articles)
    return rank_articles_by_relevance(user_input, articles)


def build_summary_messages(user_input: str, articles: List[Dict[str, Any]]) -> List[Any]:
    """Builds the LLM message payload used to synthesize the final report summary."""

    system_prompt = _read_prompt_template(SYSTEM_PROMPT_PATH)
    user_prompt_template = _read_prompt_template(USER_PROMPT_PATH)
    user_prompt = user_prompt_template.format(user_input=user_input)
    article_context = _format_article_context(articles)

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"{user_prompt}\n\nRetrieved articles:\n{article_context}"),
    ]


def render_report_html(user_input: str, summary: str, articles: List[Dict[str, Any]]) -> str:
    """Renders the report template to HTML."""

    generation_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    summary_html = markdown(
        summary,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
    )
    template = environment.get_template("report_template.html")
    return template.render(
        prompt=user_input,
        summary=summary,
        summary_html=summary_html,
        articles=articles,
        generation_date=generation_date,
        source_count=len(SOURCE_TOOLS),
    )


def _plain_text(value: str) -> str:
    """Normalizes rich text into a PDF-safe plain text representation."""

    text = re.sub(r"\*\*(.*?)\*\*", r"\1", value or "")
    text = text.replace("\r", "")
    text = text.replace("\x00", "")
    return text.strip()


def _pdf_paragraphs(text: str, style: ParagraphStyle) -> List[Paragraph]:
    """Converts plain text blocks into PDF-safe paragraphs."""

    blocks = [line.strip() for line in _plain_text(text).split("\n") if line.strip()]
    return [Paragraph(escape(block), style) for block in blocks]


def _find_chromium_executable() -> Path | None:
    """Returns a local Chromium/Chrome executable if available."""

    configured_path = os.getenv("SCIFETCH_CHROMIUM_PATH", "").strip()
    if configured_path:
        configured_candidate = Path(configured_path)
        if configured_candidate.exists():
            return configured_candidate

    playwright_roots = []
    configured_playwright_root = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if configured_playwright_root:
        playwright_roots.append(Path(configured_playwright_root))

    playwright_roots.extend(
        [
            Path.home() / ".cache" / "ms-playwright",
            Path.home() / "AppData" / "Local" / "ms-playwright",
            Path("/opt/render/project/.cache/ms-playwright"),
        ]
    )

    playwright_candidates: List[Path] = []
    for root in playwright_roots:
        if not root.exists():
            continue
        for chromium_dir in sorted(root.glob("chromium-*"), reverse=True):
            playwright_candidates.extend(
                [
                    chromium_dir / "chrome-linux" / "chrome",
                    chromium_dir / "chrome-linux" / "headless_shell",
                    chromium_dir / "chrome-win" / "chrome.exe",
                    chromium_dir / "chrome-win64" / "chrome.exe",
                ]
            )

    candidates = [
        *playwright_candidates,
        Path(os.getenv("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.getenv("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.getenv("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.getenv("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.getenv("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    for command_name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        resolved = shutil.which(command_name)
        if resolved:
            return Path(resolved)
    return None


def _draw_pdf_frame(canvas, document) -> None:
    """Draws a light SciFetch-inspired frame on every page."""

    width, height = A4
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#f6fafb"))
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#0f766e"))
    canvas.rect(16 * mm, height - 13 * mm, width - 32 * mm, 1.6 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#d8a11e"))
    canvas.rect(width - 52 * mm, height - 13 * mm, 36 * mm, 1.6 * mm, stroke=0, fill=1)

    canvas.setFillColor(colors.HexColor("#102032"))
    canvas.setFont("Helvetica-Bold", 11.5)
    canvas.drawString(16 * mm, height - 18 * mm, "SciFetch")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5d7286"))
    canvas.drawString(16 * mm, height - 22 * mm, "Scientific intelligence workspace")
    canvas.drawRightString(width - 16 * mm, height - 18 * mm, "Research report")

    canvas.setStrokeColor(colors.HexColor("#d8e3ea"))
    canvas.setLineWidth(0.6)
    canvas.line(16 * mm, 12 * mm, width - 16 * mm, 12 * mm)
    canvas.setFillColor(colors.HexColor("#5d7286"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(16 * mm, 7.2 * mm, "Generated by SciFetch")
    canvas.drawRightString(width - 16 * mm, 7.2 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _draw_divider(width_mm: float = 170.0) -> Table:
    """Creates a soft divider line for article separation."""

    divider = Table([[""]], colWidths=[width_mm * mm])
    divider.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 0.6, colors.HexColor("#d7e2ea")),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return divider


def write_pdf_report(rendered_html: str, output_path: Path) -> None:
    """
    Generates the main PDF report with a high-fidelity HTML renderer.

    The HTML argument is kept for compatibility with tests and existing callers.
    """

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chrome_executable = _find_chromium_executable()
    if chrome_executable:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as handle:
            handle.write(rendered_html)
            html_path = Path(handle.name)

        try:
            chromium_arguments = [
                str(chrome_executable),
                "--headless=new",
                "--disable-gpu",
                "--allow-file-access-from-files",
                "--run-all-compositor-stages-before-draw",
                f"--print-to-pdf={str(output_path)}",
                html_path.resolve().as_uri(),
            ]
            if os.name != "nt":
                chromium_arguments.insert(1, "--disable-dev-shm-usage")
                chromium_arguments.insert(1, "--no-sandbox")

            logger.info(f"Attempting Chromium PDF rendering with executable: {chrome_executable}")
            completed_process = subprocess.run(
                chromium_arguments,
                capture_output=True,
                text=True,
                timeout=int(os.getenv("SCIFETCH_PDF_RENDER_TIMEOUT_SECONDS", "90")),
            )
            if output_path.exists() and output_path.stat().st_size > 0:
                return
            logger.warning(
                "Chromium PDF rendering did not produce a file. returncode=%s stderr=%s",
                completed_process.returncode,
                completed_process.stderr.strip(),
            )
        except Exception as exc:
            logger.warning(f"Chromium PDF rendering failed: {exc}")
        finally:
            html_path.unlink(missing_ok=True)

    try:
        from weasyprint import HTML
    except Exception as exc:
        raise RuntimeError("No high-fidelity PDF renderer is available in this environment.") from exc

    logger.info("Falling back to WeasyPrint for PDF generation.")
    HTML(
        string=rendered_html,
        base_url=str(Path(__file__).resolve().parent.parent),
    ).write_pdf(str(output_path))

    if output_path.exists() and output_path.stat().st_size > 0:
        return

    raise RuntimeError("High-fidelity PDF rendering failed.")


def _build_report_payload(user_input: str, api_key: str) -> Dict[str, Any]:
    """Builds the report payload without generating the PDF artifact."""

    if not user_input.strip():
        raise ValueError("User input cannot be empty.")
    if not api_key.strip():
        raise ValueError("API key cannot be empty.")

    logger.info("Launching scientific literature retrieval pipeline...")

    articles = collect_articles(user_input)
    if not articles:
        raise RuntimeError("No scientific articles were retrieved from the configured sources.")

    llm = ChatOpenAI(
        temperature=0.2,
        model="gpt-4o",
        api_key=api_key,
    )

    summary_messages = build_summary_messages(user_input, articles)
    summary_response = llm.invoke(summary_messages)
    summary = _normalize_text(summary_response.content)

    relevant_articles = extract_relevant_articles(summary, articles)
    if relevant_articles:
        logger.info(f"Identified {len(relevant_articles)} explicitly referenced articles in the summary.")

    generation_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    rendered_html = render_report_html(user_input=user_input, summary=summary, articles=articles)
    report_id = uuid4().hex[:8]
    filename = f"{slugify_filename(user_input) or 'scifetch_report'}_{report_id}"
    pdf_output_path = OUTPUT_DIR / f"{filename}.pdf"

    _LAST_REPORT_CONTEXT.clear()
    _LAST_REPORT_CONTEXT.update(
        {
            "user_input": user_input,
            "summary": summary,
            "articles": articles,
            "generation_date": generation_date,
        }
    )

    return {
        "report_id": report_id,
        "summary": summary,
        "articles": articles,
        "html_preview": rendered_html,
        "filename": f"{filename}.pdf",
        "output_path": pdf_output_path,
    }


def generate_pdf_artifact(rendered_html: str, output_path: Path) -> Dict[str, Any]:
    """Generates the PDF artifact and returns the resulting output metadata."""

    pdf_warning = None
    output_file = None

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_pdf_report(rendered_html, output_path)
        output_file = str(output_path)
        logger.info(f"Scientific retrieval pipeline completed successfully: {output_path}")
    except Exception as exc:
        pdf_warning = f"PDF generation failed in this environment: {exc.__class__.__name__}"
        logger.exception("PDF generation failed.")

    return {
        "output_file": output_file,
        "pdf_warning": pdf_warning,
    }


def run_agent(user_input: str, api_key: str) -> Dict[str, Any]:
    """Runs the scientific retrieval pipeline end-to-end."""

    result = _build_report_payload(user_input, api_key)
    pdf_result = generate_pdf_artifact(result["html_preview"], result["output_path"])

    return {
        "report_id": result["report_id"],
        "summary": result["summary"],
        "articles": result["articles"],
        "html_preview": result["html_preview"],
        "filename": result["filename"],
        "output_file": pdf_result["output_file"],
        "pdf_warning": pdf_result["pdf_warning"],
    }


##################################################################################################
#                                               MAIN                                             #
##################################################################################################

if __name__ == "__main__":
    user_input = input("Provide your scientific research prompt: ")
    user_api_key = input("Provide your OpenAI API key: ")
    result = run_agent(user_input, user_api_key)
    print(f"\nOutput saved to: {result['output_file']}")
