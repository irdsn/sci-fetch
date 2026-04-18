##################################################################################################
#                                        OVERVIEW                                                #
#                                                                                                #
# This module defines shared configuration variables for the project.                            #
# It includes the default output directory used to save reports, logs, and images.               #
# Designed to centralize paths and simplify reuse across CLI and FastAPI components.             #
##################################################################################################

##################################################################################################
#                                            IMPORTS                                             #
##################################################################################################

import os
from pathlib import Path
import tempfile

##################################################################################################
#                                        CONFIGURATION                                           #
##################################################################################################

def _is_render_environment() -> bool:
    """Returns whether the application is running on Render."""

    return os.getenv("RENDER", "").lower() in {"1", "true", "yes"}


def _resolve_output_dir() -> Path:
    """Resolves the report output directory for the current runtime environment."""

    configured_output_dir = os.getenv("SCIFETCH_OUTPUT_DIR", "").strip()
    if configured_output_dir:
        return Path(configured_output_dir)

    if _is_render_environment():
        return Path("/tmp") / "scifetch_outputs"

    return Path(tempfile.gettempdir()) / "scifetch_outputs"


OUTPUT_DIR = _resolve_output_dir()

# Ensure the directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
