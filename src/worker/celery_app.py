"""Celery worker configuration and scheduled tasks for external data sync."""

import time
from typing import List, Any
from celery import Celery
from src.app.config import settings
from .llm_scraper import run_scraper
from .thingiverse_api import fetch_thingiverse_collections

celery_app = Celery(
    "printqueue",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Any, **kwargs: Any) -> None:
    """Schedule recurring sync tasks for various 3D model platforms."""
    sender.add_periodic_task(1800.0, sync_makerworld.s(), name='sync_makerworld_every_30_mins')
    sender.add_periodic_task(1800.0, sync_printables.s(), name='sync_printables_every_30_mins')
    sender.add_periodic_task(1800.0, sync_thingiverse.s(), name='sync_thingiverse_every_30_mins')
    sender.add_periodic_task(1800.0, sync_cults3d.s(), name='sync_cults3d_every_30_mins')
    sender.add_periodic_task(1800.0, sync_minihoarder.s(), name='sync_minihoarder_every_30_mins')

@celery_app.task
def sync_makerworld() -> List[dict[str, Any]]:
    """Synchronize liked models from MakerWorld using an LLM scraper."""
    print("Starting MakerWorld synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@celery_app.task
def sync_printables() -> List[dict[str, Any]]:
    """Synchronize liked collections from Printables using an LLM scraper."""
    print("Starting Printables synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("printables", "https://www.printables.com/user/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@celery_app.task
def sync_thingiverse() -> List[dict[str, Any]]:
    """Synchronize liked models from Thingiverse using the API, falling back to LLM."""
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

@celery_app.task
def sync_cults3d() -> List[dict[str, Any]]:
    """Synchronize liked collections from Cults3D using an LLM scraper."""
    print("Starting Cults3D synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("cults3d", "https://cults3d.com/en/users/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@celery_app.task
def sync_minihoarder() -> List[dict[str, Any]]:
    """Synchronize library from Minihoarder using an LLM scraper."""
    print("Starting Minihoarder synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("minihoarder", "https://www.minihoarder.com/library/")
    print(f"Sync complete. Found {len(result)} models.")
    return result
