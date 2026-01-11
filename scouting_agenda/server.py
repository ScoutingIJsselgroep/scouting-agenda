#!/usr/bin/env python3
"""
FastAPI server for serving generated ICS calendar files.

Serves ICS files from the output directory with proper content-type headers.
"""

import logging
from pathlib import Path
from typing import Dict, Any

import yaml
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Scouting Calendar Server",
    description="Serves merged iCal calendar files",
    version="1.0.0"
)

# Global config (loaded on startup)
CONFIG: Dict[str, Any] = {}
OUTPUT_DIR: Path = Path("./output")


class SecretYamlLoader(yaml.SafeLoader):
    """Custom YAML loader that supports !secret tag like Home Assistant."""
    pass

load(f, Loader=SecretYamlLoader
def secret_constructor(loader: yaml.Loader, node: yaml.Node) -> str:
    """
    Constructor for !secret tag.
    Loads value from secrets.yaml file.
    """
    secret_key = loader.construct_scalar(node)
    
    # Load secrets file
    secrets_path = Path("secrets.yaml")
    if not secrets_path.exists():
        # Graceful fallback for server (secrets only needed for sync)
        logger.warning(f"secrets.yaml not found, secret '{secret_key}' unavailable")
        return f"!secret {secret_key}"
    
    try:
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = yaml.safe_load(f)
        
        if secret_key not in secrets:
            logger.warning(f"Secret '{secret_key}' not found in secrets.yaml")
            return f"!secret {secret_key}"
        
        return secrets[secret_key]
    except Exception as e:
        logger.warning(f"Error loading secret '{secret_key}': {e}")
        return f"!secret {secret_key}"


# Register the !secret constructor
yaml.add_constructor('!secret', secret_constructor, SecretYamlLoader)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        return {}


@app.on_event("startup")
async def startup_event():
    """Load configuration on server startup."""
    global CONFIG, OUTPUT_DIR
    
    CONFIG = load_config()
    
    # Get output directory from config
    output_dir_str = CONFIG.get("server", {}).get("output_dir", "./output")
    OUTPUT_DIR = Path(output_dir_str)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Server started")
    logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")
    logger.info(f"Available calendars: {list_available_calendars()}")


def list_available_calendars() -> list[str]:
    """List all ICS files in output directory."""
    if not OUTPUT_DIR.exists():
        return []
    
    return sorted([f.name for f in OUTPUT_DIR.glob("*.ics")])


@app.get("/")
async def root():
    """
    Health check and list available calendars.
    """
    calendars = list_available_calendars()
    
    configured_calendars = []
    for cal in CONFIG.get("calendars", []):
        configured_calendars.append({
            "name": cal.get("name"),
            "file": cal.get("output"),
            "visibility": cal.get("visibility", "all_details"),
            "sources_count": len(cal.get("sources", []))
        })
    
    return JSONResponse({
        "status": "ok",
        "message": "Scouting Calendar Server",
        "calendars": calendars,
        "configured": configured_calendars,
        "output_dir": str(OUTPUT_DIR.absolute())
    })


@app.get("/{calendar_name}")
async def get_calendar(calendar_name: str):
    """
    Serve an ICS calendar file.
    
    Args:
        calendar_name: Name of the ICS file (e.g., 'verhuur.ics')
    
    Returns:
        ICS file with proper content-type header
    """
    # Ensure filename ends with .ics
    if not calendar_name.endswith(".ics"):
        calendar_name = f"{calendar_name}.ics"
    
    file_path = OUTPUT_DIR / calendar_name
    
    # Security: prevent directory traversal
    try:
        file_path = file_path.resolve()
        OUTPUT_DIR.resolve()
        
        if not str(file_path).startswith(str(OUTPUT_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Invalid calendar name")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid calendar name")
    
    # Check if file exists
    if not file_path.exists():
        available = list_available_calendars()
        raise HTTPException(
            status_code=404,
            detail=f"Calendar '{calendar_name}' not found. Available: {available}"
        )
    
    # Return file with proper content-type
    return FileResponse(
        path=file_path,
        media_type="text/calendar; charset=utf-8",
        filename=calendar_name,
        headers={
            "Content-Disposition": f'inline; filename="{calendar_name}"',
            "Cache-Control": "no-cache, must-revalidate",
        }
    )


@app.get("/api/sync")
async def trigger_sync():
    """
    Manual sync trigger (for debugging).
    
    Note: In production, use cron job instead.
    This endpoint requires sync_calendars to be importable.
    """
    try:
        # Import here to avoid requiring sync_calendars at server startup
        import subprocess
        import sys
        from pathlib import Path
        
        # Find the sync.py in the project root
        project_root = Path(__file__).parent.parent
        sync_script = project_root / "sync.py"
        
        result = subprocess.run(
            [sys.executable, str(sync_script)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_root)
        )
        
        return JSONResponse({
            "status": "completed" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        })
        
    except subprocess.TimeoutExpired:
        return JSONResponse({
            "status": "timeout",
            "message": "Sync took too long (>120s)"
        }, status_code=500)
    
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


@app.get("/api/calendars")
async def list_calendars():
    """
    List all configured calendars with metadata.
    """
    calendars = []
    
    for cal in CONFIG.get("calendars", []):
        name = cal.get("name")
        output_file = cal.get("output")
        file_path = OUTPUT_DIR / output_file
        
        calendars.append({
            "name": name,
            "file": output_file,
            "url": f"/{output_file}",
            "visibility": cal.get("visibility", "all_details"),
            "sources": [
                {"name": s.get("name"), "url": s.get("url")[:50] + "..."}
                for s in cal.get("sources", [])
            ],
            "exists": file_path.exists(),
            "size_bytes": file_path.stat().st_size if file_path.exists() else None,
            "modified": file_path.stat().st_mtime if file_path.exists() else None
        })
    
    return JSONResponse({"calendars": calendars})


def run_server():
    """Start the FastAPI server."""
    import uvicorn
    
    # Load config to get host/port
    config = load_config()
    server_config = config.get("server", {})
    
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "scouting_agenda.server:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
