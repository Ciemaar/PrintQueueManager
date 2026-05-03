"""Unit tests for the command-line interface."""

from unittest.mock import patch

from click.testing import CliRunner

from src.app.cli import main


def test_start_web_command():
    """Verify that the 'web' command starts the uvicorn server and sets up logging."""
    runner = CliRunner()
    with patch("src.app.cli.uvicorn.run") as mock_run:
        with patch("src.app.cli.setup_logging") as mock_setup_logging:
            result = runner.invoke(main, ["web"])
            assert result.exit_code == 0
            mock_setup_logging.assert_called_once()
            mock_run.assert_called_once_with(
                "src.app.main:app", host="0.0.0.0", port=8000, reload=False
            )


def test_start_watchdog_command():
    """Verify that the 'watchdog' command delegates to the watchdog service and sets up logging."""
    runner = CliRunner()
    with patch("src.app.cli.watchdog_main") as mock_watchdog_main:
        with patch("src.app.cli.setup_logging") as mock_setup_logging:
            result = runner.invoke(main, ["watchdog"])
            assert result.exit_code == 0
            mock_setup_logging.assert_called_once()
            mock_watchdog_main.assert_called_once()
