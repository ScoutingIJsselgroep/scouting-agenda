"""
ICS calendar fetching and parsing utilities.
"""

import logging

import requests
from icalendar import Calendar

logger = logging.getLogger(__name__)


def fetch_ics(url: str, timeout_s: int = 20) -> bytes:
    """
    Fetch ICS content from URL with error handling.

    Args:
        url: URL to fetch ICS from
        timeout_s: Request timeout in seconds

    Returns:
        ICS content as bytes

    Raises:
        requests.RequestException: If fetch fails
        ValueError: If response is not valid ICS
    """
    try:
        logger.info(f"Fetching: {url[:60]}...")
        r = requests.get(
            url, timeout=timeout_s, headers={"User-Agent": "scouting-calendar-merger/1.0"}
        )
        r.raise_for_status()

        content_type = (r.headers.get("Content-Type") or "").lower()
        if "text/html" in content_type and b"BEGIN:VCALENDAR" not in r.content[:2000]:
            raise ValueError(f"URL returned HTML instead of ICS: {url}")

        logger.info(f"✓ Fetched {len(r.content)} bytes")
        return r.content

    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise


def parse_ics(blob: bytes) -> Calendar:
    """
    Parse ICS blob to Calendar object.

    Args:
        blob: ICS content as bytes

    Returns:
        Parsed Calendar object

    Raises:
        ValueError: If ICS cannot be parsed
    """
    try:
        return Calendar.from_ical(blob)
    except Exception as e:
        raise ValueError(f"Could not parse ICS: {e}") from e
