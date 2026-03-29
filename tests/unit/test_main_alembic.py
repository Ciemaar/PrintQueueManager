from unittest.mock import patch

from src.app.main import startup_event


@patch("src.app.main.Base.metadata.create_all")
@patch("alembic.command.upgrade")
@patch("src.app.main.sync_local.delay")
def test_startup_event(mock_sync, mock_upgrade, mock_create):
    """Verify that startup event successfully creates tables, runs migrations, and triggers sync."""
    startup_event()
    mock_create.assert_called_once()
    mock_upgrade.assert_called_once()
    mock_sync.assert_called_once()


@patch("src.app.main.Base.metadata.create_all")
@patch("alembic.command.upgrade", side_effect=Exception("Alembic failed"))
@patch("src.app.main.sync_local.delay", side_effect=Exception("Celery failed"))
def test_startup_event_exceptions(mock_sync, mock_upgrade, mock_create, capfd):
    """Verify that exceptions during alembic or celery sync are gracefully caught and logged."""
    startup_event()
    mock_create.assert_called_once()
    mock_upgrade.assert_called_once()
    mock_sync.assert_called_once()
    out, err = capfd.readouterr()
    assert "Failed to run database migrations: Alembic failed" in out
    assert "Failed to trigger initial sync_local task: Celery failed" in out
