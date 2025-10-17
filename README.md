# SciFetch: Autonomous Agent for Scientific Literature Retrieval

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![AI](https://img.shields.io/badge/AI-LangChain-blueviolet)
![Task](https://img.shields.io/badge/Task-Information_Retrieval-orange)
![Last Updated](https://img.shields.io/badge/Last%20Updated-June%202025-brightgreen)

**SciFetch** is an autonomous AI agent designed to search, synthesize, and generate scientific literature reports based on natural language prompts.

It leverages modern AI and web technologies—LangChain for autonomous reasoning, OpenAI for summarization, and academic APIs for up-to-date content retrieval. The final output is delivered as a styled, downloadable **PDF report**, accessible via a clean web interface.

>👉 Try it live at: [https://scifetch.vercel.app](https://scifetch.vercel.app)

---

## Author

Íñigo Rodríguez Sánchez  
AI & Data Engineer

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Scientific Domain Coverage](#scientific-domain-coverage)
- [Project Structure](#project-structure)
- [Backend Overview](#backend-overview)
- [Frontend Overview](#frontend-overview)
- [Tests & Coverage](#tests--coverage)
- [Installation](#installation)
- [Usage](#usage)
- [Future Work](#future-work)
- [Final Words](#final-words)

---

## Introduction

**SciFetch** is a full-stack autonomous system designed to assist researchers and professionals in exploring scientific literature efficiently through AI-powered summarization and presentation.

Born from the need to automate scientific information retrieval, SciFetch uses a multi-agent architecture to query multiple trusted academic APIs, extract relevant publications, and synthesize a human-readable report in PDF format.

It combines the reasoning capabilities of **LangChain agents**, the language generation power of **OpenAI models**, and a **web-friendly interface** built with **Next.js** to offer:

- Fast and structured access to scientific knowledge.
- Reliable summarization of complex topics from multiple sources.
- Ready-to-use, visually styled PDF reports.
- Deployment flexibility, with both API and browser access.

The platform serves both as a **research assistant** and as a **proof of concept** for combining autonomous agents, modern web development, and scientific APIs into an end-to-end application.


---

## Key Features

- **Autonomous Literature Agent:** Combines LangChain's ReAct planning with domain-specific tools to select the most relevant academic APIs for each query.
- **Multi-Source Scientific Retrieval:** Aggregates results from PubMed, arXiv, OpenAlex, EuropePMC, and CrossRef to ensure coverage and diversity.
- **LLM-Powered Summarization:** Synthesizes complex, multi-source information into a cohesive and accessible summary using OpenAI's GPT models.
- **Styled PDF Report Generation:** Outputs are delivered as downloadable, professionally formatted PDF documents using custom HTML templates and WeasyPrint.
- **Modern Web Interface:** Built with Next.js, the frontend allows users to submit research prompts and retrieve results directly from the browser.
- **Full Public Deployment:** The backend is deployed on Render and the frontend on Vercel, providing instant access at [https://scifetch.vercel.app](https://scifetch.vercel.app).
- **Graceful Failure Handling:** If one API fails or returns incomplete data, the agent continues processing with the remaining sources.
- **Secure API Usage:** Requires an OpenAI API key, securely transmitted and handled via environment variables.
- **Tested for Robustness:** Includes a high-coverage test suite using Pytest (89%) to ensure system reliability and future extensibility.

---
## Scientific Domain Coverage

SciFetch integrates multiple academic APIs, each specializing in different scientific domains. Understanding the scope of each can help formulate more effective prompts.

| API                                           | Covered Domains (Examples)                                                                               |
|-----------------------------------------------|----------------------------------------------------------------------------------------------------------|
| [**arXiv**](https://arxiv.org)                | Hard Sciences & CS: Artificial Intelligence, Physics, Mathematics, Computer Vision, Quantitative Finance |
| [**CrossRef**](https://www.crossref.org)      | General Metadata: Scientific articles from all disciplines including Arts, Law, and Engineering          |
| [**EuropePMC**](https://europepmc.org)        | Biomedical (Europe-focused): Pharmacology, Virology, Bioinformatics, Clinical Trials                     |
| [**OpenAlex**](https://openalex.org)          | Multidisciplinary: Education, Social Sciences, Computer Science, Psychology, Economics                   |
| [**PubMed**](https://pubmed.ncbi.nlm.nih.gov) | Biomedical & Life Sciences: Medicine, Genomics, Neuroscience, Public Health                              |
 
> 💡 **Prompt Tip:**  
> When querying SciFetch, focus on topics within **healthcare, AI, bioinformatics, computer science, or physics**, as these are well represented in the integrated repositories.  
> Niche fields (e.g., Art Theory, Theology) may return sparse or irrelevant results.

---

## Project Structure

```bash
sci-fetch/
├── agents/                    # Core agent logic
│   └── scientific_fetcher.py  # Main autonomous agent that orchestrates API tools
│
├── apis/                      # Scientific API integrations
│   ├── arXiv.py               # arXiv search client and LangChain tool
│   ├── CrossRef.py            # CrossRef metadata retriever
│   ├── EuropePMC.py           # Europe PMC API wrapper
│   ├── OpenAlex.py            # OpenAlex client with inverted abstract decoding
│   └── PubMed.py              # PubMed search and fetch logic
│
├── frontend/                  # Next.js frontend interface
│   ├── components/            # React components (InputForm, Footer, etc.)
│   ├── pages/                 # Application pages (index.tsx)
│   └── styles/                # Global styles and CSS
│
├── inputs/                    
│   └── prompts.txt            # Input prompts for test runs
│
├── outputs/                   # Generated summaries in Markdown format
│   └── input_prompt.pdf       # Example PDF output generated by the backend (one per input prompt)
│
├── templates/                 # HTML template used for styled PDF rendering
│   └── report_template.html   # Jinja2-compatible PDF export layout
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
│   ├── config.py              # Environment variable loader and backend settings
│   ├── logs_config.py         # Color-coded logging setup
│   └── name_sanitizer.py      # PDF filename sanitization utility
│
├── .env.example               # Template for environment variables
├── .gitignore                 # Files and folders to ignore in Git
├── app.py                     # FastAPI entrypoint for running the agent via HTTP
├── Procfile                   # Deployment instruction for Render using Uvicorn
├── pytest.ini                 # Pytest configuration (warnings, env setup, etc.)
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

---

## Backend Overview

![Backend](https://img.shields.io/badge/Backend-FastAPI-teal)
![Hosted on Render](https://img.shields.io/badge/Hosted--on-Render-indigo)


The backend is developed with FastAPI, providing an HTTP interface to the LangChain-powered agent. It processes user prompts, orchestrates API calls, and generates the final PDF report. The application is deployed on Render, exposing a /run endpoint that receives the input, executes the agent, and returns the path to the generated report.

| Script / Module                  | Description                                                                                                                            |
|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `agents/scientific_fetcher.py`   | Main agent script that takes a user prompt, queries academic APIs, summarizes findings using GPT-4o, and saves the output to Markdown. |
| `apis/arXiv.py`                  | Interface for querying the arXiv API and extracting metadata. Includes LangChain-compatible tool wrapper.                              |
| `apis/CrossRef.py`               | Retrieves publication metadata from CrossRef. Cleans and filters fields like DOI, title, abstract, and date.                           |
| `apis/EuropePMC.py`              | Connects to the Europe PMC API and returns structured article metadata. LangChain-ready.                                               |
| `apis/OpenAlex.py`               | Queries OpenAlex API and decodes abstracts from inverted index format. Provides unified metadata output.                               |
| `apis/PubMed.py`                 | Uses PubMed's E-utilities to search and fetch publication metadata. Parses XML response into structured JSON.                          |
| `templates/report_template.html` | Jinja2 HTML template used to generate styled PDF reports with article summaries and metadata.                                          |
| `utils/config.py	`               | Environment variable and path configuration management for both local and deployed environments.                                       |
| `utils/logs_config.py`           | Centralized logging configuration with color-coded output for different log levels.                                                    |
| `utils/name_sanitizer.py	`       | Utility for sanitizing prompt strings into safe filenames for saving and downloading reports.                                          |

---

## Frontend Overview

![Next.js](https://img.shields.io/badge/Frontend-Next.js-darkblue)
![Hosted on Vercel](https://img.shields.io/badge/Hosted--on-Vercel-black)

The frontend is built with Next.js, providing a clean web interface where users can submit prompts, view the response in styled Markdown, and download the result as a PDF. It is deployed on Vercel and connected to the FastAPI backend.

| File                                     | Description                                                             |
|------------------------------------------|-------------------------------------------------------------------------|
| `frontend/components/InputForm.tsx`      | Prompt input form component with button handlers and download logic.    |
| `frontend/components/MarkdownViewer.tsx` | Displays the Markdown-formatted response from the backend.              |
| `frontend/components/Footer.tsx`         | Footer with author credits and project links.                           |
| `frontend/pages/index.tsx`               | Main entry point. Hosts the input form, API logic, and renders results. |
| `frontend/styles/globals.css`            | Global CSS styles for layout, typography, and markdown formatting.      |

---

## Tests & Coverage

![Coverage](https://img.shields.io/badge/Coverage-89%25-brightgreen)
![Tested](https://img.shields.io/badge/Tested-Pytest-blue)

SciFetch includes a robust test suite to ensure stability, API correctness, and agent reliability across its components.

All core modules and external API clients are covered by unit and integration tests using `pytest` and `pytest-cov`.

| Test File                          | Description                                                                 |
|------------------------------------|-----------------------------------------------------------------------------|
| `tests/test_app.py`                | Tests the FastAPI /run endpoint with a mocked run_agent.                    |
| `tests/test_arxiv.py`              | Verifies that ArxivClient and ArxivTool return valid responses.             |
| `tests/test_crossref.py`           | Tests CrossRefClient's date extraction, abstract cleaning, and tool output. |
| `tests/test_europepmc.py`          | Checks metadata extraction from EuropePMC API via client and tool.          |
| `tests/test_openalex.py`           | Tests abstract decoding logic and tool results for OpenAlex.                |
| `tests/test_pubmed.py`             | Validates PubMed ID search, metadata parsing, and tool integration.         |
| `tests/test_scientific_fetcher.py` | Covers run_agent() integration and article relevance extraction logic.      |


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

These tests give confidence that core modules behave reliably under various scenarios and inputs. High coverage ensures robustness across future updates.

---

## Installation

To run SciFetch locally, follow these steps:

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/sci-fetch.git
cd sci-fetch
```

2. (Optional but recommended) Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install required Python packages:
```bash
pip install -r requirements.txt
```

4. Add your OpenAI key on the .env file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

> Note: The application currently runs locally only and is not deployed as a public API or web service.

---

## Usage

You can use SciFetch in **two ways**:

### 1. Use the Web App (recommended)

Access the live web application here:
> https://scifetch.vercel.app

- Enter your research prompt and OpenAI API key.
- The agent will run automatically, fetch and summarize scientific articles, and display the results. 
- You can preview the generated content and download a styled PDF report.

### 2. Run Locally via CLI or API (advanced)

#### Option A: Run the agent via CLI

Launch the agent script and enter your prompt interactively:

```bash
python agents/scientific_fetcher.py
```

You'll be prompted to enter your research query. A PDF file will be saved locally in the outputs/ folder.

#### Option B: Run the FastAPI server

You can expose the agent functionality via a local REST API:
```bash
uvicorn app:app --reload
```

Then access the interactive documentation (API) at:
```bash
http://127.0.0.1:8000/docs
```

Send a POST request to /run endpoint with the following JSON:
```json
{
  "prompt": "Applications of self-supervised learning in genomics",
  "api_key": "your_openai_api_key_here"
}
```

The server will return:
```json
{
  "html_preview": "<...>",
  "download_url": "/outputs/your_report.pdf"
}
```

The api_key is required in every request and must be a valid OpenAI key.

---

## Future Work

Although SciFetch is functional and publicly accessible, there are several directions for future enhancement:

- **LLM Self-Evaluation:** Implement article scoring or ranking based on relevance confidence.
- **Advanced PDF Formatting:** Enhance visual formatting with typographic refinements, tables, or charts.
- **API Usage Monitoring:** Track rate limits, quota consumption, and per-tool fallback metrics.
- **Multilingual Summarization:** Allow output generation in languages other than English.
- **Tool Expansion:** Add support for new academic APIs (e.g., Semantic Scholar, CORE, IEEE Xplore).
- **Offline LLM Compatibility:** Explore use of local open-source models (e.g., Mistral, LLaMA) for air-gapped environments.

---

## Final Words

SciFetch is a small but ambitious project, built to help researchers and engineers accelerate the information gathering process.   
It is an evolving tool, open for experimentation, extension, or integration into larger pipelines or interfaces.

Feel free to explore, extend, or integrate it into your own applications. Contributions, feedback, or improvements are always welcome.

**If you’ve found this project useful or inspiring — feel free to build on it, break it, or just drop a star 🌟.**

