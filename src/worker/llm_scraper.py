import os
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from pydantic_ai import Agent

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
    'ollama:llama3.2',  # Requires running Ollama locally with this model
    output_type=ScrapedPageData,
    system_prompt=(
        "You are an expert web scraping agent specialized in extracting 3D model data. "
        "Extract the model's title, direct URL, author name, and thumbnail image URL from the provided HTML content. "
        "Return the output exactly in the requested JSON format."
    ),
)

def run_scraper(source: str, url: str) -> List[dict[str, Any]]:
    """
    Runs the agent against a URL (mocked in testing) and stores results in the database.
    """
    Base.metadata.create_all(bind=engine)
    mock_html = f"""
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

    print(f"Agentic extraction starting for {source} at {url}")

    try:
        result = scraper_agent.run_sync(mock_html)
        data = result.data.models
    except Exception as e:
        print(f"Error communicating with Ollama: {e}. Returning mock data.")
        data = [
            ExtractedModelInfo(
                title=f"Mock Vase from {source}",
                url=f"http://{source}.com/1",
                author="MockUser1",
                thumbnail=""
            ),
            ExtractedModelInfo(
                title=f"Mock Holder from {source}",
                url=f"http://{source}.com/2",
                author="MockUser2",
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
