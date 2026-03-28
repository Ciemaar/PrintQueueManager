"""Test module for the CLI entry points."""

from unittest.mock import patch
import sys
import pytest
from src.app.cli import main, start_web, start_watchdog, start_worker


@patch("src.app.cli.uvicorn.run")
def test_start_web(mock_run):
    """Ensure start_web calls uvicorn.run."""
    start_web()
    mock_run.assert_called_once()


@patch("src.app.cli.watchdog_main")
def test_start_watchdog(mock_main):
    """Ensure start_watchdog calls watchdog_main."""
    start_watchdog()
    mock_main.assert_called_once()


@patch("src.app.cli.worker_main")
def test_start_worker(mock_main):
    """Ensure start_worker calls worker_main."""
    start_worker()
    mock_main.assert_called_once()


@patch("src.app.cli.start_web")
def test_main_web(mock_start_web):
    """Ensure main routes to start_web correctly."""
    with patch.object(sys, "argv", ["printqueue", "web"]):
        main()
        mock_start_web.assert_called_once()


@patch("src.app.cli.start_watchdog")
def test_main_watchdog(mock_start_watchdog):
    """Ensure main routes to start_watchdog correctly."""
    with patch.object(sys, "argv", ["printqueue", "watchdog"]):
        main()
        mock_start_watchdog.assert_called_once()


@patch("src.app.cli.start_worker")
def test_main_worker(mock_start_worker):
    """Ensure main routes to start_worker correctly."""
    with patch.object(sys, "argv", ["printqueue", "worker"]):
        main()
        mock_start_worker.assert_called_once()


def test_main_invalid():
    """Ensure main exits with 2 (argparse error) on invalid command."""
    with patch.object(sys, "argv", ["printqueue", "invalid"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2


def test_main_no_args():
    """Ensure main exits with 1 on no command."""
    with patch.object(sys, "argv", ["printqueue"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
