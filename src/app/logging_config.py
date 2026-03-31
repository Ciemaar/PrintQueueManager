"""Centralized logging configuration for Print Queue Manager."""

import logging

from src.app.config import settings


def setup_logging() -> None:
    """
    Configure the root logger for the application.

    Sets the log level based on the `settings.verbose` flag.
    """
    level = logging.DEBUG if settings.verbose else logging.INFO

    # Configure the basic settings for the root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
