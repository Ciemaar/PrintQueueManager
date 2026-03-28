"""Test module for the manual synchronization trigger endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

@pytest.fixture
def mock_temporal_client():
    """Mock the Temporal client."""
    with patch("src.app.main.get_temporal_client", new_callable=AsyncMock) as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        yield mock_client

def test_trigger_sync_success(mock_temporal_client):
    """Ensure that a valid platform triggers the Temporal workflow and returns a success message."""
    response = client.post("/sync/makerworld")
    assert response.status_code == 200
    assert "Sync started for Makerworld!" in response.text
    mock_temporal_client.start_workflow.assert_called_once()

def test_trigger_sync_local(mock_temporal_client):
    """Ensure that the local platform triggers the Temporal workflow."""
    response = client.post("/sync/local")
    assert response.status_code == 200
    assert "Sync started for Local!" in response.text
    mock_temporal_client.start_workflow.assert_called_once()

def test_trigger_sync_unknown_platform(mock_temporal_client):
    """Ensure that an invalid platform returns an error message and does not trigger a workflow."""
    response = client.post("/sync/unknown")
    assert response.status_code == 200
    assert "Unknown platform: unknown" in response.text
    mock_temporal_client.start_workflow.assert_not_called()
