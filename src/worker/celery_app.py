"""Celery worker configuration and scheduled tasks for external data sync."""

import logging
import time
from pathlib import Path
from typing import Any, List

from celery import Celery

from src.app.config import settings
from src.app.database import SessionLocal
from src.app.logging_config import setup_logging
from src.app.models import PrintJob

from .llm_scraper import run_scraper
from .thingiverse_api import fetch_thingiverse_collections

setup_logging()
logger = logging.getLogger(__name__)

celery_app = Celery("printqueue", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.on_after_configure.connect  # type: ignore
def setup_periodic_tasks(sender: Any, **kwargs: Any) -> None:
    """Register all platform synchronization tasks to run automatically based on config."""
    sender.add_periodic_task(
        settings.makerworld_sync_interval, sync_makerworld.s(), name="sync_makerworld_periodic"
    )
    sender.add_periodic_task(
        settings.printables_sync_interval, sync_printables.s(), name="sync_printables_periodic"
    )
    sender.add_periodic_task(
        settings.thingiverse_sync_interval, sync_thingiverse.s(), name="sync_thingiverse_periodic"
    )
    sender.add_periodic_task(
        settings.cults3d_sync_interval, sync_cults3d.s(), name="sync_cults3d_periodic"
    )
    sender.add_periodic_task(
        settings.minihoarder_sync_interval, sync_minihoarder.s(), name="sync_minihoarder_periodic"
    )


@celery_app.task(name="sync_makerworld")
def sync_makerworld() -> List[dict[str, Any]]:
    """
    Fetch the user's liked models from MakerWorld.

    Uses Playwright and session cookies to access the private user page,
    and leverages the local Pydantic AI agent to extract model attributes.
    """
    logger.info("Starting MakerWorld synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    logger.info(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_printables")
def sync_printables() -> List[dict[str, Any]]:
    """
    Fetch the user's collections from Printables.

    Uses Playwright and session cookies to access the private user page,
    and leverages the local Pydantic AI agent to extract model attributes.
    """
    logger.info("Starting Printables synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("printables", "https://www.printables.com/user/collections")
    logger.info(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_thingiverse")
def sync_thingiverse() -> List[dict[str, Any]]:
    """
    Fetch the user's liked models from Thingiverse.

    Prioritizes querying the official Thingiverse REST API if a token is provided.
    If the token is missing or the API returns nothing, falls back to using
    Playwright and the local LLM agent to scrape the user's public collections page.
    """
    logger.info("Starting Thingiverse synchronization via Official API...")
    time.sleep(2)
    # Prefer API logic for structured Thingiverse data.
    # If a token isn't provided, `fetch_thingiverse_collections` simply returns `[]`.
    result = fetch_thingiverse_collections()
    if not result:
        logger.info("Fallback to Ollama agent for Thingiverse...")
        result = run_scraper("thingiverse", "https://www.thingiverse.com/user/collections")
    logger.info(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_cults3d")
def sync_cults3d() -> List[dict[str, Any]]:
    """
    Fetch the user's collections from Cults3D.

    Uses Playwright and session cookies to access the private user page,
    and leverages the local Pydantic AI agent to extract model attributes.
    """
    logger.info("Starting Cults3D synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("cults3d", "https://cults3d.com/en/users/collections")
    logger.info(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_minihoarder")
def sync_minihoarder() -> List[dict[str, Any]]:
    """
    Fetch the user's purchased/downloaded library from Minihoarder.

    Uses Playwright and session cookies to access the private user library,
    and leverages the local Pydantic AI agent to extract model attributes.
    """
    logger.info("Starting Minihoarder synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("minihoarder", "https://www.minihoarder.com/library/")
    logger.info(f"Sync complete. Found {len(result)} models.")
    return result


def _process_local_file(file_path: Path, known_paths: set[str | None]) -> dict[str, Any] | None:
    """Check if a local file is a valid 3D model and return its metadata if it's new."""
    if not (file_path.is_file() or file_path.is_symlink()):
        return None
    if file_path.suffix.lower() not in {".stl", ".3mf"}:
        return None
    if str(file_path) in known_paths:
        return None

    is_broken = file_path.is_symlink() and not file_path.exists()
    logger.debug(
        f"Discovered {'broken symlink' if is_broken else 'new 3D file'}: "
        f"{file_path.name} at {file_path}"
    )

    metadata: dict[str, Any] = {"size_bytes": 0 if is_broken else file_path.stat().st_size}
    if is_broken:
        metadata["is_broken_symlink"] = True

    return {
        "title": file_path.name,
        "source": "Local",
        "file_path": str(file_path),
        "metadata_json": metadata,
    }


@celery_app.task(name="sync_local")
def sync_local() -> List[dict[str, Any]]:
    """Scan the local watched directory for models and import any missing files."""
    logger.info(f"Scanning local directory for new models: {settings.watch_directory}")
    watch_path = Path(settings.watch_directory)
    watch_path.mkdir(parents=True, exist_ok=True)

    added_files = []
    db = SessionLocal()
    try:
        known_paths = {
            job.file_path for job in db.query(PrintJob.file_path).filter(PrintJob.source == "Local")
        }

        for file_path in watch_path.rglob("*"):
            job_data = _process_local_file(file_path, known_paths)
            if job_data:
                db.add(PrintJob(**job_data))
                added_files.append({"title": job_data["title"], "file_path": job_data["file_path"]})

        if added_files:
            db.commit()
            logger.info(f"Added {len(added_files)} local files to print queue.")
        else:
            logger.info("No new local files discovered.")
    except Exception as e:
        logger.error(f"Error synchronizing local files: {e}")
        db.rollback()
    finally:
        db.close()

    return added_files
