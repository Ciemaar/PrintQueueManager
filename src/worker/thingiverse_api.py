"""Direct API connector for fetching data from Thingiverse without an LLM."""

import logging
from typing import Any, List

import httpx

from src.app.config import settings
from src.app.database import SessionLocal, engine
from src.app.models import Base, PrintJob

from .llm_scraper import ExtractedModelInfo

logger = logging.getLogger(__name__)


def fetch_thingiverse_collections() -> List[dict[str, Any]]:
    """
    Fetch liked or collected models from the official Thingiverse REST API.

    Bypasses the LLM agentic scraper entirely for perfect structured data.
    Returns an empty list if no token is configured.
    """
    token = settings.thingiverse_api_token
    if not token:
        logger.info("No Thingiverse API Token found. Skipping Thingiverse API sync.")
        return []

    url = "https://api.thingiverse.com/users/me/likes"
    headers = {"Authorization": f"Bearer {token}"}

    saved_items: List[dict[str, Any]] = []

    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Initialize DB
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()

        try:
            # Batch query existing URLs to avoid N+1 queries
            urls = [
                str(item.get("url", f"https://www.thingiverse.com/thing:{item.get('id')}"))
                for item in data
            ]

            existing_urls = set()
            if urls:
                existing_urls = {
                    url
                    for (url,) in db.query(PrintJob.source_url)
                    .filter(PrintJob.source_url.in_(urls))
                    .all()
                }

            for item in data:
                model_url = str(
                    item.get("url", f"https://www.thingiverse.com/thing:{item.get('id')}")
                )

                if model_url not in existing_urls:
                    new_job = PrintJob(
                        title=str(item.get("name", "Unknown Thingiverse Model")),
                        source="thingiverse",
                        source_url=model_url,
                        thumbnail_url=str(item.get("thumbnail", "")),
                        author=str(item.get("creator", {}).get("name", "Unknown")),
                        metadata_json={"extracted_via": "official_api", "raw_api_data": item},
                    )
                    db.add(new_job)

                    # Add to set to avoid duplicates within the same batch
                    existing_urls.add(model_url)

                    extracted = ExtractedModelInfo(
                        title=str(new_job.title),
                        url=str(new_job.source_url),
                        thumbnail=str(new_job.thumbnail_url),
                        author=str(new_job.author),
                    )
                    saved_items.append(extracted.model_dump())
            db.commit()
            logger.info(f"Successfully synced {len(saved_items)} models from Thingiverse API.")
        except Exception as e:
            logger.error(f"Database error saving Thingiverse models: {e}")
            db.rollback()
        finally:
            db.close()

    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting Thingiverse API: {exc}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Error response {exc.response.status_code} while requesting Thingiverse API.")

    return saved_items
