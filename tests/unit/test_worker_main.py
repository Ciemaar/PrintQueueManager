"""Test module for the Temporal Worker main entrypoint."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from src.worker.main import run_worker, setup_schedules, main
from temporalio.client import Client

@pytest.mark.asyncio
@patch("src.worker.main.Client.connect")
@patch("src.worker.main.Worker")
async def test_run_worker(mock_worker_cls, mock_connect):
    """Ensure run_worker connects to Temporal and starts the worker."""
    mock_client = AsyncMock(spec=Client)
    mock_connect.return_value = mock_client

    mock_worker_instance = MagicMock()
    mock_worker_instance.run = AsyncMock()
    mock_worker_cls.return_value = mock_worker_instance

    await run_worker()

    mock_connect.assert_called_once()
    mock_worker_cls.assert_called_once()
    mock_worker_instance.run.assert_called_once()

@pytest.mark.asyncio
async def test_setup_schedules():
    """Ensure setup_schedules creates schedules correctly."""
    mock_client = AsyncMock(spec=Client)
    await setup_schedules(mock_client)
    assert mock_client.create_schedule.call_count == 5

@pytest.mark.asyncio
async def test_setup_schedules_already_exists():
    """Ensure setup_schedules handles AlreadyExists exception."""
    mock_client = AsyncMock(spec=Client)
    mock_client.create_schedule.side_effect = Exception("Schedule AlreadyExists")
    await setup_schedules(mock_client)
    assert mock_client.create_schedule.call_count == 5

@pytest.mark.asyncio
async def test_setup_schedules_other_error():
    """Ensure setup_schedules handles arbitrary exceptions."""
    mock_client = AsyncMock(spec=Client)
    mock_client.create_schedule.side_effect = Exception("Some other error")
    await setup_schedules(mock_client)
    assert mock_client.create_schedule.call_count == 5

@patch("src.worker.main.asyncio.run")
def test_main(mock_asyncio_run):
    """Ensure main calls asyncio.run."""
    main()
    mock_asyncio_run.assert_called_once()
