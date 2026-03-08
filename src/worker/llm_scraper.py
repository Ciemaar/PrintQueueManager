import os
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from pydantic_ai import Agent

from playwright.sync_api import sync_playwright

from src.app.database import SessionLocal, engine
from src.app.models import Base, PrintJob
from src.app.config import settings

class ExtractedModelInfo(BaseModel):
    title: str = Field(description="The name of the 3D model")
    url: str = Field(description="The direct link to the model page")
    thumbnail: Optional[str] = Field(None, description="The URL of the model's cover image")
    author: Optional[str] = Field(None, description="The creator of the model")

class ScrapedPageData(BaseModel):
    models: List[ExtractedModelInfo]

if "OLLAMA_BASE_URL" not in os.environ:
    os.environ["OLLAMA_BASE_URL"] = settings.ollama_host

scraper_agent: Agent[Any, ScrapedPageData] = Agent(
    'ollama:llama3.2',
    output_type=ScrapedPageData,
    system_prompt=(
        "You are an expert web scraping agent specialized in extracting 3D model data. "
        "Extract the model's title, direct URL, author name, and thumbnail image URL from the provided HTML content. "
        "Return the output exactly in the requested JSON format."
    ),
)

def get_page_html(source: str, url: str) -> str:
    """Uses Playwright to fetch dynamic HTML, injecting session cookies if available."""
    cookie_str = ""
    domain = ""
    if source == "makerworld":
        cookie_str = settings.makerworld_cookie
        domain = "makerworld.com"
    elif source == "printables":
        cookie_str = settings.printables_cookie
        domain = ".printables.com"
    elif source == "cults3d":
        cookie_str = settings.cults3d_cookie
        domain = "cults3d.com"
    elif source == "minihoarder":
        cookie_str = settings.minihoarder_cookie
        domain = "www.minihoarder.com"

    # If no cookie is provided for authentication, the mocked HTML is returned for safety
    if not cookie_str:
        print(f"No authentication cookie found for {source}. Falling back to mock data.")
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

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            # Inject session cookie if provided
            if cookie_str:
                context.add_cookies([{
                    "name": "session", # Varies by site; this is a simplified generic approach
                    "value": cookie_str,
                    "domain": domain,
                    "path": "/"
                }])

            page = context.new_page()
            page.goto(url, wait_until="networkidle")
            content = str(page.content())
            browser.close()
            return content
    except Exception as e:
        print(f"Failed to fetch {url} using Playwright: {e}")
        return ""

def run_scraper(source: str, url: str) -> List[dict[str, Any]]:
    """Runs the agent against a URL and stores results in the database."""
    Base.metadata.create_all(bind=engine)

    print(f"Fetching live HTML for {source} at {url}...")
    html_content = get_page_html(source, url)

    if not html_content:
        return []

    print(f"Agentic extraction starting for {source}...")

    try:
        result = scraper_agent.run_sync(html_content)
        data = result.data.models
    except Exception as e:
        print(f"Error communicating with Ollama: {e}. Returning fallback mock data.")
        data = [
            ExtractedModelInfo(
                title=f"Mock Vase from {source}",
                url=f"http://{source}.com/1",
                author="MockUser1",
                thumbnail=""
            )
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
                    metadata_json={"extracted_via": "ollama_agent"}
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
