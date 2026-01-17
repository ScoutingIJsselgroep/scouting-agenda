"""
Calendar event visibility filtering.
"""

import hashlib
import logging
import re

from icalendar import Event, vText

logger = logging.getLogger(__name__)


class VisibilityLevel:
    """Visibility filtering levels for calendar events."""

    TITLE_ONLY = "title_only"
    BUSY_ONLY = "busy_only"
    ALL_DETAILS = "all_details"


def _norm_text(v) -> str:
    """Normalize text value to string."""
    if v is None:
        return ""
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, vText):
        return str(v)
    return str(v)


def _build_summary(original_summary: str, source_name: str, source_emoji: str | None) -> str:
    """Build event summary with optional emoji and source name."""
    parts = [f"{source_emoji} {source_name}"] if source_emoji else [source_name]
    if original_summary and original_summary != "Event":
        parts.append(original_summary)
    return ": ".join(parts) if len(parts) > 1 else parts[0]


def _copy_essential_fields(event: Event, filtered: Event, source_name: str) -> None:
    """Copy essential fields and generate UID if missing."""
    essential_fields = ["UID", "DTSTART", "DTEND", "DTSTAMP", "CREATED", "LAST-MODIFIED"]
    for field in essential_fields:
        if field in event:
            filtered[field] = event[field]

    # Generate UID if missing
    if "UID" not in filtered:
        summary = _norm_text(event.get("SUMMARY", "event"))
        dtstart = event.get("DTSTART", "")
        uid_raw = f"{source_name}-{summary}-{dtstart}".encode()
        filtered["UID"] = hashlib.md5(uid_raw).hexdigest()


def apply_visibility_filter(
    event: Event, visibility: str, source_name: str, source_emoji: str | None = None
) -> Event:
    """
    Apply privacy filtering to event based on visibility level.

    Args:
        event: Original event
        visibility: One of VisibilityLevel values
        source_name: Name of source calendar (for labeling)
        source_emoji: Optional emoji to prefix to event title

    Returns:
        Filtered event
    """
    original_summary = _norm_text(event.get("SUMMARY", "Event"))

    if visibility == VisibilityLevel.ALL_DETAILS:
        event["SUMMARY"] = _build_summary(original_summary, source_name, source_emoji)
        event["X-SOURCE-CALENDAR"] = source_name
        return event

    # Create filtered event with essential fields
    filtered = Event()
    _copy_essential_fields(event, filtered, source_name)
    filtered["X-SOURCE-CALENDAR"] = source_name

    if visibility == VisibilityLevel.TITLE_ONLY:
        filtered["SUMMARY"] = _build_summary(original_summary, source_name, source_emoji)
        filtered["CLASS"] = "PUBLIC"
        if "TRANSP" in event:
            filtered["TRANSP"] = event["TRANSP"]

    elif visibility == VisibilityLevel.BUSY_ONLY:
        busy_text = f"{source_emoji} Bezet" if source_emoji else "Bezet"
        filtered["SUMMARY"] = busy_text
        filtered["TRANSP"] = "OPAQUE"
        filtered["CLASS"] = "PRIVATE"

    return filtered
