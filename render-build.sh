#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
pip install -r requirements.txt

# Install a deterministic Chromium runtime for Playwright-based PDF rendering.
PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.cache/ms-playwright python -m playwright install chromium
