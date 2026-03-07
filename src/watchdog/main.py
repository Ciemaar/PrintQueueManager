import os
import time
from typing import Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy.orm import Session
from src.app.database import SessionLocal, engine
from src.app.models import Base, PrintJob
from src.app.config import settings

class PrintQueueEventHandler(FileSystemEventHandler):
    def on_created(self, event: Any) -> None:
        if not event.is_directory:
            file_path = event.src_path
            filename = os.path.basename(file_path)

            if file_path.endswith(('.stl', '.3mf')):
                print(f"Detected new file: {filename}")
                self._add_to_queue(file_path, filename)

    def _add_to_queue(self, file_path: str, filename: str) -> None:
        db: Session = SessionLocal()
        try:
            # Check if file already exists
            existing_job = db.query(PrintJob).filter(PrintJob.file_path == file_path).first()
            if existing_job:
                print(f"File {filename} is already in the queue.")
                return

            new_job = PrintJob(
                title=filename,
                source="Local",
                file_path=file_path,
                metadata_json={"size_bytes": os.path.getsize(file_path)}
            )
            db.add(new_job)
            db.commit()
            print(f"Added {filename} to print queue.")
        except Exception as e:
            print(f"Failed to add {filename} to queue: {e}")
            db.rollback()
        finally:
            db.close()

def main() -> None:
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)

    path = settings.watch_directory
    if not os.path.exists(path):
        os.makedirs(path)

    event_handler = PrintQueueEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    print(f"Starting Watchdog service on directory: {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
