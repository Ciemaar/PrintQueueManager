"""Test module for the Celery worker scheduled tasks."""

from unittest.mock import patch, MagicMock
from src.worker.celery_app import (
    setup_periodic_tasks,
    sync_makerworld,
    sync_printables,
    sync_thingiverse,
    sync_cults3d,
    sync_minihoarder,
    sync_local,
)


def test_setup_periodic_tasks():
    """Ensure all expected periodic synchronization tasks are registered."""
    sender_mock = MagicMock()
    setup_periodic_tasks(sender=sender_mock)
    assert sender_mock.add_periodic_task.call_count == 5


@patch("src.worker.celery_app.run_scraper")
def test_sync_makerworld(mock_run_scraper):
    """Verify that the MakerWorld task triggers the scraper with the correct target."""
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_makerworld()
    mock_run_scraper.assert_called_once_with("makerworld", "https://makerworld.com/en/user/likes")
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app.run_scraper")
def test_sync_printables(mock_run_scraper):
    """Verify that the Printables task triggers the scraper with the correct target."""
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_printables()
    mock_run_scraper.assert_called_once_with(
        "printables", "https://www.printables.com/user/collections"
    )
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app.fetch_thingiverse_collections")
def test_sync_thingiverse_api_success(mock_fetch_api):
    """Verify that the Thingiverse task prefers the API over scraping if data is returned."""
    mock_fetch_api.return_value = [{"title": "Test from API"}]
    result = sync_thingiverse()
    mock_fetch_api.assert_called_once()
    assert result == [{"title": "Test from API"}]


@patch("src.worker.celery_app.run_scraper")
@patch("src.worker.celery_app.fetch_thingiverse_collections")
def test_sync_thingiverse_api_fallback(mock_fetch_api, mock_run_scraper):
    """Verify that the Thingiverse task falls back to the scraper if the API returns no data."""
    mock_fetch_api.return_value = []
    mock_run_scraper.return_value = [{"title": "Test from Scraper"}]
    result = sync_thingiverse()
    mock_fetch_api.assert_called_once()
    mock_run_scraper.assert_called_once_with(
        "thingiverse", "https://www.thingiverse.com/user/collections"
    )
    assert result == [{"title": "Test from Scraper"}]


@patch("src.worker.celery_app.run_scraper")
def test_sync_cults3d(mock_run_scraper):
    """Verify that the Cults3D task triggers the scraper with the correct target."""
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_cults3d()
    mock_run_scraper.assert_called_once_with("cults3d", "https://cults3d.com/en/users/collections")
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app.run_scraper")
def test_sync_minihoarder(mock_run_scraper):
    """Verify that the Minihoarder task triggers the scraper with the correct target."""
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_minihoarder()
    mock_run_scraper.assert_called_once_with("minihoarder", "https://www.minihoarder.com/library/")
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app.Path")
@patch("src.worker.celery_app.SessionLocal")
def test_sync_local(mock_session, mock_path_cls):
    """Verify the local directory scan properly identifies and inserts missing files."""
    mock_db = MagicMock()
    mock_session.return_value = mock_db

    # Mock file discovery via Path.rglob
    mock_path_instance = MagicMock()
    mock_path_cls.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True

    # Setup 3 fake files
    file1 = MagicMock()
    file1.is_file.return_value = True
    file1.suffix = ".stl"
    file1.name = "existing.stl"
    file1.__str__.return_value = "/test/path/existing.stl"

    file2 = MagicMock()
    file2.is_file.return_value = True
    file2.suffix = ".3mf"
    file2.name = "new.3mf"
    file2.__str__.return_value = "/test/path/new.3mf"
    file2.stat.return_value.st_size = 1024

    file3 = MagicMock()
    file3.is_file.return_value = True
    file3.suffix = ".txt"
    file3.name = "ignore.txt"

    mock_path_instance.rglob.return_value = [file1, file2, file3]

    # Setup the query to return True for the existing file, False for the new file
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        MagicMock(),  # First file "existing.stl" found
        None,  # Second file "new.3mf" not found
    ]

    result = sync_local()

    # Only "new.3mf" should be added to the queue
    assert len(result) == 1
    assert result[0]["title"] == "new.3mf"
    assert mock_db.add.call_count == 1
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()
