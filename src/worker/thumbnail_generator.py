import logging
import os

import trimesh

logger = logging.getLogger(__name__)

# Constants for paths
STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static"
)
THUMBNAIL_DIR = os.path.join(STATIC_DIR, "thumbnails")


def get_thumbnail_file_path(job_id: int) -> str:
    """Return the absolute path where the thumbnail image should be saved on disk."""
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    return os.path.join(THUMBNAIL_DIR, f"job_{job_id}.png")


def get_thumbnail_path(job_id: int) -> str | None:
    """Return the relative web URL path for a job's thumbnail, or None if it does not exist."""
    file_path = get_thumbnail_file_path(job_id)
    if os.path.exists(file_path):
        return f"/static/thumbnails/job_{job_id}.png"
    return None


def generate_thumbnail(file_path: str, job_id: int) -> bool:
    """
    Generate a 3D rendering of an STL or 3MF file and save it as a PNG.

    Requires an X Server (Xvfb) if running headlessly on Linux.
    """
    if not os.path.exists(file_path):
        logger.error(f"Cannot generate thumbnail: File not found at {file_path}")
        return False

    output_path = get_thumbnail_file_path(job_id)

    # Note: If running locally without a display on Linux, Xvfb must be active.
    # In Docker, we typically wrap the Celery worker process with xvfb-run.
    try:
        # Load the mesh (works for .stl and .3mf)
        mesh = trimesh.load(file_path, force="mesh")

        # Create a scene
        scene = trimesh.Scene(mesh)

        # Set a decent camera angle to view the object
        # (Isometrics or slightly angled down usually look best)
        # trimesh auto-centers by default

        # Render the scene to a PNG bytes object (uses Pyglet under the hood)
        png_bytes = scene.save_image(resolution=[500, 500])

        if not png_bytes:
            logger.error(f"Failed to generate image bytes for {file_path}")
            return False

        # Save to disk
        with open(output_path, "wb") as f:
            f.write(png_bytes)

        logger.info(f"Successfully generated thumbnail for job {job_id} at {output_path}")
        return True

    except Exception as e:
        logger.error(f"Exception during thumbnail generation for {file_path}: {e}")
        return False
