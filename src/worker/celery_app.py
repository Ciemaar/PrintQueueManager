import time
from celery import Celery
from src.app.config import settings
from .llm_scraper import run_scraper
from typing import List, Any

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
    # Calls sync_makerworld every 30 minutes
    sender.add_periodic_task(1800.0, sync_makerworld.s(), name='sync_makerworld_every_30_mins')

    # Calls sync_printables every 30 minutes
    sender.add_periodic_task(1800.0, sync_printables.s(), name='sync_printables_every_30_mins')

@celery_app.task
def sync_makerworld() -> List[dict[str, Any]]:
    print("Starting MakerWorld synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@celery_app.task
def sync_printables() -> List[dict[str, Any]]:
    print("Starting Printables synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("printables", "https://www.printables.com/user/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result
