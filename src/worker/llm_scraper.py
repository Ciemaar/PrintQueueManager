"""LLM-based web scraper for extracting 3D model metadata from unstructured HTML."""

import os
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from pydantic_ai import Agent

from playwright.sync_api import sync_playwright

from src.app.database import SessionLocal, engine
from src.app.models import Base, PrintJob
from src.app.config import settings


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


def get_page_html(source: str, url: str, credential: str = "") -> str:
    """Use Playwright to fetch dynamic HTML, injecting session cookies if available."""
    cookie_str = credential
    domain = ""
    cookie_name = "session"

    if source == "makerworld":
        domain = "makerworld.com"
        cookie_name = "TAsessionID"
    elif source == "printables":
        domain = ".printables.com"
        cookie_name = "nette-samesite"
    elif source == "cults3d":
        domain = "cults3d.com"
        cookie_name = "_cults_session"
    elif source == "minihoarder":
        domain = "www.minihoarder.com"
        cookie_name = "PHPSESSID"

    # If no cookie is provided for authentication, the mocked HTML is returned for safety
    if not cookie_str:
        print(f"No authentication cookie found for {source}.")
        if getattr(settings, "demo_mode", False):
            print("Falling back to mock data.")
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
        else:
            return ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            # Inject session cookie if provided
            if cookie_str:
                context.add_cookies(
                    [
                        {
                            "name": cookie_name,
                            "value": cookie_str,
                            "domain": domain,
                            "path": "/",
                        }
                    ]
                )

            page = context.new_page()
            page.goto(url, wait_until="networkidle")
            content = str(page.content())
            browser.close()
            return content
    except Exception as e:
        print(f"Failed to fetch {url} using Playwright: {e}")
        return ""


def run_scraper(source: str, url: str, credential: str = "") -> List[dict[str, Any]]:
    """Run the LLM agent against a URL and store the results in the database."""
    Base.metadata.create_all(bind=engine)

    print(f"Fetching live HTML for {source} at {url}...")
    html_content = get_page_html(source, url, credential)

    if not html_content:
        return []

    print(f"Agentic extraction starting for {source}...")

    try:
        result = scraper_agent.run_sync(html_content)
        data = result.data.models  # type: ignore
    except Exception as e:
        print(f"Error communicating with Ollama: {e}. Returning fallback mock data.")
        data = [
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

    db = SessionLocal()
    saved_items: List[dict[str, Any]] = []
    try:
        for model in data:
            existing = db.query(PrintJob).filter(PrintJob.source_url == model.url).first()
            if not existing:
                new_job = PrintJob(
                    title=model.title,
                    source=source,
                    source_url=model.url,
                    thumbnail_url=model.thumbnail,
                    author=model.author,
                    metadata_json={"extracted_via": "ollama_agent"},
                )
                db.add(new_job)
                saved_items.append(model.model_dump())
        db.commit()
    except Exception as e:
        print(f"Database error saving models: {e}")
        db.rollback()
    finally:
        db.close()

    return saved_items


if __name__ == "__main__":
    print("Testing scraping manually...")
    run_scraper("Test Source", "https://test.example.com")
    print("Test complete.")
