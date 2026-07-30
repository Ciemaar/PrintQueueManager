"""Test module for the Celery worker scheduled tasks."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.worker.celery_app import (
    normalize_priorities,
    setup_periodic_tasks,
    sync_cults3d,
    sync_local,
    sync_makerworld,
    sync_minihoarder,
    sync_printables,
    sync_thingiverse,
)


def test_setup_periodic_tasks():
    """Ensure all expected periodic synchronization tasks are registered."""
    sender_mock = MagicMock()
    setup_periodic_tasks(sender=sender_mock)
    assert sender_mock.add_periodic_task.call_count == 6


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

    # Create a valid symlink to new.3mf
    valid_symlink = tmp_path / "valid_link.3mf"
    valid_symlink.symlink_to(new_file)

    # Create a broken symlink
    broken_symlink = tmp_path / "broken_link.stl"
    broken_symlink.symlink_to(tmp_path / "does_not_exist.stl")

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

    # Mocking the new behavior in `sync_local` which queries the db
    # to return an iterable of jobs to build a set.
    class FakeJob:
        def __init__(self, path):
            self.file_path = str(path)

    class MockQuery:
        def __iter__(self):
            # Simulates the DB query returning a single known file
            yield FakeJob(existing_file)

    class MockFilter:
        def filter(self, *args, **kwargs):
            return MockQuery()

    mock_db.query.return_value = MockFilter()

    result = sync_local()

    # The function should find "new.3mf", "nested_new.STL", "valid_link.3mf", and "broken_link.stl"
    assert len(result) == 4
    titles = [r["title"] for r in result]
    assert "new.3mf" in titles
    assert "nested_new.STL" in titles
    assert "valid_link.3mf" in titles
    assert "broken_link.stl" in titles
    assert "existing.stl" not in titles

    # Check that the broken symlink is correctly identified in its metadata
    broken_job_call = next(
        call for call in mock_db.add.call_args_list if call[0][0].title == "broken_link.stl"
    )
    assert broken_job_call[0][0].metadata_json.get("is_broken_symlink") is True
    assert broken_job_call[0][0].metadata_json.get("size_bytes") == 0

    # The database `add` should be called four times
    assert mock_db.add.call_count == 4
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


@patch("src.worker.celery_app.SessionLocal")
def test_normalize_priorities_success(mock_session_local):
    """Verify that priorities are reassigned as sequential floats."""
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db

    # Create mock jobs
    job1 = MagicMock()
    job2 = MagicMock()
    # Setup the chain: query().filter().order_by().all()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_order = mock_filter.order_by.return_value
    mock_order.all.return_value = [job1, job2]

    normalize_priorities()

    # Verify sequential priorities starting from 1.0
    assert job1.user_priority == 1.0
    assert job2.user_priority == 2.0
    mock_db.commit.assert_called_once()

    # Verify query calls
    mock_db.query.assert_called()
    # Check that it filters out deleted jobs
    filter_args = mock_query.filter.call_args[0][0]
    # In SQLAlchemy this is usually a BinaryExpression
    assert "status != 'DELETED'" in str(filter_args) or "status != :status_1" in str(filter_args)
    assert mock_filter.order_by.called


@patch("src.worker.celery_app.SessionLocal")
def test_normalize_priorities_exception(mock_session_local):
    """Verify that database exceptions trigger a rollback."""
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.query.side_effect = SQLAlchemyError("DB Error")

    # The task should catch the exception, log it, and rollback
    normalize_priorities()

    mock_db.rollback.assert_called_once()


@patch("src.worker.celery_app.SessionLocal")
def test_normalize_priorities_unknown_exception(mock_session_local):
    """Verify that unknown exceptions are rolled back and re-raised."""
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_db.query.side_effect = Exception("Unknown Error")

    with pytest.raises(Exception, match="Unknown Error"):
        normalize_priorities()

    mock_db.rollback.assert_called_once()


@patch("src.worker.celery_app.settings")
@patch("src.worker.celery_app.SessionLocal")
def test_sync_local_db_query_error(mock_session_local, mock_settings, tmp_path):
    """Verify that a database error during the query phase triggers a rollback."""
    mock_settings.watch_directory = str(tmp_path)
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Simulate an error when querying for known paths
    mock_db.query.side_effect = SQLAlchemyError("Database query failed")

    sync_local()
    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()


@patch("src.worker.celery_app.settings")
@patch("src.worker.celery_app.SessionLocal")
def test_sync_local_db_commit_error(mock_session_local, mock_settings, tmp_path):
    """Verify that a database error during the commit phase triggers a rollback."""
    mock_settings.watch_directory = str(tmp_path)
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Create a physical file to ensure we attempt a commit
    new_file = tmp_path / "new.stl"
    new_file.write_text("dummy content")

    # Mock the query to return empty (no known paths)
    mock_db.query.return_value.filter.return_value.__iter__.return_value = []

    # Simulate an error during commit
    mock_db.commit.side_effect = SQLAlchemyError("Database commit failed")

    sync_local()
    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()


@patch("src.worker.celery_app.settings")
@patch("src.worker.celery_app.SessionLocal")
def test_sync_local_unknown_error(mock_session_local, mock_settings, tmp_path):
    """Verify that an unknown error is re-raised and session is rolled back."""
    mock_settings.watch_directory = str(tmp_path)
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Simulate an unknown exception during query
    mock_db.query.side_effect = Exception("Unknown failure")

    with pytest.raises(Exception, match="Unknown failure"):
        sync_local()

    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()
