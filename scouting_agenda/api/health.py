"""
Health check and root endpoints.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from scouting_agenda.settings import get_config, get_output_dir
from scouting_agenda.utils.calendar import list_available_calendars

router = APIRouter()

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Serve embeddable Vue/Vuetify widget.
    """
    config = get_config()

    # Build calendar info for template
    calendar_configs = []
    for cal in config.get("calendars", []):
        # Get friendly display name
        display_names = {
            "welpen": "Welpen",
            "scouts": "Scouts",
            "explorers": "Explorers",
            "roverscouts": "Roverscouts",
            "stam": "Stam",
            "verhuur": "Verhuur",
            "groepsbreed": "🔒 Kaderleden",
        }

        cal_name = cal.get("name")
        password = cal.get("password", "")
        calendar_configs.append(
            {
                "name": cal_name,
                "display_name": display_names.get(cal_name, cal_name.capitalize()),
                "file": cal.get("output"),
                "visibility": cal.get("visibility", "all_details"),
                "sources": cal.get("sources", []),
                "protected": bool(password),
            }
        )

    return templates.TemplateResponse(
        "embed.html",
        {
            "request": request,
            "calendars": calendar_configs,
        },
    )


@router.get("/api/health")
async def health():
    """
    API health check endpoint.
    """
    calendars = list_available_calendars()
    config = get_config()
    output_dir = get_output_dir()

    configured_calendars = []
    for cal in config.get("calendars", []):
        configured_calendars.append(
            {
                "name": cal.get("name"),
                "file": cal.get("output"),
                "visibility": cal.get("visibility", "all_details"),
                "sources_count": len(cal.get("sources", [])),
            }
        )

    return JSONResponse(
        {
            "status": "ok",
            "message": "Scouting Calendar Server",
            "calendars": calendars,
            "configured": configured_calendars,
            "output_dir": str(output_dir.absolute()),
        }
    )
