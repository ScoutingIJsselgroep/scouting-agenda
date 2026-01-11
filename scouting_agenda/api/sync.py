"""
Manual sync trigger endpoint.
"""

import logging
import subprocess

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/sync")
async def trigger_sync():
    """
    Manual sync trigger (for debugging).

    Note: In production, use cron job instead.
    This endpoint requires the sync script to be available.
    """
    try:
        # Use the sync command installed via project.scripts
        result = subprocess.run(
            ["sync"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        return JSONResponse(
            {
                "status": "completed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )

    except subprocess.TimeoutExpired:
        return JSONResponse(
            {"status": "timeout", "message": "Sync took too long (>120s)"}, status_code=500
        )

    except FileNotFoundError:
        return JSONResponse(
            {
                "status": "error",
                "message": "Sync command not found. Make sure the package is installed.",
            },
            status_code=500,
        )

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
