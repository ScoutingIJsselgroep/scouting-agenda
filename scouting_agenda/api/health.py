"""
Health check and root endpoints.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from scouting_agenda.settings import get_config, get_output_dir
from scouting_agenda.utils.calendar import list_available_calendars

router = APIRouter()


@router.get("/")
async def root():
    """
    Health check and list available calendars.
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
