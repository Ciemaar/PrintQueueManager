"""Test module for the Celery worker scheduled tasks."""

from unittest.mock import patch, MagicMock
from src.app.models import ServiceConfig
from src.worker.celery_app import (
    _get_service_config,
    setup_periodic_tasks,
    sync_makerworld,
    sync_printables,
    sync_thingiverse,
    sync_cults3d,
    sync_minihoarder,
    sync_myminifactory,
    sync_local,
)


def test_setup_periodic_tasks():
    """Ensure all expected periodic synchronization tasks are registered."""
    sender_mock = MagicMock()
    setup_periodic_tasks(sender=sender_mock)
    assert sender_mock.add_periodic_task.call_count == 6


@patch("src.worker.celery_app.SessionLocal")
def test_get_service_config_disabled(mock_session):
    """Verify _get_service_config returns False if config is missing or disabled."""
    mock_db = MagicMock()
    mock_session.return_value = mock_db

    # Case 1: No config found
    mock_db.query.return_value.filter.return_value.first.return_value = None
    enabled, url, cred = _get_service_config("missing_service")
    assert enabled is False
    assert url == ""
    assert cred == ""

    # Case 2: Config exists but is disabled
    disabled_config = MagicMock(spec=ServiceConfig)
    disabled_config.enabled = 0
    mock_db.query.return_value.filter.return_value.first.return_value = disabled_config
    enabled, url, cred = _get_service_config("disabled_service")
    assert enabled is False


@patch("src.worker.celery_app.SessionLocal")
def test_get_service_config_enabled(mock_session):
    """Verify _get_service_config returns correctly parsed properties when enabled."""
    mock_db = MagicMock()
    mock_session.return_value = mock_db

    enabled_config = MagicMock(spec=ServiceConfig)
    enabled_config.enabled = 1
    enabled_config.target_url = "http://target"
    enabled_config.credential = "secret"

    mock_db.query.return_value.filter.return_value.first.return_value = enabled_config
    enabled, url, cred = _get_service_config("active_service")

    assert enabled is True
    assert url == "http://target"
    assert cred == "secret"


@patch("src.worker.celery_app._get_service_config")
@patch("src.worker.celery_app.run_scraper")
def test_sync_myminifactory(mock_run_scraper, mock_get_config):
    """Verify that the MyMiniFactory task triggers the scraper with the correct target."""
    mock_get_config.return_value = (True, "https://www.myminifactory.com/library", "fake_cookie")
    mock_run_scraper.return_value = [{"title": "TestMMF"}]
    result = sync_myminifactory()
    mock_run_scraper.assert_called_once_with(
        "myminifactory", "https://www.myminifactory.com/library", "fake_cookie"
    )
    assert result == [{"title": "TestMMF"}]


@patch("src.worker.celery_app._get_service_config")
@patch("src.worker.celery_app.run_scraper")
def test_sync_makerworld(mock_run_scraper, mock_get_config):
    """Verify that the MakerWorld task triggers the scraper with the correct target."""
    mock_get_config.return_value = (True, "https://makerworld.com/en/user/likes", "fake_cookie")
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_makerworld()
    mock_run_scraper.assert_called_once_with(
        "makerworld", "https://makerworld.com/en/user/likes", "fake_cookie"
    )
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app._get_service_config")
def test_sync_makerworld_disabled(mock_get_config):
    """Verify that the MakerWorld task exits early if disabled."""
    mock_get_config.return_value = (False, "", "")
    result = sync_makerworld()
    assert result == []


@patch("src.worker.celery_app._get_service_config")
@patch("src.worker.celery_app.run_scraper")
def test_sync_printables(mock_run_scraper, mock_get_config):
    """Verify that the Printables task triggers the scraper with the correct target."""
    mock_get_config.return_value = (
        True,
        "https://www.printables.com/user/collections",
        "fake_cookie",
    )
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_printables()
    mock_run_scraper.assert_called_once_with(
        "printables", "https://www.printables.com/user/collections", "fake_cookie"
    )
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app._get_service_config")
def test_sync_printables_disabled(mock_get_config):
    """Verify that the Printables task exits early if disabled."""
    mock_get_config.return_value = (False, "", "")
    result = sync_printables()
    assert result == []


