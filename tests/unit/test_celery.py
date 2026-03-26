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


@patch("src.worker.celery_app.settings")
@patch("src.worker.celery_app.SessionLocal")
def test_sync_local(mock_session, mock_settings, tmp_path):
    """Verify the local directory scan properly identifies and inserts missing files."""
    # Point settings.watch_directory to the temporary py.test directory
    mock_settings.watch_directory = str(tmp_path)
    mock_settings.verbose = False

    mock_db = MagicMock()
    mock_session.return_value = mock_db

    # Create physical files inside the temp directory
    existing_file = tmp_path / "existing.stl"
    existing_file.write_text("dummy stl content")

    new_file = tmp_path / "new.3mf"
    new_file.write_text("dummy 3mf content")

    ignored_file = tmp_path / "ignore.txt"
    ignored_file.write_text("this should be ignored")

    # We also create a nested subdirectory to test recursive rglob
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_file = nested_dir / "nested_new.STL"
    nested_file.write_text("dummy nested content")

    # Define what the mock DB query `.first()` returns.
    # It will be called once per valid file (.stl or .3mf) discovered.
    # We will simulate that "existing.stl" is already in the database,
    # but the others are not.
    def mock_db_check():
        # The sqlalchemy filter expression is passed down, we can inspect
        # the call args if we wanted to be perfectly precise, but simulating
        # based on call order is easiest here. We know rglob order isn't guaranteed,
        # so we inspect the mock's call history.
        pass

    def side_effect(*args, **kwargs):
        # We need to know which file path is being queried to return the right result.
        # Since we mock the DB session, we can just intercept the filter call.
        pass

    # A better approach to mock the DB finding only `existing.stl`:
    # We'll patch the PrintJob model or the query directly.
    # Let's just track how many times `add` is called.

    # Let's mock the `first()` method to return a MagicMock (exists) if "existing.stl"
    # is in the path, and None (doesn't exist) otherwise.
    # We have to inject this logic into the mocked query chain.
    class MockQuery:
        def __init__(self, is_existing):
            self.is_existing = is_existing

        def first(self):
            return MagicMock() if self.is_existing else None

    class MockFilter:
        def filter(self, condition):
            # condition is a BinaryExpression like PrintJob.file_path == '/tmp/.../existing.stl'
            # To actually catch the filename from the BinaryExpression, we inspect its right side.
            # Since we pass `str(file_path)` to the query, `condition.right.value` holds the path.
            is_existing = "existing.stl" in str(condition.right.value)
            return MockQuery(is_existing)

    mock_db.query.return_value = MockFilter()

    result = sync_local()

    # The function should have found "new.3mf" and "nested_new.STL"
    assert len(result) == 2
    titles = [r["title"] for r in result]
    assert "new.3mf" in titles
    assert "nested_new.STL" in titles
    assert "existing.stl" not in titles

    # The database `add` should be called twice
    assert mock_db.add.call_count == 2
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()
