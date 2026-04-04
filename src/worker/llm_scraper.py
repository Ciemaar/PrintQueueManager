"""LLM-based web scraper for extracting 3D model metadata from unstructured HTML."""

import logging
import os
from typing import Any, List, Optional

from playwright.sync_api import sync_playwright
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.app.config import settings
from src.app.database import SessionLocal, engine
from src.app.models import Base, PrintJob

logger = logging.getLogger(__name__)


class ExtractedModelInfo(BaseModel):
    """Schema representing an individual 3D model extracted from a page."""

    title: str = Field(description="The name of the 3D model")
    url: str = Field(description="The direct link to the model page")
    thumbnail: Optional[str] = Field(None, description="The URL of the model's cover image")
    author: Optional[str] = Field(None, description="The creator of the model")


class ScrapedPageData(BaseModel):
    """Schema representing the structured output of an LLM scraping agent."""

    models: List[ExtractedModelInfo]


if "OLLAMA_BASE_URL" not in os.environ:
    os.environ["OLLAMA_BASE_URL"] = settings.ollama_host

scraper_agent: Agent[Any, ScrapedPageData] = Agent(
    "ollama:llama3.2",  # Requires running Ollama locally with this model
    output_type=ScrapedPageData,
    system_prompt=(
        "You are an expert web scraping agent specialized in extracting 3D model data. "
        "Extract the model's title, direct URL, author name, and thumbnail image URL from the "
        "provided HTML content. Return the output exactly in the requested JSON format."
    ),
)


def _get_cookie_config(source: str) -> tuple[str, str]:
    """Return the session cookie and domain for a given source."""
    configs = {
        "makerworld": (settings.makerworld_cookie, "makerworld.com"),
        "printables": (settings.printables_cookie, ".printables.com"),
        "cults3d": (settings.cults3d_cookie, "cults3d.com"),
        "minihoarder": (settings.minihoarder_cookie, "www.minihoarder.com"),
    }
    return configs.get(source, ("", ""))


def _get_mock_html(source: str) -> str:
    """Return mock HTML content for demo mode."""
    return f"""
    <html><body>
    <div class="model-card">
        <img src="https://example.com/thumb1.jpg" />
        <a href="https://{source}.example.com/model/123">Cool Vase</a>
        <span class="author">By PrintMaster</span>
    </div>
    <div class="model-card">
        <img src="https://example.com/thumb2.jpg" />
        <a href="https://{source}.example.com/model/456">Desk Organizer</a>
        <span class="author">By OrganizerPro</span>
    </div>
    </body></html>
    """


def get_page_html(source: str, url: str) -> str:
    """Use Playwright to fetch dynamic HTML, injecting session cookies if available."""
    cookie_str, domain = _get_cookie_config(source)

    if not cookie_str:
        logger.info(f"No authentication cookie found for {source}.")
        if getattr(settings, "demo_mode", False):
            logger.info("Falling back to mock data.")
            return _get_mock_html(source)
        return ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(
                [{"name": "session", "value": cookie_str, "domain": domain, "path": "/"}]
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle")
            content = str(page.content())
            browser.close()
            return content
    except Exception as e:
        logger.error(f"Failed to fetch {url} using Playwright: {e}")
        return ""


def _get_fallback_data(source: str) -> list[ExtractedModelInfo]:
    """Return fallback ExtractedModelInfo list when LLM fails."""
    return [
        ExtractedModelInfo(
            title=f"Mock Vase from {source}",
            url=f"http://{source}.com/1",
            author="MockUser1",
            thumbnail="",
        ),
        ExtractedModelInfo(
            title=f"Mock Holder from {source}",
            url=f"http://{source}.com/2",
            author="MockUser2",
            thumbnail="",
        ),
    ]


def _save_extracted_model(db: SessionLocal, source: str, model: ExtractedModelInfo) -> dict | None:
    """Save an extracted model if it doesn't already exist in the database."""
    if db.query(PrintJob).filter(PrintJob.source_url == model.url).first():
        return None
    db.add(
        PrintJob(
            title=model.title,
            source=source,
            source_url=model.url,
            thumbnail_url=model.thumbnail,
            author=model.author,
            metadata_json={"extracted_via": "ollama_agent"},
        )
    )
    return model.model_dump()


def _get_scraped_data(source: str, html_content: str) -> list[ExtractedModelInfo]:
    """Run the LLM agent to extract model info from HTML."""
    try:
        return scraper_agent.run_sync(html_content).data.models  # type: ignore
    except Exception as e:
        logger.error(f"Error communicating with Ollama: {e}. Using fallback.")
        return _get_fallback_data(source)


def run_scraper(source: str, url: str) -> List[dict[str, Any]]:
    """Run the LLM agent against a URL and store the results in the database."""
    Base.metadata.create_all(bind=engine)
    html_content = get_page_html(source, url)
    if not html_content:
        return []

    data = _get_scraped_data(source, html_content)
    db = SessionLocal()
    saved_items: List[dict[str, Any]] = []
    try:
        for model in data:
            saved = _save_extracted_model(db, source, model)
            if saved:
                saved_items.append(saved)
        db.commit()
    except Exception as e:
        logger.error(f"Database error saving models: {e}")
        db.rollback()
    finally:
        db.close()
    return saved_items


if __name__ == "__main__":
    logger.info("Testing scraping manually...")
    run_scraper("Test Source", "https://test.example.com")
    logger.info("Test complete.")
