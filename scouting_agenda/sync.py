"""
Calendar synchronization logic.
"""

import logging
import sys
from pathlib import Path
from typing import Any

from scouting_agenda.utils.file import write_atomic
from scouting_agenda.utils.ics import fetch_ics, parse_ics
from scouting_agenda.utils.merge import merge_calendars
from scouting_agenda.utils.visibility import VisibilityLevel
from scouting_agenda.utils.yaml import load_yaml_with_secrets

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Path to config YAML file

    Returns:
        Parsed configuration dictionary

    Raises:
        SystemExit: If config is invalid or missing
    """
    config = load_yaml_with_secrets(config_path)

    if not config or "calendars" not in config:
        logger.error("Config must contain 'calendars' key")
        sys.exit(1)

    return config


def sync_calendar(cal_config: dict[str, Any], base_config: dict[str, Any]) -> None:
    """
    Sync a single calendar configuration.

    Fetches all configured sources, merges them with visibility filtering,
    and writes the output ICS file.

    Args:
        cal_config: Calendar configuration from YAML
        base_config: Global configuration (for timeout, output_dir, etc)

    Raises:
        Exception: If merge or write fails
    """
    name = cal_config.get("name", "unknown")
    output_file = cal_config.get("output", f"{name}.ics")
    visibility = cal_config.get("visibility", VisibilityLevel.ALL_DETAILS)
    sources = cal_config.get("sources", [])
    metadata = cal_config.get("metadata", {})
    include_opties = cal_config.get("include_opties", False)  # Default: exclude [optie] events

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Syncing calendar: {name}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Visibility: {visibility}")
    logger.info(f"Include opties: {include_opties}")
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
    fetched_sources = []

    for source in sources:
        source_name = source.get("name", "Unknown")
        source_url = source.get("url")
        source_emoji = source.get("emoji")  # Optional emoji

        if not source_url:
            logger.warning(f"Source {source_name} has no URL, skipping")
            continue

        try:
            blob = fetch_ics(source_url, timeout_s=timeout)
            cal = parse_ics(blob)
            fetched_sources.append((source_name, source_emoji, source_url, cal))
        except Exception as e:
            logger.error(f"Failed to fetch {source_name}: {e}")
            # Continue with other sources

    if not fetched_sources:
        logger.error(f"No sources could be fetched for {name}")
        return

    # Merge calendars
    try:
        merged = merge_calendars(
            fetched_sources, visibility, metadata, calendar_name=name, include_opties=include_opties
        )

        # Write output
        output_path = output_dir / output_file
        write_atomic(str(output_path), merged.to_ical())

        logger.info(f"✓ Successfully synced {name}")

    except Exception as e:
        logger.error(f"Failed to merge/write {name}: {e}")
        raise
