"""
Calendar file serving and listing endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from scouting_agenda.settings import get_config
from scouting_agenda.utils.calendar import (
    get_calendar_config,
    get_calendar_path,
    list_available_calendars,
    validate_calendar_path,
    validate_password,
)

router = APIRouter()


@router.get("/{calendar_name}")
async def get_calendar(calendar_name: str, password: str | None = Query(None, alias="key")):
    """
    Serve an ICS calendar file.

    Args:
        calendar_name: Name of the ICS file (e.g., 'welpen.ics')
        password: Optional password for protected calendars (query param: ?key=xxx)

    Returns:
        ICS file with proper content-type header
    """
    # Ensure filename ends with .ics
    if not calendar_name.endswith(".ics"):
        calendar_name = f"{calendar_name}.ics"

    file_path = get_calendar_path(calendar_name)

    # Security: prevent directory traversal
    if not validate_calendar_path(file_path):
        raise HTTPException(status_code=400, detail="Invalid calendar name")

    # Check if file exists
    if not file_path.exists():
        available = list_available_calendars()
        raise HTTPException(
            status_code=404, detail=f"Calendar '{calendar_name}' not found. Available: {available}"
        )

    # Check password if calendar is protected
    calendar_config = get_calendar_config(calendar_name)
    if calendar_config and not validate_password(calendar_config, password):
        raise HTTPException(
            status_code=401, detail="Password required. Add ?key=your_password to the URL"
        )

    # Return file with proper content-type
    return FileResponse(
        path=file_path,
        media_type="text/calendar; charset=utf-8",
        filename=calendar_name,
        headers={
            "Content-Disposition": f'inline; filename="{calendar_name}"',
            "Cache-Control": "no-cache, must-revalidate",
        },
    )


@router.get("/api/calendars")
async def list_calendars():
    """
    List all configured calendars with metadata.
    """
    config = get_config()
    calendars = []

    for cal in config.get("calendars", []):
        name = cal.get("name")
        output_file = cal.get("output")
        file_path = get_calendar_path(output_file)

        calendars.append(
            {
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
                "modified": file_path.stat().st_mtime if file_path.exists() else None,
            }
        )

    return JSONResponse({"calendars": calendars})
