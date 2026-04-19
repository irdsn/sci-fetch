##################################################################################################
#                                        FASTAPI ENTRYPOINT                                      #
#                                                                                                #
# FastAPI entrypoint that exposes the SciFetch pipeline over HTTP and serves generated PDF files.#
##################################################################################################

##################################################################################################
#                                            IMPORTS                                             #
##################################################################################################

import logging
import os
from threading import Lock
import urllib.parse

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import APIStatusError, AuthenticationError
from pydantic import BaseModel

from agents.scientific_fetcher import _build_report_payload, generate_pdf_artifact, run_agent
from utils.config import OUTPUT_DIR
from utils.name_sanitizer import slugify_filename

##################################################################################################
#                                        CONFIGURATION                                           #
##################################################################################################

logging.basicConfig(level=logging.INFO)
REPORT_STATUS_LOCK = Lock()
REPORT_STATUS: dict[str, dict[str, str | None]] = {}

##################################################################################################
#                                     FASTAPI INITIALIZATION                                     #
##################################################################################################

app = FastAPI(
    title="SciFetch API",
    description=(
        "SciFetch is an autonomous retrieval pipeline that queries academic APIs, "
        "synthesizes findings, and generates an HTML preview plus an optional PDF report."
    ),
    version="1.0.0",
)

##################################################################################################
#                                             CORS                                               #
##################################################################################################

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://scifetch.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##################################################################################################
#                                         REQUEST MODEL                                          #
##################################################################################################


class PromptRequest(BaseModel):
    """Request schema for the /run endpoint."""

    prompt: str
    api_key: str


##################################################################################################
#                                           ENDPOINTS                                            #
##################################################################################################


def _set_report_status(report_id: str, status: str, output_file: str | None = None, pdf_warning: str | None = None) -> None:
    """Updates the in-memory report status registry."""

    with REPORT_STATUS_LOCK:
        REPORT_STATUS[report_id] = {
            "status": status,
            "output_file": output_file,
            "pdf_warning": pdf_warning,
        }


def _generate_pdf_in_background(report_id: str, rendered_html: str, output_path) -> None:
    """Generates the PDF artifact and updates report status asynchronously."""

    pdf_result = generate_pdf_artifact(rendered_html, output_path)
    if pdf_result["output_file"]:
        _set_report_status(report_id, "ready", pdf_result["output_file"], pdf_result["pdf_warning"])
        return
    _set_report_status(report_id, "failed", pdf_result["output_file"], pdf_result["pdf_warning"])


@app.post("/run")
def run_scifetch(request: PromptRequest, http_request: Request, background_tasks: BackgroundTasks):
    """
    Executes the SciFetch pipeline using the provided prompt and request-scoped API key.
    """

    try:
        result = _build_report_payload(request.prompt, request.api_key)
        logging.info("Agent result generated successfully.")

        base_url = os.getenv("BASE_URL") or str(http_request.base_url).rstrip("/")
        report_id = str(result["report_id"])
        filename = str(result["filename"])
        download_url = f"{base_url}/download/{filename}"
        status_url = f"{base_url}/reports/{report_id}/status"

        _set_report_status(report_id, "pending")
        background_tasks.add_task(
            _generate_pdf_in_background,
            report_id,
            result["html_preview"],
            result["output_path"],
        )

        return {
            "message": "SciFetch run completed.",
            "report_id": report_id,
            "filename": filename,
            "download_url": download_url,
            "output_file": None,
            "html_preview": result.get("html_preview"),
            "pdf_warning": None,
            "pdf_status": "pending",
            "status_url": status_url,
        }

    except Exception as exc:
        logging.exception("Agent execution failed.")
        if isinstance(exc, AuthenticationError):
            raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
        if isinstance(exc, APIStatusError) and getattr(exc, "status_code", None) == 401:
            raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
        raise HTTPException(status_code=500, detail="SciFetch could not complete the request.")


@app.get("/reports/{report_id}/status", summary="Get PDF generation status")
def get_report_status(report_id: str, http_request: Request):
    """Returns the current PDF generation status for a report."""

    with REPORT_STATUS_LOCK:
        report_status = REPORT_STATUS.get(report_id)

    if not report_status:
        raise HTTPException(status_code=404, detail="Requested report was not found.")

    base_url = os.getenv("BASE_URL") or str(http_request.base_url).rstrip("/")
    output_file = report_status.get("output_file")
    filename = os.path.basename(str(output_file)) if output_file else None
    download_url = f"{base_url}/download/{filename}" if filename else None

    return {
        "report_id": report_id,
        "status": report_status["status"],
        "filename": filename,
        "download_url": download_url,
        "output_file": output_file,
        "pdf_warning": report_status["pdf_warning"],
    }


@app.get("/download/{filename}", summary="Download PDF report")
def download_file(filename: str):
    """Downloads a previously generated PDF report."""

    sanitized_name = slugify_filename(filename).replace(".pdf", "") + ".pdf"
    file_path = OUTPUT_DIR / sanitized_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file not found.")

    encoded_filename = urllib.parse.quote(sanitized_name)
    content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"

    return FileResponse(
        path=file_path,
        filename=sanitized_name,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition},
    )


##################################################################################################
#                                        ROOT ENDPOINT                                           #
##################################################################################################


@app.get("/")
def read_root():
    """Returns a small health-style response."""

    return {"message": "SciFetch API is up and running!"}