@patch("src.worker.celery_app._get_service_config")
@patch("src.worker.celery_app.fetch_thingiverse_collections")
def test_sync_thingiverse_api_success(mock_fetch_api, mock_get_config):
    """Verify that the Thingiverse task prefers the API over scraping if data is returned."""
    mock_get_config.return_value = (
        True,
        "https://www.thingiverse.com/user/collections",
        "fake_token",
    )
    mock_fetch_api.return_value = [{"title": "Test from API"}]
    result = sync_thingiverse()
    mock_fetch_api.assert_called_once()
    assert result == [{"title": "Test from API"}]


@patch("src.worker.celery_app._get_service_config")
@patch("src.worker.celery_app.run_scraper")
@patch("src.worker.celery_app.fetch_thingiverse_collections")
def test_sync_thingiverse_api_fallback(mock_fetch_api, mock_run_scraper, mock_get_config):
    """Verify that the Thingiverse task falls back to the scraper if the API returns no data."""
    mock_get_config.return_value = (
        True,
        "https://www.thingiverse.com/user/collections",
        "fake_token",
    )
    mock_fetch_api.return_value = []
    mock_run_scraper.return_value = [{"title": "Test from Scraper"}]
    result = sync_thingiverse()
    mock_fetch_api.assert_called_once()
    mock_run_scraper.assert_called_once_with(
        "thingiverse", "https://www.thingiverse.com/user/collections", "fake_token"
    )
    assert result == [{"title": "Test from Scraper"}]


@patch("src.worker.celery_app._get_service_config")
def test_sync_thingiverse_disabled(mock_get_config):
    """Verify that the Thingiverse task exits early if disabled."""
    mock_get_config.return_value = (False, "", "")
    result = sync_thingiverse()
    assert result == []


@patch("src.worker.celery_app._get_service_config")
@patch("src.worker.celery_app.run_scraper")
def test_sync_cults3d(mock_run_scraper, mock_get_config):
    """Verify that the Cults3D task triggers the scraper with the correct target."""
    mock_get_config.return_value = (True, "https://cults3d.com/en/users/collections", "fake_cookie")
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_cults3d()
    mock_run_scraper.assert_called_once_with(
        "cults3d", "https://cults3d.com/en/users/collections", "fake_cookie"
    )
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app._get_service_config")
@patch("src.worker.celery_app.run_scraper")
def test_sync_minihoarder(mock_run_scraper, mock_get_config):
    """Verify that the Minihoarder task triggers the scraper with the correct target."""
    mock_get_config.return_value = (True, "https://www.minihoarder.com/library/", "fake_cookie")
    mock_run_scraper.return_value = [{"title": "Test"}]
    result = sync_minihoarder()
    mock_run_scraper.assert_called_once_with(
        "minihoarder", "https://www.minihoarder.com/library/", "fake_cookie"
    )
    assert result == [{"title": "Test"}]


@patch("src.worker.celery_app._get_service_config")
def test_sync_cults3d_disabled(mock_get_config):
    """Verify that the Cults3D task exits early if disabled."""
    mock_get_config.return_value = (False, "", "")
    result = sync_cults3d()
    assert result == []


@patch("src.worker.celery_app._get_service_config")
def test_sync_minihoarder_disabled(mock_get_config):
    """Verify that the Minihoarder task exits early if disabled."""
    mock_get_config.return_value = (False, "", "")
    result = sync_minihoarder()
    assert result == []


@patch("src.worker.celery_app._get_service_config")
def test_sync_myminifactory_disabled(mock_get_config):
    """Verify that the MyMiniFactory task exits early if disabled."""
    mock_get_config.return_value = (False, "", "")
    result = sync_myminifactory()
    assert result == []


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
