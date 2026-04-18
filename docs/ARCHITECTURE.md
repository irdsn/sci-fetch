# SciFetch Architecture

## Project Structure

```bash
sci-fetch/
├── agents/                    # Core retrieval and report orchestration logic
│   └── scientific_fetcher.py  # Main pipeline for search, ranking, summary, and PDF generation
│
├── apis/                      # Scientific API integrations
│   ├── arXiv.py               # arXiv search client and tool wrapper
│   ├── CrossRef.py            # CrossRef metadata retriever
│   ├── EuropePMC.py           # Europe PMC API wrapper
│   ├── OpenAlex.py            # OpenAlex client with inverted abstract decoding
│   └── PubMed.py              # PubMed search and fetch logic
│
├── docs/                      # Extended technical documentation
│   ├── images/                # Images used in project documentation
│   │   └── SciFetch_logo.png  # Project logo used in docs
│   └── ARCHITECTURE.md        # Detailed repository structure and technical overview
│
├── frontend/                  # Next.js frontend interface
│   ├── components/            # React components (InputForm, Footer, etc.)
│   ├── pages/                 # Application pages (index.tsx)
│   └── styles/                # Global styles and CSS
│
├── inputs/
│   └── prompts.txt            # Input prompts for test runs
│
├── outputs/                   # Generated PDF outputs during local development
│   └── *.pdf                  # Generated report artifacts
│
├── prompt-engineering/        # Prompt templates used by the backend
│   ├── system_prompt.txt
│   └── user_prompt.txt
│
├── templates/                 # HTML template used for preview and PDF rendering
│   └── report_template.html   # Jinja2-compatible report layout
│
├── tests/                     # Pytest test suite (unit + integration)
│   ├── test_app.py
│   ├── test_arxiv.py
│   ├── test_crossref.py
│   ├── test_europepmc.py
│   ├── test_openalex.py
│   ├── test_pubmed.py
│   └── test_scientific_fetcher.py
│
├── utils/                     # Utilities and helper modules
│   ├── config.py              # Environment variable loader and output directory resolution
│   ├── logs_config.py         # Color-coded logging setup
│   └── name_sanitizer.py      # PDF filename sanitization utility
│
├── .env.example               # Template for environment variables
├── .gitignore                 # Files and folders to ignore in Git
├── app.py                     # FastAPI entrypoint for running the pipeline via HTTP
├── Procfile                   # Deployment instruction for Render using Uvicorn
├── pytest.ini                 # Pytest configuration
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## Backend Overview

![Backend](https://img.shields.io/badge/Backend-FastAPI-teal)
![Hosted on Render](https://img.shields.io/badge/Hosted--on-Render-indigo)

The backend is developed with FastAPI, providing an HTTP interface to the SciFetch pipeline. It processes user prompts, orchestrates API calls, renders the report preview, and generates the final PDF report. The application is deployed on Render, exposing a `/run` endpoint that receives the input, executes the pipeline, and returns preview and download information.

| Script / Module                  | Description                                                                                                                                 |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `agents/scientific_fetcher.py`   | Main pipeline that takes a user prompt, queries academic APIs, ranks and summarizes findings using GPT-4o, renders HTML, and generates PDF output. |
| `apis/arXiv.py`                  | Interface for querying the arXiv API and extracting metadata. Includes tool-compatible wrapper logic.                                      |
| `apis/CrossRef.py`               | Retrieves publication metadata from CrossRef. Cleans and filters fields like DOI, title, abstract, and date.                              |
| `apis/EuropePMC.py`              | Connects to the Europe PMC API and returns structured article metadata.                                                                     |
| `apis/OpenAlex.py`               | Queries OpenAlex API and decodes abstracts from inverted index format. Provides unified metadata output.                                   |
| `apis/PubMed.py`                 | Uses PubMed E-utilities to search and fetch publication metadata. Parses XML responses into structured output.                             |
| `templates/report_template.html` | Jinja2 HTML template used to generate the report preview and serve as the source for the final PDF rendering.                              |
| `utils/config.py`                | Environment variable and output-path configuration management for both local and deployed environments.                                     |
| `utils/logs_config.py`           | Centralized logging configuration with color-coded output for different log levels.                                                         |
| `utils/name_sanitizer.py`        | Utility for sanitizing prompt strings into safe filenames for saving and downloading reports.                                              |

## Frontend Overview

![Next.js](https://img.shields.io/badge/Frontend-Next.js-darkblue)
![Hosted on Vercel](https://img.shields.io/badge/Hosted--on-Vercel-black)

The frontend is built with Next.js, providing a clean web interface where users can submit prompts, inspect the generated report preview, and download the result as a PDF. It is deployed on Vercel and connected to the FastAPI backend.

| File                                     | Description                                                                 |
|------------------------------------------|-----------------------------------------------------------------------------|
| `frontend/components/InputForm.tsx`      | Prompt input form component with button states and request submission logic. |
| `frontend/components/MarkdownViewer.tsx` | Displays the collapsible report preview returned by the backend and exposes the PDF download action. |
| `frontend/components/Footer.tsx`         | Footer with author credits and project links.                               |
| `frontend/pages/index.tsx`               | Main entry point. Hosts the input form, API logic, and renders results.     |
| `frontend/styles/globals.css`            | Global CSS styles for layout, typography, and application theming.          |

## Tests & Coverage

![Coverage](https://img.shields.io/badge/Coverage-89%25-brightgreen)
![Tested](https://img.shields.io/badge/Tested-Pytest-blue)

SciFetch includes a robust test suite to ensure stability, API correctness, and pipeline reliability across its components.

All core modules and external API clients are covered by unit and integration tests using `pytest` and `pytest-cov`.

| Test File                          | Description                                                                 |
|------------------------------------|-----------------------------------------------------------------------------|
| `tests/test_app.py`                | Tests the FastAPI `/run` endpoint with a mocked `run_agent`.                |
| `tests/test_arxiv.py`              | Verifies that `ArxivClient` and `ArxivTool` return valid responses.         |
| `tests/test_crossref.py`           | Tests `CrossRefClient` date extraction, abstract cleaning, and tool output. |
| `tests/test_europepmc.py`          | Checks metadata extraction from Europe PMC via client and tool.             |
| `tests/test_openalex.py`           | Tests abstract decoding logic and tool results for OpenAlex.                |
| `tests/test_pubmed.py`             | Validates PubMed ID search, metadata parsing, and tool integration.         |
| `tests/test_scientific_fetcher.py` | Covers `run_agent()` integration, query generation, article ranking, and related helpers. |

Once the full suite is executed, the following results were obtained from the latest full test run on the main branch:

```bash
python -m pytest --cov=agents --cov=app --cov=apis tests/

