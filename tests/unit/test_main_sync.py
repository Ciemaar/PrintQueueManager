"""Test module for the manual synchronization trigger endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


@patch("src.worker.dramatiq_app.sync_makerworld.send")
def test_trigger_sync_success(mock_send):
    """Ensure that a valid platform triggers the Dramatiq task and returns a success message."""
    response = client.post("/sync/makerworld")
    assert response.status_code == 200
    assert "Sync started for Makerworld!" in response.text
    mock_send.assert_called_once()


@patch("src.worker.dramatiq_app.sync_local.send")
def test_trigger_sync_local(mock_send):
    """Ensure that the local platform triggers the Dramatiq task and returns a success message."""
    response = client.post("/sync/local")
    assert response.status_code == 200
    assert "Sync started for Local!" in response.text
    mock_send.assert_called_once()


def test_trigger_sync_unknown_platform():
    """Ensure that an invalid platform returns an error message and does not trigger a task."""
    response = client.post("/sync/unknown")
    assert response.status_code == 200
    assert "Unknown platform: unknown" in response.text
