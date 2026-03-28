"""Command-line interface entry point for launching the Print Queue Manager services."""

import argparse
import sys
import uvicorn

from src.watchdog.main import main as watchdog_main
from src.worker.main import main as worker_main


def start_web() -> None:
    """Launch the FastAPI web server using uvicorn."""
    print("Starting Print Queue Manager Web Server on http://0.0.0.0:8000")
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=False)


def start_watchdog() -> None:
    """Launch the watchdog folder monitoring process."""
    print("Starting Print Queue Manager Watchdog Service...")
    watchdog_main()


def start_worker() -> None:
    """Launch the Temporal worker process."""
    print("Starting Print Queue Manager Temporal Worker...")
    worker_main()


def main() -> None:
    """Parse command line arguments and route to the correct service runner."""
    parser = argparse.ArgumentParser(description="Print Queue Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("web", help="Start the FastAPI web server")
    subparsers.add_parser("watchdog", help="Start the local directory watchdog")
    subparsers.add_parser("worker", help="Start the Temporal worker")

    args = parser.parse_args()

    if args.command == "web":
        start_web()
    elif args.command == "watchdog":
        start_watchdog()
    elif args.command == "worker":
        start_worker()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
