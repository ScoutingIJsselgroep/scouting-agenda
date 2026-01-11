"""
Configuration and settings management.
"""

import logging
from pathlib import Path
from typing import Any

from scouting_agenda.utils.yaml import load_yaml_with_secrets

logger = logging.getLogger(__name__)

# Global config (loaded on startup)
CONFIG: dict[str, Any] = {}
OUTPUT_DIR: Path = Path("./output")


def load_config(config_path: str = "config.yaml") -> dict[str, Any]:
    """Load configuration from YAML file with secrets support."""
    return load_yaml_with_secrets(config_path)


def initialize_settings(config_path: str = "config.yaml") -> None:
    """Initialize global settings from config file."""
    global CONFIG, OUTPUT_DIR

    CONFIG = load_config(config_path)

    # Get output directory from config
    output_dir_str = CONFIG.get("server", {}).get("output_dir", "./output")
    OUTPUT_DIR = Path(output_dir_str)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Settings initialized")
    logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")


def get_config() -> dict[str, Any]:
    """Get current configuration."""
    return CONFIG


def get_output_dir() -> Path:
    """Get output directory path."""
    return OUTPUT_DIR