<details>
======================================================= test session starts ========================================================
platform darwin -- Python 3.11.10, pytest-8.4.0, pluggy-1.6.0
plugins: anyio-4.9.0, cov-6.2.1, langsmith-0.3.38
collected 20 items

tests/test_app.py .                                                                                                          [  5%]
tests/test_arxiv.py ....                                                                                                     [ 25%]
tests/test_crossref.py ....                                                                                                  [ 45%]
tests/test_europepmc.py ...                                                                                                  [ 60%]
tests/test_openalex.py ...                                                                                                   [ 75%]
tests/test_pubmed.py ...                                                                                                     [ 90%]
tests/test_scientific_fetcher.py ..                                                                                          [100%]

========================================================== tests coverage ==========================================================
Name                           Stmts   Miss  Cover
--------------------------------------------------
agents/scientific_fetcher.py      64     10    84%
apis/CrossRef.py                  51      4    92%
apis/EuropePMC.py                 22      2    91%
apis/OpenAlex.py                  26      1    96%
apis/PubMed.py                    66      9    86%
apis/arXiv.py                     30      1    97%
app.py                            20      3    85%
--------------------------------------------------
TOTAL                            279     30    89%
</details>
```

These tests give confidence that core modules behave reliably under various scenarios and inputs. High coverage helps reduce avoidable regressions across future updates.
