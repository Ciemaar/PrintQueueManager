"""Celery worker configuration and scheduled tasks for external data sync."""

import time
from typing import List, Any
from celery import Celery
from src.app.config import settings
from .llm_scraper import run_scraper
import os
from src.app.database import SessionLocal
from src.app.models import PrintJob
from .thingiverse_api import fetch_thingiverse_collections

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
    print("Starting MakerWorld synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    print(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_printables")
def sync_printables() -> List[dict[str, Any]]:
    """
    Fetch the user's collections from Printables.

    Uses Playwright and session cookies to access the private user page,
    and leverages the local Pydantic AI agent to extract model attributes.
    """
    print("Starting Printables synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("printables", "https://www.printables.com/user/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_thingiverse")
def sync_thingiverse() -> List[dict[str, Any]]:
    """
    Fetch the user's liked models from Thingiverse.

    Prioritizes querying the official Thingiverse REST API if a token is provided.
    If the token is missing or the API returns nothing, falls back to using
    Playwright and the local LLM agent to scrape the user's public collections page.
    """
    print("Starting Thingiverse synchronization via Official API...")
    time.sleep(2)
    # Prefer API logic for structured Thingiverse data.
    # If a token isn't provided, `fetch_thingiverse_collections` simply returns `[]`.
    result = fetch_thingiverse_collections()
    if not result:
        print("Fallback to Ollama agent for Thingiverse...")
        result = run_scraper("thingiverse", "https://www.thingiverse.com/user/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_cults3d")
def sync_cults3d() -> List[dict[str, Any]]:
    """
    Fetch the user's collections from Cults3D.

    Uses Playwright and session cookies to access the private user page,
    and leverages the local Pydantic AI agent to extract model attributes.
    """
    print("Starting Cults3D synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("cults3d", "https://cults3d.com/en/users/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_minihoarder")
def sync_minihoarder() -> List[dict[str, Any]]:
    """
    Fetch the user's purchased/downloaded library from Minihoarder.

    Uses Playwright and session cookies to access the private user library,
    and leverages the local Pydantic AI agent to extract model attributes.
    """
    print("Starting Minihoarder synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("minihoarder", "https://www.minihoarder.com/library/")
    print(f"Sync complete. Found {len(result)} models.")
    return result


@celery_app.task(name="sync_local")
def sync_local() -> List[dict[str, Any]]:
    """
    Scan the local watched directory for models and import any missing files.

    This is useful for bulk-importing a pre-existing directory that was already
    populated before the Watchdog service was running.
    """
    print(f"Scanning local directory for new models: {settings.watch_directory}")
    path = settings.watch_directory
    if not os.path.exists(path):
        os.makedirs(path)

    added_files = []
    db = SessionLocal()
    try:
        for root, _, files in os.walk(path):
            for filename in files:
                if filename.lower().endswith((".stl", ".3mf")):
                    file_path = os.path.join(root, filename)
                    # Check if file already exists in DB
                    existing_job = (
                        db.query(PrintJob).filter(PrintJob.file_path == file_path).first()
                    )
                    if existing_job:
                        continue

                    # Insert new job for the local file
                    new_job = PrintJob(
                        title=filename,
                        source="Local",
                        file_path=file_path,
                        metadata_json={"size_bytes": os.path.getsize(file_path)},
                    )
                    db.add(new_job)
                    added_files.append({"title": filename, "file_path": file_path})

        if added_files:
            db.commit()
            print(f"Added {len(added_files)} local files to print queue.")
        else:
            print("No new local files discovered.")
    except Exception as e:
        print(f"Error synchronizing local files: {e}")
        db.rollback()
    finally:
        db.close()

    return added_files
