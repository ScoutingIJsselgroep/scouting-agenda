"""
Calendar event visibility filtering.
"""

import hashlib
import logging

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
    if visibility == VisibilityLevel.ALL_DETAILS:
        # Keep everything, just add source marker and optional emoji
        event["X-SOURCE-CALENDAR"] = source_name
        if source_emoji:
            original_summary = _norm_text(event.get("SUMMARY", "Event"))
            event["SUMMARY"] = f"{source_emoji} {original_summary}"
        return event

    # Create filtered event with essential fields
    filtered = Event()

    # Always keep these fields
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

    if visibility == VisibilityLevel.TITLE_ONLY:
        # Show title and basic time info only
        original_summary = _norm_text(event.get("SUMMARY", "Event"))

        # Build summary with optional emoji and source name
        if source_emoji:
            summary_parts = (
                [source_emoji, source_name, original_summary]
                if original_summary != "Event"
                else [source_emoji, source_name]
            )
        else:
            summary_parts = (
                [source_name, original_summary] if original_summary != "Event" else [source_name]
            )

        filtered["SUMMARY"] = (
            ": ".join(summary_parts) if len(summary_parts) > 1 else summary_parts[0]
        )

        # Keep transparency
        if "TRANSP" in event:
            filtered["TRANSP"] = event["TRANSP"]

        # Mark as private to hint clients
        filtered["CLASS"] = "PUBLIC"
        filtered["X-SOURCE-CALENDAR"] = source_name

    elif visibility == VisibilityLevel.BUSY_ONLY:
        # Only show busy/free status
        busy_text = f"{source_emoji} Bezet" if source_emoji else "Bezet"
        filtered["SUMMARY"] = busy_text
        filtered["TRANSP"] = "OPAQUE"  # Mark as busy
        filtered["CLASS"] = "PRIVATE"
        filtered["X-SOURCE-CALENDAR"] = source_name

    return filtered
