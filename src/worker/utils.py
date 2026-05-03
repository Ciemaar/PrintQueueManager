"""Utility functions for worker tasks."""

import logging
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def scan_local_directory(watch_path: Path) -> Iterable[dict[str, Any]]:
    """
    Scan the local directory recursively for 3D model files.

    Yields metadata for each discovered .stl or .3mf file, including
    handling for broken symlinks.
    """
    logger.debug(f"Scanning directory: {watch_path} recursively")
    for file_path in watch_path.rglob("*"):
        if (file_path.is_file() or file_path.is_symlink()) and file_path.suffix.lower() in {
            ".stl",
            ".3mf",
        }:
            is_broken_symlink = file_path.is_symlink() and not file_path.exists()

            # If the symlink is broken, we cannot stat() it directly.
            file_size = 0 if is_broken_symlink else file_path.stat().st_size

            yield {
                "name": file_path.name,
                "path": str(file_path),
                "size": file_size,
                "is_broken_symlink": is_broken_symlink,
            }
