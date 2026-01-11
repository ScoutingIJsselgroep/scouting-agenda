#!/usr/bin/env python3
"""
Calendar ICS merger with configurable visibility.

Reads config.yaml and generates merged ICS files with privacy filtering.
Designed to run as a cron job for periodic sync.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml
from icalendar import Calendar, Event, vText

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VisibilityLevel:
    """Visibility filtering levels for calendar events."""

    TITLE_ONLY = "title_only"
    BUSY_ONLY = "busy_only"
    ALL_DETAILS = "all_details"


class SecretYamlLoader(yaml.SafeLoader):
    """Custom YAML loader that supports !secret tag like Home Assistant."""

    pass


def secret_constructor(loader: yaml.Loader, node: yaml.Node) -> str:
    """
    Constructor for !secret tag.
    Loads value from secrets.yaml file.
    """
    secret_key = loader.construct_scalar(node)

    # Load secrets file
    secrets_path = Path("secrets.yaml")
    if not secrets_path.exists():
        raise FileNotFoundError(f"secrets.yaml not found. Create it with key: {secret_key}")

    with open(secrets_path, encoding="utf-8") as f:
        secrets = yaml.safe_load(f)

    if secret_key not in secrets:
        raise KeyError(f"Secret '{secret_key}' not found in secrets.yaml")

    return secrets[secret_key]


# Register the !secret constructor
yaml.add_constructor("!secret", secret_constructor, SecretYamlLoader)


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """Load and validate configuration from YAML file."""
    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.load(f, Loader=SecretYamlLoader)

        if not config or "calendars" not in config:
            raise ValueError("Config must contain 'calendars' key") from None

        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config: {e}")
        sys.exit(1)


def fetch_ics(url: str, timeout_s: int = 20) -> bytes:
    """Fetch ICS content from URL with error handling."""
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


def to_calendar(blob: bytes) -> Calendar:
    """Parse ICS blob to Calendar object."""
    try:
        return Calendar.from_ical(blob)
    except Exception as e:
        raise ValueError(f"Could not parse ICS: {e}") from e


def apply_visibility_filter(
    event: Event, visibility: str, source_name: str, source_emoji: str = None
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


def merge_calendars(
    sources: list[tuple[str, str, str, Calendar]], visibility: str, metadata: dict[str, Any]
) -> Calendar:
    """
    Merge multiple calendars into one with visibility filtering.

    Args:
        sources: List of (source_name, source_emoji, source_url, calendar) tuples
        visibility: Visibility level to apply
        metadata: Calendar metadata (name, description, timezone)

    Returns:
        Merged calendar
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
        logger.info(f"Processing source: {source_name}{' ' + source_emoji if source_emoji else ''}")
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


def write_atomic(path: str, data: bytes) -> None:
    """Write file atomically using tmp + rename."""
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    logger.info(f"✓ Written: {path}")


def sync_calendar(cal_config: dict[str, Any], base_config: dict[str, Any]) -> None:
    """
    Sync a single calendar configuration.

    Args:
        cal_config: Calendar configuration from YAML
        base_config: Global configuration (for timeout, output_dir, etc)
    """
    name = cal_config.get("name", "unknown")
    output_file = cal_config.get("output", f"{name}.ics")
    visibility = cal_config.get("visibility", VisibilityLevel.ALL_DETAILS)
    sources = cal_config.get("sources", [])
    metadata = cal_config.get("metadata", {})

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Syncing calendar: {name}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Visibility: {visibility}")
    logger.info(f"Sources: {len(sources)}")
    logger.info(f"{'=' * 60}")

    if not sources:
        logger.warning(f"No sources configured for {name}, skipping")
        return

    # Get global settings
    timeout = base_config.get("sync", {}).get("timeout_seconds", 20)
    output_dir = Path(base_config.get("server", {}).get("output_dir", "./output"))

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch all sources
    fetched_sources: list[tuple[str, str, str, Calendar]] = []

    for source in sources:
        source_name = source.get("name", "Unknown")
        source_url = source.get("url")
        source_emoji = source.get("emoji")  # Optional emoji

        if not source_url:
            logger.warning(f"Source {source_name} has no URL, skipping")
            continue

        try:
            blob = fetch_ics(source_url, timeout_s=timeout)
            cal = to_calendar(blob)
            fetched_sources.append((source_name, source_emoji, source_url, cal))
        except Exception as e:
            logger.error(f"Failed to fetch {source_name}: {e}")
            # Continue with other sources

    if not fetched_sources:
        logger.error(f"No sources could be fetched for {name}")
        return

    # Merge calendars
    try:
        merged = merge_calendars(fetched_sources, visibility, metadata)

        # Write output
        output_path = output_dir / output_file
        write_atomic(str(output_path), merged.to_ical())

        logger.info(f"✓ Successfully synced {name}")

    except Exception as e:
        logger.error(f"Failed to merge/write {name}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Sync and merge iCal calendars based on config.yaml"
    )
    parser.add_argument(
        "--config", default="config.yaml", help="Path to config file (default: config.yaml)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--calendar", help="Only sync specific calendar (by name)")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Load configuration
    config = load_config(args.config)

    # Sync each calendar
    calendars = config.get("calendars", [])

    if args.calendar:
        calendars = [c for c in calendars if c.get("name") == args.calendar]
        if not calendars:
            logger.error(f"Calendar '{args.calendar}' not found in config")
            sys.exit(1)

    success_count = 0
    fail_count = 0

    for cal_config in calendars:
        try:
            sync_calendar(cal_config, config)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to sync {cal_config.get('name')}: {e}")
            fail_count += 1

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Sync complete: {success_count} succeeded, {fail_count} failed")
    logger.info(f"{'=' * 60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
