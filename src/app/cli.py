"""Command-line interface entry point for launching the Print Queue Manager services."""

import logging

import click
import uvicorn

from src.app.logging_config import setup_logging
from src.watchdog_service.main import main as watchdog_main

logger = logging.getLogger(__name__)


@click.group()
def main() -> None:
    """Print Queue Manager CLI."""
    setup_logging()


@main.command("web")
def start_web() -> None:
    """Start the FastAPI web server."""
    logger.info("Starting Print Queue Manager Web Server on http://0.0.0.0:8000")
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=False)


@main.command("watchdog")
def start_watchdog() -> None:
    """Start the local directory watchdog."""
    logger.info("Starting Print Queue Manager Watchdog Service...")
    watchdog_main()


if __name__ == "__main__":
    main()
