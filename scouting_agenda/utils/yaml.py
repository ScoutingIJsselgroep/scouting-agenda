"""
YAML utilities with !secret tag support (Home Assistant style).
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class SecretYamlLoader(yaml.SafeLoader):
    """Custom YAML loader that supports !secret tag like Home Assistant."""

    pass


def secret_constructor(loader: yaml.Loader, node: yaml.Node) -> str:
    """
    Constructor for !secret tag.
    Loads value from environment variable or secrets.yaml file.

    Priority:
    1. Environment variable (SECRET_<key_upper>)
    2. secrets.yaml file
    """
    secret_key = loader.construct_scalar(node)

    # Try environment variable first (convert key to uppercase with SECRET_ prefix)
    env_key = f"SECRET_{secret_key.upper()}"
    env_value = os.environ.get(env_key)
    if env_value is not None:
        logger.debug(f"Secret '{secret_key}' loaded from environment variable {env_key}")
        return env_value

    # Load secrets file
    secrets_path = Path("secrets.yaml")
    if not secrets_path.exists():
        logger.warning(
            f"secrets.yaml not found and no env var {env_key}, secret '{secret_key}' unavailable"
        )
        return f"!secret {secret_key}"

    try:
        with open(secrets_path, encoding="utf-8") as f:
            secrets = yaml.safe_load(f)

        if secret_key not in secrets:
            logger.warning(f"Secret '{secret_key}' not found in secrets.yaml or env var {env_key}")
            return f"!secret {secret_key}"

        return secrets[secret_key]
    except Exception as e:
        logger.warning(f"Error loading secret '{secret_key}': {e}")
        return f"!secret {secret_key}"


# Register the !secret constructor
yaml.add_constructor("!secret", secret_constructor, SecretYamlLoader)


def load_yaml_with_secrets(file_path: str) -> dict[str, Any]:
    """
    Load YAML file with !secret tag support.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML data with secrets resolved
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.load(f, Loader=SecretYamlLoader) or {}
    except Exception as e:
        logger.warning(f"Could not load {file_path}: {e}")
        return {}
