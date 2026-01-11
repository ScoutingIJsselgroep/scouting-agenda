"""
Calendar utility functions.
"""

import secrets
from pathlib import Path
from typing import Any

from scouting_agenda.settings import get_config, get_output_dir


def list_available_calendars() -> list[str]:
    """List all ICS files in output directory."""
    output_dir = get_output_dir()
    if not output_dir.exists():
        return []

    return sorted([f.name for f in output_dir.glob("*.ics")])


def get_calendar_config(calendar_name: str) -> dict[str, Any] | None:
    """
    Get configuration for a specific calendar by filename.

    Args:
        calendar_name: Name of the ICS file (e.g., 'welpen.ics')

    Returns:
        Calendar configuration dict or None if not found
    """
    config = get_config()
    for cal in config.get("calendars", []):
        if cal.get("output") == calendar_name:
            return cal
    return None


def validate_password(calendar_config: dict[str, Any], provided_password: str | None) -> bool:
    """
    Validate password for a calendar if password protection is enabled.

    Args:
        calendar_config: Calendar configuration dict
        provided_password: Password provided by user

    Returns:
        True if password is valid or not required, False otherwise
    """
    required_password = calendar_config.get("password")

    # No password required
    if not required_password or required_password.startswith("!secret"):
        return True

    # Password required but none provided
    if not provided_password:
        return False

    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(required_password, provided_password)


def get_calendar_path(calendar_name: str) -> Path:
    """
    Get full path to calendar file.

    Args:
        calendar_name: Name of the ICS file

    Returns:
        Path object to the calendar file
    """
    output_dir = get_output_dir()
    return output_dir / calendar_name


def validate_calendar_path(calendar_path: Path) -> bool:
    """
    Validate calendar path to prevent directory traversal attacks.

    Args:
        calendar_path: Path to validate

    Returns:
        True if path is safe, False otherwise
    """
    output_dir = get_output_dir()
    try:
        resolved_path = calendar_path.resolve()
        resolved_output = output_dir.resolve()
        return str(resolved_path).startswith(str(resolved_output))
    except Exception:
        return False
