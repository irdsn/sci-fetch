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
import urllib.parse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import APIStatusError, AuthenticationError
from pydantic import BaseModel

from agents.scientific_fetcher import run_agent
from utils.config import OUTPUT_DIR
from utils.name_sanitizer import slugify_filename

##################################################################################################
#                                        CONFIGURATION                                           #
##################################################################################################

logging.basicConfig(level=logging.INFO)

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


@app.post("/run")
def run_scifetch(request: PromptRequest, http_request: Request):
    """
    Executes the SciFetch pipeline using the provided prompt and request-scoped API key.
    """

    try:
        result = run_agent(request.prompt, request.api_key)
        logging.info("Agent result generated successfully.")

        output_path = result.get("output_file")
        filename = None
        download_url = None
        base_url = os.getenv("BASE_URL") or str(http_request.base_url).rstrip("/")

        if output_path:
            output_path = str(output_path)
            filename = os.path.basename(output_path)
            download_url = f"{base_url}/download/{filename}"

        return {
            "message": "SciFetch run completed.",
            "filename": filename,
            "download_url": download_url,
            "output_file": output_path,
            "html_preview": result.get("html_preview"),
            "pdf_warning": result.get("pdf_warning"),
        }

    except Exception as exc:
        logging.exception("Agent execution failed.")
        if isinstance(exc, AuthenticationError):
            raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
        if isinstance(exc, APIStatusError) and getattr(exc, "status_code", None) == 401:
            raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
        raise HTTPException(status_code=500, detail="SciFetch could not complete the request.")


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
