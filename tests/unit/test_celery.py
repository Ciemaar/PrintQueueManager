"""Test module for the Celery worker scheduled tasks."""

from unittest.mock import MagicMock, patch

from src.worker.celery_app import (
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


class FakeJob:
    """Helper class to mock SQLAlchemy PrintJob objects in tests."""

    def __init__(self, path):
        """Initialize the fake job with a file path."""
        self.file_path = str(path)


class MockQuery:
    """Helper class to mock SQLAlchemy Query objects in tests."""

    def __init__(self, items):
        """Initialize the mock query with a list of items."""
        self.items = items

    def __iter__(self):
        """Return an iterator over the items."""
        return iter(self.items)


class MockFilter:
    """Helper class to mock SQLAlchemy Filter objects in tests."""

    def __init__(self, items):
        """Initialize the mock filter with a list of items."""
        self.items = items

    def filter(self, *args, **kwargs):
        """Mock the filter method to return a MockQuery."""
        return MockQuery(self.items)


@patch("src.worker.celery_app.settings")
@patch("src.worker.celery_app.SessionLocal")
def test_sync_local(mock_session, mock_settings, tmp_path):
    """Verify the local directory scan properly identifies and inserts missing files."""
    mock_settings.watch_directory = str(tmp_path)
    mock_settings.verbose = False

    mock_db = MagicMock()
    mock_session.return_value = mock_db

    existing_file = tmp_path / "existing.stl"
    existing_file.write_text("dummy stl content")

    new_file = tmp_path / "new.3mf"
    new_file.write_text("dummy 3mf content")

    (tmp_path / "ignore.txt").write_text("this should be ignored")

    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    (nested_dir / "nested_new.STL").write_text("dummy nested content")

    (tmp_path / "valid_link.3mf").symlink_to(new_file)
    (tmp_path / "broken_link.stl").symlink_to(tmp_path / "does_not_exist.stl")

    mock_db.query.return_value = MockFilter([FakeJob(existing_file)])

    result = sync_local()

    assert len(result) == 4
    titles = [r["title"] for r in result]
    for name in ["new.3mf", "nested_new.STL", "valid_link.3mf", "broken_link.stl"]:
        assert name in titles
    assert "existing.stl" not in titles

    broken_job_call = next(
        call for call in mock_db.add.call_args_list if call[0][0].title == "broken_link.stl"
    )
    assert broken_job_call[0][0].metadata_json.get("is_broken_symlink") is True
    assert broken_job_call[0][0].metadata_json.get("size_bytes") == 0

    assert mock_db.add.call_count == 4
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()
