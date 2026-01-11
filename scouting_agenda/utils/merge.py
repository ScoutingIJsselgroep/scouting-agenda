"""
Calendar merging and deduplication logic.
"""

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from icalendar import Calendar, Event, vText

from scouting_agenda.utils.visibility import apply_visibility_filter

logger = logging.getLogger(__name__)


def _norm_text(v) -> str:
    """Normalize text value to string."""
    if v is None:
        return ""
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, vText):
        return str(v)
    return str(v)


def event_key(ev: Event) -> str:
    """
    Generate deduplication key for event.
    Prefers UID, falls back to hash of summary+dtstart.

    Args:
        ev: Event to generate key for

    Returns:
        Unique key string
    """
    uid = _norm_text(ev.get("UID")).strip()
    if uid:
        return f"uid:{uid}"

    summary = _norm_text(ev.get("SUMMARY")).strip()
    loc = _norm_text(ev.get("LOCATION")).strip()
    dtstart = ev.get("DTSTART")
    dtend = ev.get("DTEND")

    raw = f"{summary}|{loc}|{dtstart}|{dtend}".encode("utf-8", errors="replace")
    h = hashlib.sha256(raw).hexdigest()[:24]
    return f"hash:{h}"


def merge_calendars(
    sources: list[tuple[str, str | None, str, Calendar]],
    visibility: str,
    metadata: dict[str, Any],
) -> Calendar:
    """
    Merge multiple calendars into one with visibility filtering.

    Args:
        sources: List of (source_name, source_emoji, source_url, calendar) tuples
        visibility: Visibility level to apply
        metadata: Calendar metadata (name, description, timezone)

    Returns:
        Merged calendar with deduplicated events
    """
    merged = Calendar()
    merged.add("PRODID", "-//Scouting Agenda Merger//NL")
    merged.add("VERSION", "2.0")
    merged.add("CALSCALE", "GREGORIAN")
    merged.add("METHOD", "PUBLISH")

    # Apply metadata
    cal_name = metadata.get("cal_name", "Merged Calendar")
    merged.add("X-WR-CALNAME", cal_name)
    merged.add("NAME", cal_name)

    if "description" in metadata:
        merged.add("X-WR-CALDESC", metadata["description"])

    if "timezone" in metadata:
        merged.add("X-WR-TIMEZONE", metadata["timezone"])

    merged.add("X-GENERATED-AT", datetime.now(UTC).isoformat())

    # Merge events with deduplication
    seen = set()
    count_in = 0
    count_out = 0

    for source_name, source_emoji, _source_url, cal in sources:
        emoji_text = f" {source_emoji}" if source_emoji else ""
        logger.info(f"Processing source: {source_name}{emoji_text}")

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            count_in += 1
            key = event_key(component)

            if key in seen:
                logger.debug(f"Skipping duplicate event: {key}")
                continue

            seen.add(key)

            # Apply visibility filtering with optional emoji
            filtered_event = apply_visibility_filter(
                component, visibility, source_name, source_emoji
            )
            merged.add_component(filtered_event)
            count_out += 1

    logger.info(f"Merged {count_out} events from {count_in} total (deduplicated)")
    return merged
