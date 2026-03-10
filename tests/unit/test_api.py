"""Unit tests for external API functions."""

from unittest.mock import patch, MagicMock
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock the database before importing the API code
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

with patch("src.app.database.engine", engine):
    with patch("src.app.database.SessionLocal", TestingSessionLocal):
        from src.worker.thingiverse_api import fetch_thingiverse_collections
        from src.app.models import Base


@pytest.fixture(autouse=True)
def setup_db():
    """Set up and tear down the test database schema before/after each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_no_token(mock_settings):
    """Verify function returns empty list immediately if no token is provided."""
    mock_settings.thingiverse_api_token = ""
    result = fetch_thingiverse_collections()
    assert result == []


@patch("src.worker.thingiverse_api.httpx.get")
@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_success(mock_settings, mock_get):
    """Verify function correctly parses API response and saves to DB."""
    mock_settings.thingiverse_api_token = "fake_token"

    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"id": 123, "name": "API Vase", "thumbnail": "img.jpg", "creator": {"name": "Bob"}}
    ]
    mock_get.return_value = mock_response

    result = fetch_thingiverse_collections()

    assert len(result) == 1
    assert result[0]["title"] == "API Vase"


@patch("src.worker.thingiverse_api.httpx.get")
@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_existing_item(mock_settings, mock_get):
    """Verify function ignores items already in the database."""
    mock_settings.thingiverse_api_token = "fake_token"

    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 123, "name": "API Vase"}]
    mock_get.return_value = mock_response

    # First call adds it
    fetch_thingiverse_collections()
    # Second call should ignore it and return nothing saved
    result2 = fetch_thingiverse_collections()

    assert len(result2) == 0


@patch("src.worker.thingiverse_api.httpx.get")
@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_http_error(mock_settings, mock_get):
    """Verify function handles HTTP errors gracefully."""
    mock_settings.thingiverse_api_token = "fake_token"

    mock_response = MagicMock()
    # Ensure line breaks to respect length limit
    err = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock(status_code=500))
    mock_response.raise_for_status.side_effect = err
    mock_get.return_value = mock_response

    result = fetch_thingiverse_collections()

    assert result == []


@patch("src.worker.thingiverse_api.httpx.get")
@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_db_error(mock_settings, mock_get):
    """Verify function handles database errors gracefully."""
    mock_settings.thingiverse_api_token = "fake_token"

    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 123, "name": "API Vase"}]
    mock_get.return_value = mock_response

    with patch("src.worker.thingiverse_api.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.side_effect = Exception("DB Error")

        result = fetch_thingiverse_collections()

        assert result == []
        mock_db.rollback.assert_called_once()
