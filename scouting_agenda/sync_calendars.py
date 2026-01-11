#!/usr/bin/env python3
"""
Calendar ICS merger with configurable visibility.

Main entry point for calendar synchronization.
"""

import argparse
import logging
import sys

from scouting_agenda.sync import load_config, sync_calendar

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
