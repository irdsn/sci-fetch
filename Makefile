SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -Command

PYTHON := .\.venv\Scripts\python.exe
PYTEST := .\.venv\Scripts\pytest.exe
FRONTEND_DIR := frontend

.PHONY: help format lint test run-api run-front run

help:
	@Write-Host "Available targets:"
	@Write-Host "  make help       Show this help message"
	@Write-Host "  make format     Run available formatters"
	@Write-Host "  make lint       Run frontend lint and backend sanity checks"
	@Write-Host "  make test       Run backend test suite"
	@Write-Host "  make run-api    Start the FastAPI backend"
	@Write-Host "  make run-front  Start the Next.js frontend"
	@Write-Host "  make run        Show how to run backend and frontend together"

format:
	Set-Location $(FRONTEND_DIR); npm.cmd run format

lint:
	Set-Location $(FRONTEND_DIR); npm.cmd run lint
	$(PYTHON) -m compileall app.py agents apis utils tests

test:
	$(PYTEST) -q

run-api:
	$(PYTHON) -m uvicorn app:app --reload

run-front:
	Set-Location $(FRONTEND_DIR); npm.cmd run dev

run:
	@Write-Host "Run these commands in separate terminals:"
	@Write-Host "  make run-api"
	@Write-Host "  make run-front"
