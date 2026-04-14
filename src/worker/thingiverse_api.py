"""Direct API connector for fetching data from Thingiverse without an LLM."""

import logging
from typing import Any, List

import httpx
from sqlalchemy.orm import Session

from src.app.config import settings
from src.app.database import SessionLocal, engine
from src.app.models import Base, PrintJob

from .llm_scraper import ExtractedModelInfo

logger = logging.getLogger(__name__)


def _save_thingiverse_item(db: Session, item: dict[str, Any]) -> dict[str, Any] | None:
    """Save a single Thingiverse item to the database if it doesn't exist."""
    model_url = str(item.get("url", f"https://www.thingiverse.com/thing:{item.get('id')}"))
    if db.query(PrintJob).filter(PrintJob.source_url == model_url).first():
        return None

    new_job = PrintJob(
        title=str(item.get("name", "Unknown Thingiverse Model")),
        source="thingiverse",
        source_url=model_url,
        thumbnail_url=str(item.get("thumbnail", "")),
        author=str(item.get("creator", {}).get("name", "Unknown")),
        metadata_json={"extracted_via": "official_api", "raw_api_data": item},
    )
    db.add(new_job)
    return ExtractedModelInfo(
        title=str(new_job.title),
        url=str(new_job.source_url),
        thumbnail=str(new_job.thumbnail_url),
        author=str(new_job.author),
    ).model_dump()


def _fetch_thingiverse_data(token: str) -> list[dict[str, Any]]:
    """Fetch JSON data from Thingiverse API."""
    response = httpx.get(
        "https://api.thingiverse.com/users/me/likes",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()  # type: ignore


def _process_thingiverse_items(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Process and save Thingiverse items to the database."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    saved_items = []
    try:
        for item in data:
            saved = _save_thingiverse_item(db, item)
            if saved:
                saved_items.append(saved)
        db.commit()
        logger.info(f"Successfully synced {len(saved_items)} models from Thingiverse API.")
    except Exception as e:
        logger.error(f"Database error saving Thingiverse models: {e}")
        db.rollback()
    finally:
        db.close()
    return saved_items


def fetch_thingiverse_collections() -> List[dict[str, Any]]:
    """Fetch liked models from the official Thingiverse REST API."""
    token = settings.thingiverse_api_token
    if not token:
        logger.info("No Thingiverse API Token found. Skipping Thingiverse API sync.")
        return []

    try:
        data = _fetch_thingiverse_data(token)
        return _process_thingiverse_items(data)
    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        logger.error(f"Error while requesting Thingiverse API: {exc}")
        return []
