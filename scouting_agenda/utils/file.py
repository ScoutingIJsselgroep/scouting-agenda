"""
File operation utilities.
"""

import logging
import os

logger = logging.getLogger(__name__)


def write_atomic(path: str, data: bytes) -> None:
    """
    Write file atomically using tmp + rename.

    This ensures that the file is never partially written if the process
    is interrupted.

    Args:
        path: Destination file path
        data: Data to write
    """
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    logger.info(f"✓ Written: {path}")
