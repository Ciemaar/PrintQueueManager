"""Watchdog service to monitor local directories for new 3D model files."""

from typing import Any
import os
import time

import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy.orm import Session

from src.app.database import SessionLocal, engine
from src.app.models import Base, PrintJob
from src.app.config import settings
from src.app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class PrintQueueEventHandler(FileSystemEventHandler):
    """
    Event handler that detects newly created files in a watched directory.

    Specifically looks for `.stl` or `.3mf` files and inserts them into the
    PostgreSQL tracking database so they appear on the local web dashboard.
    """

    def on_created(self, event: Any) -> None:
        """Trigger when a new object is created in the watched filesystem path."""
        logger.debug(f"Watchdog event received: {event.event_type} on {event.src_path}")

        if not event.is_directory:
            file_path = event.src_path
            filename = os.path.basename(file_path)

            if file_path.lower().endswith((".stl", ".3mf")):
                is_broken_symlink = os.path.islink(file_path) and not os.path.exists(file_path)

                status_log = "broken symlink" if is_broken_symlink else "valid 3D file"
                logger.debug(f"Detected {status_log}: {filename}")
                logger.info(f"Detected new file: {filename}")
                self._add_to_queue(file_path, filename, is_broken_symlink)
            else:
                logger.debug(f"Ignored non-3D file: {filename}")
        else:
            logger.debug(f"Ignored directory creation: {event.src_path}")

    def _add_to_queue(self, file_path: str, filename: str, is_broken_symlink: bool = False) -> None:
        """
        Insert the discovered local file into the PostgreSQL queue.

        Ensures the file isn't already present by checking its exact file path
        before inserting a new PrintJob record. Also calculates and stores the
        file size in bytes in the flexible JSONB metadata column.
        """
        db: Session = SessionLocal()
        try:
            # Check if file already exists
            existing_job = db.query(PrintJob).filter(PrintJob.file_path == file_path).first()
            if existing_job:
                logger.info(f"File {filename} is already in the queue.")
                return

            file_size = 0 if is_broken_symlink else os.path.getsize(file_path)
            metadata = {"size_bytes": file_size}
            if is_broken_symlink:
                metadata["is_broken_symlink"] = True

            new_job = PrintJob(
                title=filename,
                source="Local",
                file_path=file_path,
                metadata_json=metadata,
            )
            db.add(new_job)
            db.commit()
            logger.info(f"Added {filename} to print queue.")
        except Exception as e:
            logger.error(f"Failed to add {filename} to queue: {e}")
            db.rollback()
        finally:
            db.close()


def main() -> None:
    """
    Start the continuous watchdog monitoring service.

    Will initialize the database tables if they do not exist, create the
    target watch directory if missing, and block the main thread indefinitely
    while listening for OS filesystem events.
    """
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)

    path = settings.watch_directory
    if not os.path.exists(path):
        os.makedirs(path)

    event_handler = PrintQueueEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    logger.info(f"Starting Watchdog service on directory: {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
