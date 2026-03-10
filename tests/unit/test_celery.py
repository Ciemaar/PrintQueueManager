"""Unit tests for the celery worker functions."""

from unittest.mock import patch, MagicMock
from src.worker.celery_app import (
    sync_makerworld,
    sync_printables,
    sync_thingiverse,
    sync_cults3d,
    sync_minihoarder,
    setup_periodic_tasks,
)


def test_setup_periodic_tasks():
    """Verify all 5 platforms are scheduled."""
    sender_mock = MagicMock()
    setup_periodic_tasks(sender_mock)
    assert sender_mock.add_periodic_task.call_count == 5


@patch("src.worker.celery_app.run_scraper")
@patch("src.worker.celery_app.time.sleep")
def test_sync_makerworld(mock_sleep, mock_run_scraper):
    """Verify makerworld sync calls the scraper correctly."""
    mock_run_scraper.return_value = [{"title": "Vase"}]
    result = sync_makerworld()
    assert result == [{"title": "Vase"}]
    mock_run_scraper.assert_called_once_with("makerworld", "https://makerworld.com/en/user/likes")


@patch("src.worker.celery_app.run_scraper")
@patch("src.worker.celery_app.time.sleep")
def test_sync_printables(mock_sleep, mock_run_scraper):
    """Verify printables sync calls the scraper correctly."""
    mock_run_scraper.return_value = [{"title": "Vase"}]
    result = sync_printables()
    assert result == [{"title": "Vase"}]
    mock_run_scraper.assert_called_once_with(
        "printables", "https://www.printables.com/user/collections"
    )


@patch("src.worker.celery_app.fetch_thingiverse_collections")
@patch("src.worker.celery_app.time.sleep")
def test_sync_thingiverse_api_success(mock_sleep, mock_fetch_api):
    """Verify thingiverse sync returns API results directly if successful."""
    mock_fetch_api.return_value = [{"title": "Vase"}]
    result = sync_thingiverse()
    assert result == [{"title": "Vase"}]


@patch("src.worker.celery_app.run_scraper")
@patch("src.worker.celery_app.fetch_thingiverse_collections")
@patch("src.worker.celery_app.time.sleep")
def test_sync_thingiverse_api_fallback(mock_sleep, mock_fetch_api, mock_run_scraper):
    """Verify thingiverse sync falls back to scraper if API returns empty."""
    mock_fetch_api.return_value = []
    mock_run_scraper.return_value = [{"title": "Vase from scraper"}]
    result = sync_thingiverse()
    assert result == [{"title": "Vase from scraper"}]
    mock_run_scraper.assert_called_once()


@patch("src.worker.celery_app.run_scraper")
@patch("src.worker.celery_app.time.sleep")
def test_sync_cults3d(mock_sleep, mock_run_scraper):
    """Verify cults3d sync calls the scraper correctly."""
    mock_run_scraper.return_value = [{"title": "Vase"}]
    result = sync_cults3d()
    assert result == [{"title": "Vase"}]


@patch("src.worker.celery_app.run_scraper")
@patch("src.worker.celery_app.time.sleep")
def test_sync_minihoarder(mock_sleep, mock_run_scraper):
    """Verify minihoarder sync calls the scraper correctly."""
    mock_run_scraper.return_value = [{"title": "Vase"}]
    result = sync_minihoarder()
    assert result == [{"title": "Vase"}]
