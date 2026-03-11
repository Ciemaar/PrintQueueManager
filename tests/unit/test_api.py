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
    """Set up and tear down the test database schema before/after each test execution."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_no_token(mock_settings):
    """
    Ensure the API fetcher short-circuits and returns an empty list.

    It should immediately return if no Thingiverse API token is present in the configuration.
    """
    mock_settings.thingiverse_api_token = ""
    result = fetch_thingiverse_collections()
    assert not result


@patch("src.worker.thingiverse_api.httpx.get")
@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_success(mock_settings, mock_get):
    """
    Verify that a successful HTTP response is correctly mapped and inserted.

    The JSON payload from the Thingiverse REST API should be inserted into the
    local PostgreSQL database cleanly.
    """
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
    """
    Ensure that executing the fetcher consecutively does not duplicate models.

    It verifies that already existing target URLs are skipped during insert.
    """
    mock_settings.thingiverse_api_token = "fake_token"

    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 123, "name": "API Vase"}]
    mock_get.return_value = mock_response

    # First call adds it
    fetch_thingiverse_collections()
    # Second call should ignore it and return nothing saved
    result2 = fetch_thingiverse_collections()

    assert not result2


@patch("src.worker.thingiverse_api.httpx.get")
@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_http_error(mock_settings, mock_get):
    """
    Verify that if the external Thingiverse API goes down or returns a 500 error.

    The function handles the HTTPStatusError cleanly and returns an empty list
    without crashing.
    """
    mock_settings.thingiverse_api_token = "fake_token"

    mock_response = MagicMock()
    # Ensure line breaks to respect length limit
    err = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock(status_code=500))
    mock_response.raise_for_status.side_effect = err
    mock_get.return_value = mock_response

    result = fetch_thingiverse_collections()

    assert not result


@patch("src.worker.thingiverse_api.httpx.get")
@patch("src.worker.thingiverse_api.settings")
def test_fetch_thingiverse_db_error(mock_settings, mock_get):
    """
    Ensure that a failure during the SQLAlchemy database commit phase triggers rollback.

    A constraint violation or exception should trigger a proper session rollback
    and return safely.
    """
    mock_settings.thingiverse_api_token = "fake_token"

    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": 123, "name": "API Vase"}]
    mock_get.return_value = mock_response

    with patch("src.worker.thingiverse_api.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.side_effect = Exception("DB Error")

        result = fetch_thingiverse_collections()

        assert not result
        mock_db.rollback.assert_called_once()
