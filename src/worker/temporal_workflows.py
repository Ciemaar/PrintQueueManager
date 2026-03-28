"""Temporal workflows and activities for external data sync."""

import time
from datetime import timedelta
from typing import List, Any
from pathlib import Path

from temporalio import activity, workflow

from src.app.config import settings
from src.app.database import SessionLocal
from src.app.models import PrintJob
from .llm_scraper import run_scraper
from .thingiverse_api import fetch_thingiverse_collections

@activity.defn
async def sync_makerworld() -> List[dict[str, Any]]:
    """Fetch the user's liked models from MakerWorld."""
    print("Starting MakerWorld synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@activity.defn
async def sync_printables() -> List[dict[str, Any]]:
    """Fetch the user's collections from Printables."""
    print("Starting Printables synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("printables", "https://www.printables.com/user/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@activity.defn
async def sync_thingiverse() -> List[dict[str, Any]]:
    """Fetch the user's liked models from Thingiverse."""
    print("Starting Thingiverse synchronization via Official API...")
    time.sleep(2)
    result = fetch_thingiverse_collections()
    if not result:
        print("Fallback to Ollama agent for Thingiverse...")
        result = run_scraper("thingiverse", "https://www.thingiverse.com/user/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@activity.defn
async def sync_cults3d() -> List[dict[str, Any]]:
    """Fetch the user's collections from Cults3D."""
    print("Starting Cults3D synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("cults3d", "https://cults3d.com/en/users/collections")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@activity.defn
async def sync_minihoarder() -> List[dict[str, Any]]:
    """Fetch the user's purchased/downloaded library from Minihoarder."""
    print("Starting Minihoarder synchronization via Ollama agent...")
    time.sleep(2)
    result = run_scraper("minihoarder", "https://www.minihoarder.com/library/")
    print(f"Sync complete. Found {len(result)} models.")
    return result

@activity.defn
async def sync_local() -> List[dict[str, Any]]:
    """Scan the local watched directory for models and import any missing files."""
    print(f"Scanning local directory for new models: {settings.watch_directory}")
    watch_path = Path(settings.watch_directory)
    if not watch_path.exists():
        watch_path.mkdir(parents=True, exist_ok=True)

    added_files = []
    db = SessionLocal()
    try:
        if settings.verbose:
            print(f"[VERBOSE] Scanning directory: {watch_path} recursively")

        known_paths = {
            job.file_path for job in db.query(PrintJob.file_path).filter(PrintJob.source == "Local")
        }

        for file_path in watch_path.rglob("*"):
            if (file_path.is_file() or file_path.is_symlink()) and file_path.suffix.lower() in {
                ".stl",
                ".3mf",
            }:
                if str(file_path) in known_paths:
                    continue

                is_broken_symlink = file_path.is_symlink() and not file_path.exists()

                if settings.verbose:
                    status_log = "broken symlink" if is_broken_symlink else "new 3D file"
                    print(f"[VERBOSE] Discovered {status_log}: {file_path.name} at {file_path}")

                file_size = 0 if is_broken_symlink else file_path.stat().st_size
                metadata = {"size_bytes": file_size}
                if is_broken_symlink:
                    metadata["is_broken_symlink"] = True

                new_job = PrintJob(
                    title=file_path.name,
                    source="Local",
                    file_path=str(file_path),
                    metadata_json=metadata,
                )
                db.add(new_job)
                added_files.append({"title": file_path.name, "file_path": str(file_path)})

        if added_files:
            db.commit()
            print(f"Added {len(added_files)} local files to print queue.")
        else:
            print("No new local files discovered.")
    except Exception as e:
        print(f"Error synchronizing local files: {e}")
        db.rollback()
    finally:
        db.close()

    return added_files


@workflow.defn
class SyncMakerworldWorkflow:
    """Workflow to sync Makerworld."""

    @workflow.run
    async def run(self) -> List[dict[str, Any]]:
        """Run the workflow."""
        return await workflow.execute_activity(
            sync_makerworld,
            start_to_close_timeout=timedelta(minutes=10)
        )

@workflow.defn
class SyncPrintablesWorkflow:
    """Workflow to sync Printables."""

    @workflow.run
    async def run(self) -> List[dict[str, Any]]:
        """Run the workflow."""
        return await workflow.execute_activity(
            sync_printables,
            start_to_close_timeout=timedelta(minutes=10)
        )

@workflow.defn
class SyncThingiverseWorkflow:
    """Workflow to sync Thingiverse."""

    @workflow.run
    async def run(self) -> List[dict[str, Any]]:
        """Run the workflow."""
        return await workflow.execute_activity(
            sync_thingiverse,
            start_to_close_timeout=timedelta(minutes=10)
        )

@workflow.defn
class SyncCults3dWorkflow:
    """Workflow to sync Cults3d."""

    @workflow.run
    async def run(self) -> List[dict[str, Any]]:
        """Run the workflow."""
        return await workflow.execute_activity(
            sync_cults3d,
            start_to_close_timeout=timedelta(minutes=10)
        )

@workflow.defn
class SyncMinihoarderWorkflow:
    """Workflow to sync Minihoarder."""

    @workflow.run
    async def run(self) -> List[dict[str, Any]]:
        """Run the workflow."""
        return await workflow.execute_activity(
            sync_minihoarder,
            start_to_close_timeout=timedelta(minutes=10)
        )

@workflow.defn
class SyncLocalWorkflow:
    """Workflow to sync Local."""

    @workflow.run
    async def run(self) -> List[dict[str, Any]]:
        """Run the workflow."""
        return await workflow.execute_activity(
            sync_local,
            start_to_close_timeout=timedelta(minutes=10)
        )
