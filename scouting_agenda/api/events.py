"""
Events API endpoint for calendar data.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from icalendar import Calendar

from scouting_agenda.settings import get_config, get_output_dir
from scouting_agenda.utils.calendar import validate_password

router = APIRouter()


@router.get("/api/events/{calendar_name}")
async def get_events(
    calendar_name: str,
    key: str = Query(None, description="Password for protected calendars"),
):
    """
    Get calendar events as JSON for Vue/Vuetify calendar component.
    """
    config = get_config()
    output_dir = get_output_dir()

    # Find calendar config
    cal_config = None
    for cal in config.get("calendars", []):
        if cal.get("name") == calendar_name:
            cal_config = cal
            break

    if not cal_config:
        raise HTTPException(status_code=404, detail="Calendar not found")

    # Check password if required
    password = cal_config.get("password", "")
    if password and not validate_password(cal_config, key):
        raise HTTPException(status_code=403, detail="Invalid password")

    # Read ICS file
    ics_file = output_dir / cal_config.get("output")
    if not ics_file.exists():
        raise HTTPException(status_code=404, detail="Calendar file not found")

    try:
        with open(ics_file, "rb") as f:
            cal = Calendar.from_ical(f.read())

        events = []
        for component in cal.walk():
            if component.name == "VEVENT":
                # Extract event data
                event = {
                    "title": str(component.get("summary", "Geen titel")),
                    "start": component.get("dtstart").dt.isoformat()
                    if component.get("dtstart")
                    else None,
                    "end": component.get("dtend").dt.isoformat()
                    if component.get("dtend")
                    else None,
                }

                # Add optional fields
                if component.get("description"):
                    event["description"] = str(component.get("description"))
                if component.get("location"):
                    event["location"] = str(component.get("location"))
                if component.get("url"):
                    event["url"] = str(component.get("url"))

                events.append(event)

        return JSONResponse({"calendar": calendar_name, "events": events})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading calendar: {str(e)}") from e
