#!/usr/bin/env python3
"""
FastAPI server for serving generated ICS calendar files.

Main application that imports and registers all API endpoints.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from scouting_agenda.api import calendars, health, sync
from scouting_agenda.settings import initialize_settings, load_config
from scouting_agenda.utils.calendar import list_available_calendars

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    initialize_settings()
    logger.info("Server started")
    logger.info(f"Available calendars: {list_available_calendars()}")

    yield

    # Shutdown (if needed in the future)
    logger.info("Server shutting down")


# Initialize FastAPI with lifespan
app = FastAPI(
    title="Scouting Calendar Server",
    description="Serves merged iCal calendar files",
    version="1.0.0",
    lifespan=lifespan,
)


# Register routers
app.include_router(health.router, tags=["health"])
app.include_router(calendars.router, tags=["calendars"])
app.include_router(sync.router, tags=["sync"])


def run_server():
    """Start the FastAPI server."""
    # Load config to get host/port
    config = load_config()
    server_config = config.get("server", {})

    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run("scouting_agenda.server:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
