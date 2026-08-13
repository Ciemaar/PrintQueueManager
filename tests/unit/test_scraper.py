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
    mock_settings.makerworld_cookie = "fake_session_token"

    mock_p = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_sync_playwright.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.content.return_value = "<html>Live Page</html>"

    html = get_page_html("makerworld", "http://test.com")

    assert html == "<html>Live Page</html>"
    mock_context.add_cookies.assert_called_once()
    mock_page.goto.assert_called_with("http://test.com", wait_until="networkidle")


@patch("src.worker.llm_scraper.sync_playwright")
@patch("src.worker.llm_scraper.settings")
def test_get_page_html_playwright_error(mock_settings, mock_sync_playwright):
    """Verify playwright errors return empty string."""
    mock_settings.makerworld_cookie = "fake_session_token"

    mock_p = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_p
    mock_p.chromium.launch.side_effect = Exception("Playwright crash")

    html = get_page_html("makerworld", "http://test.com")
    assert html == ""


@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_empty_html(mock_get_html):
    """Verify run_scraper exits early if no HTML is returned."""
    mock_get_html.return_value = ""
    result = run_scraper("test", "http://test.com")
    assert result == []


@patch("src.worker.llm_scraper.get_scraper_agent")
@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_success(mock_get_html, mock_get_agent):
    """Verify run_scraper parses LLM output and saves to DB."""
    mock_get_html.return_value = "<html>Valid Data</html>"

    mock_result = MagicMock()
    mock_result.data.models = [
        ExtractedModelInfo(title="LLM Vase", url="http://url.com", thumbnail=None, author=None)
    ]
    mock_agent = MagicMock()
    mock_agent.run_sync.return_value = mock_result
    mock_get_agent.return_value = mock_agent

    result = run_scraper("test", "http://test.com")

    assert len(result) == 1
    assert result[0]["title"] == "LLM Vase"

    # Second run should skip since it exists
    result2 = run_scraper("test", "http://test.com")
    assert len(result2) == 0


@patch("src.worker.llm_scraper.get_scraper_agent")
@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_llm_error(mock_get_html, mock_get_agent):
    """Verify run_scraper uses fallback mock data if LLM throws an exception."""
    mock_get_html.return_value = "<html>Complex Data</html>"
    mock_agent = MagicMock()
    mock_agent.run_sync.side_effect = Exception("Ollama disconnected")
    mock_get_agent.return_value = mock_agent

    result = run_scraper("test", "http://test.com")

    assert len(result) == 2
    assert "Mock Vase" in result[0]["title"]


@patch("src.worker.llm_scraper.get_scraper_agent")
@patch("src.worker.llm_scraper.get_page_html")
def test_run_scraper_db_error(mock_get_html, mock_get_agent):
    """Verify run_scraper handles database commit errors safely."""
    mock_get_html.return_value = "<html>Valid Data</html>"
    mock_agent = MagicMock()
    mock_agent.run_sync.return_value.data.models = [
        ExtractedModelInfo(title="LLM Vase", url="http://url.com", thumbnail=None, author=None)
    ]
    mock_get_agent.return_value = mock_agent

    with patch("src.worker.llm_scraper.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.commit.side_effect = Exception("DB Constraints")

        result = run_scraper("test", "http://test.com")

        assert result == []  # Return logic should fail properly
        mock_db.rollback.assert_called_once()


@patch("src.worker.llm_scraper.Agent")
@patch("src.worker.llm_scraper.settings")
def test_get_scraper_agent_ollama_default(mock_settings, mock_agent_class):
    """Verify get_scraper_agent falls back to ollama by default."""
    from src.worker.llm_scraper import get_scraper_agent

    mock_settings.llm_model_mapping = {}

    get_scraper_agent("unknown")

    mock_agent_class.assert_called_once()
    assert mock_agent_class.call_args[0][0] == "ollama:llama3.2"


@patch("src.worker.llm_scraper.AsyncOpenAI")
@patch("src.worker.llm_scraper.CustomOpenAIProvider")
@patch("pydantic_ai.models.openai.OpenAIChatModel")
@patch("src.worker.llm_scraper.Agent")
@patch("src.worker.llm_scraper.settings")
def test_get_scraper_agent_openrouter(
    mock_settings, mock_agent_class, mock_openai_model, mock_custom_provider, mock_async_openai
):
    """Verify get_scraper_agent configures OpenRouter provider properly."""
    from src.worker.llm_scraper import get_scraper_agent

    mock_settings.llm_model_mapping = {"scraper.test_source": "openrouter:gpt-4o"}
    mock_settings.openrouter_api_key.get_secret_value.return_value = "secret123"

    get_scraper_agent("test_source")

    mock_async_openai.assert_called_once_with(
        base_url="https://openrouter.ai/api/v1", api_key="secret123"
    )

    mock_agent_class.assert_called_once()
    assert mock_agent_class.call_args[0][0] == mock_openai_model.return_value


@patch("src.worker.llm_scraper.AsyncOpenAI")
@patch("src.worker.llm_scraper.CustomOpenAIProvider")
@patch("pydantic_ai.models.openai.OpenAIChatModel")
@patch("src.worker.llm_scraper.Agent")
@patch("src.worker.llm_scraper.settings")
def test_get_scraper_agent_alibaba(
    mock_settings, mock_agent_class, mock_openai_model, mock_custom_provider, mock_async_openai
):
    """Verify get_scraper_agent configures Alibaba provider properly."""
    from src.worker.llm_scraper import get_scraper_agent

    mock_settings.llm_model_mapping = {"scraper.test_source": "alibaba:qwen-turbo"}
    mock_settings.alibaba_api_key.get_secret_value.return_value = "ali_secret123"

    get_scraper_agent("test_source")

    mock_async_openai.assert_called_once_with(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", api_key="ali_secret123"
    )

    mock_agent_class.assert_called_once()
    assert mock_agent_class.call_args[0][0] == mock_openai_model.return_value
