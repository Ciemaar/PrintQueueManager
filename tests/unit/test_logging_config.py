import logging
from unittest.mock import patch

from src.app.logging_config import setup_logging


def test_setup_logging_verbose_true():
    """Test setup_logging with verbose set to True."""
    with patch("src.app.logging_config.settings") as mock_settings:
        mock_settings.verbose = True
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging()
            mock_basic_config.assert_called_once_with(
                level=logging.DEBUG,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )


def test_setup_logging_verbose_false():
    """Test setup_logging with verbose set to False."""
    with patch("src.app.logging_config.settings") as mock_settings:
        mock_settings.verbose = False
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging()
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
