"""Unit tests for the LLM scraper functions."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock the database before importing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

with patch("src.app.database.engine", engine):
    with patch("src.app.database.SessionLocal", TestingSessionLocal):
        from src.app.models import Base
        from src.worker.llm_scraper import ExtractedModelInfo, get_page_html, run_scraper


@pytest.fixture(autouse=True)
def setup_db():
    """Set up and tear down the test database schema before/after each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@patch("src.worker.llm_scraper.settings")
def test_get_page_html_no_cookie(mock_settings):
    """Verify fallback to mock HTML if no cookie is present."""
    mock_settings.makerworld_cookie = ""
    mock_settings.printables_cookie = ""
    mock_settings.cults3d_cookie = ""
    mock_settings.minihoarder_cookie = ""

    html = get_page_html("makerworld", "http://test.com")
    assert "Mock Vase" not in html  # the mock string has "Cool Vase"
    assert "Cool Vase" in html


@patch("src.worker.llm_scraper.sync_playwright")
@patch("src.worker.llm_scraper.settings")
def test_get_page_html_with_cookie(mock_settings, mock_sync_playwright):
    """Verify playwright is launched when cookie is present."""
    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_sync_playwright.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.content.return_value = "<html>Live Page</html>"

    html = get_page_html("makerworld", "http://test.com", "fake_session_token")

    assert html == "<html>Live Page</html>"
    mock_context.add_cookies.assert_called_once()
    mock_page.goto.assert_called_with("http://test.com", wait_until="networkidle")


@patch("src.worker.llm_scraper.sync_playwright")
@patch("src.worker.llm_scraper.settings")
def test_get_page_html_playwright_error(mock_settings, mock_sync_playwright):
    """Verify playwright errors return empty string."""
    mock_p = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.side_effect = Exception("Playwright crash")

    html = get_page_html("makerworld", "http://test.com", "fake_session_token")
    assert html == ""


@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_empty_html(mock_get_html):
    """Verify run_scraper exits early if no HTML is returned."""
    mock_get_html.return_value = ""
    result = run_scraper("test", "http://test.com")
    assert result == []


@patch("src.worker.llm_scraper.scraper_agent.run_sync")
@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_success(mock_get_html, mock_run_sync):
    """Verify run_scraper parses LLM output and saves to DB."""
    mock_get_html.return_value = "<html>Valid Data</html>"

    mock_result = MagicMock()
    mock_result.data.models = [
        ExtractedModelInfo(title="LLM Vase", url="http://url.com", thumbnail=None, author=None)
    ]
    mock_run_sync.return_value = mock_result

    result = run_scraper("test", "http://test.com")

    assert len(result) == 1
    assert result[0]["title"] == "LLM Vase"

    # Second run should skip since it exists
    result2 = run_scraper("test", "http://test.com")
    assert len(result2) == 0


@patch("src.worker.llm_scraper.scraper_agent.run_sync")
@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_llm_error(mock_get_html, mock_run_sync):
    """Verify run_scraper uses fallback mock data if LLM throws an exception."""
    mock_get_html.return_value = "<html>Complex Data</html>"
    mock_run_sync.side_effect = Exception("Ollama disconnected")

    result = run_scraper("test", "http://test.com")

    assert len(result) == 2
    assert "Mock Vase" in result[0]["title"]


@patch("src.worker.llm_scraper.scraper_agent.run_sync")
@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_db_error(mock_get_html, mock_run_sync):
    """Verify run_scraper handles database commit errors safely."""
    mock_get_html.return_value = "<html>Valid Data</html>"
    mock_run_sync.return_value.data.models = [
        ExtractedModelInfo(title="LLM Vase", url="http://url.com", thumbnail=None, author=None)
    ]

    with patch("src.worker.llm_scraper.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.commit.side_effect = Exception("DB Constraints")

        result = run_scraper("test", "http://test.com")

        assert result == []  # Return logic should fail properly
        mock_db.rollback.assert_called_once()
