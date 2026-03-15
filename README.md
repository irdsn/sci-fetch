# SciFetch: Autonomous Agent for Scientific Literature Retrieval

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![AI](https://img.shields.io/badge/AI-LangChain-blueviolet)
![Task](https://img.shields.io/badge/Task-Information_Retrieval-orange)
![Coverage](https://img.shields.io/badge/Coverage-89%25-brightgreen)
![Last Updated](https://img.shields.io/badge/Last%20Updated-March%202026-brightgreen)

**SciFetch** is an autonomous AI agent designed to search, synthesize, and generate scientific literature reports based on natural language prompts.

It leverages modern AI and web technologies—LangChain for autonomous reasoning, OpenAI for summarization, and academic APIs for up-to-date content retrieval. The final output is delivered as a styled, downloadable **PDF report**, accessible via a clean web interface.

>Try it live at: [https://scifetch.vercel.app](https://scifetch.vercel.app)

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Scientific Domain Coverage](#scientific-domain-coverage)
- [Installation](#installation)
- [Usage](#usage)
- [Future Work](#future-work)
- [Final Words](#final-words)

## Introduction

**SciFetch** is a full-stack autonomous system designed to assist researchers and professionals in exploring scientific literature efficiently through AI-powered summarization and presentation.

Born from the need to automate scientific information retrieval, SciFetch uses a multi-agent architecture to query multiple trusted academic APIs, extract relevant publications, and synthesize a human-readable report in PDF format.

It combines the reasoning capabilities of **LangChain agents**, the language generation power of **OpenAI models**, and a **web-friendly interface** built with **Next.js** to offer:

- Fast and structured access to scientific knowledge.
- Reliable summarization of complex topics from multiple sources.
- Ready-to-use, visually styled PDF reports.
- Deployment flexibility, with both API and browser access.

The platform serves both as a **research assistant** and as a **proof of concept** for combining autonomous agents, modern web development, and scientific APIs into an end-to-end application.

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

## Future Work

Although SciFetch is functional and publicly accessible, there are several directions for future enhancement:

- **LLM Self-Evaluation:** Implement article scoring or ranking based on relevance confidence.
- **Advanced PDF Formatting:** Enhance visual formatting with typographic refinements, tables, or charts.
- **API Usage Monitoring:** Track rate limits, quota consumption, and per-tool fallback metrics.
- **Multilingual Summarization:** Allow output generation in languages other than English.
- **Tool Expansion:** Add support for new academic APIs (e.g., Semantic Scholar, CORE, IEEE Xplore).
- **Offline LLM Compatibility:** Explore use of local open-source models (e.g., Mistral, LLaMA) for air-gapped environments.

## Contributing & Contact

SciFetch is a small but ambitious project, built to help researchers and engineers accelerate the information gathering process.  
It is an evolving tool, open for experimentation, extension, or integration into larger pipelines or interfaces.

**If you’ve found this project useful or inspiring — feel free to build on it, break it, or just drop a star 🌟.**

- Bugs / feature requests: please open an **Issue**.
- Direct contact: [inigo.rodsan@gmail.com](mailto:inigo.rodsan@gmail.com)

Developed & maintained by [Íñigo Rodríguez](https://github.com/irdsn).
