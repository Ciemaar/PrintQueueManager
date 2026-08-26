import hashlib
import logging
import os
from pathlib import Path
from typing import Any, cast

import trimesh

from src.app.config import settings

logger = logging.getLogger(__name__)

THUMBNAILS_DIR = Path(settings.thumbnails_dir)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)


def _start_xvfb() -> None:
    """Start Xvfb if not already running for headless rendering."""
    # Check if a display is already set and available
    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":99"
        # We try to launch Xvfb in the background. If it fails (e.g., already running),
        # it's usually fine because the display is already active.
        # Note: os.system runs synchronously, so we run it in background with &
        cmd = "Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset >/dev/null 2>&1 &"
        os.system(cmd)


def generate_thumbnail(
    file_path: Path, thumbnail_path: Path, resolution: tuple[int, int] | None = None
) -> bool:
    """
    Generate a thumbnail for a given 3D file (.stl, .3mf) using trimesh.

    Returns True if successful, False otherwise.
    """
    if resolution is None:
        resolution = (400, 400)

    _start_xvfb()

    try:
        # Load the mesh
        logger.debug(f"Loading mesh for thumbnail generation: {file_path}")
        mesh = trimesh.load(str(file_path))

        # If it's a scene (like from some 3mf files), dump to a single mesh
        if type(mesh).__name__ == "Scene":
            mesh = cast(Any, mesh).dump(concatenate=True)

        scene = trimesh.Scene(mesh)

        logger.debug("Rendering scene...")
        png_data = scene.save_image(resolution=resolution)

        with open(thumbnail_path, "wb") as f:
            f.write(png_data)

        logger.info(f"Successfully generated thumbnail: {thumbnail_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {file_path}: {e}")
        return False


def get_thumbnail_path(file_path: Path) -> str:
    """Get the expected thumbnail path relative to static dir."""
    file_hash = hashlib.md5(str(file_path).encode(), usedforsecurity=False).hexdigest()
    return f"/static/thumbnails/{file_hash}.png"


def get_thumbnail_file_path(file_path: Path) -> Path:
    """Get the expected thumbnail path on the file system."""
    file_hash = hashlib.md5(str(file_path).encode(), usedforsecurity=False).hexdigest()
    return THUMBNAILS_DIR / f"{file_hash}.png"
