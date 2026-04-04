"""FastAPI application entrypoint and route definitions."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.app.database import Base, engine, get_db
from src.app.logging_config import setup_logging
from src.app.models import PrintJob, PrintStatus
from src.worker.celery_app import (
    sync_cults3d,
    sync_local,
    sync_makerworld,
    sync_minihoarder,
    sync_printables,
    sync_thingiverse,
)

logger = logging.getLogger(__name__)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on application startup, run migrations, and trigger local sync."""
    # Base.metadata.create_all handles creating new tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Run Alembic migrations programmatically
    try:
        import os

        import alembic.command
        import alembic.config

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        alembic_ini_path = os.path.join(project_root, "alembic.ini")
        alembic_dir = os.path.join(project_root, "alembic")

        alembic_cfg = alembic.config.Config(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", alembic_dir)

        alembic.command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(f"Failed to run database migrations: {e}")

    try:
        sync_local.delay()
    except Exception as e:
        logger.error(f"Failed to trigger initial sync_local task: {e}")

    yield


app = FastAPI(title="Print Queue Manager", lifespan=lifespan)

templates = Jinja2Templates(directory="src/app/templates")


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request, show_printed: bool = False, db: Session = Depends(get_db)
) -> HTMLResponse:
    """Render the main dashboard by fetching non-deleted PrintJobs from the database."""
    query = db.query(PrintJob)

    if show_printed:
        query = query.filter(PrintJob.status.notin_([PrintStatus.SKIPPED, PrintStatus.DELETED]))
    else:
        query = query.filter(
            PrintJob.status.notin_([PrintStatus.PRINTED, PrintStatus.SKIPPED, PrintStatus.DELETED])
        )

    jobs = query.order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()

    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(
            request=request, name="job_list.html", context={"jobs": jobs}
        )  # type: ignore

    return templates.TemplateResponse(
        request=request, name="index.html", context={"jobs": jobs, "show_printed": show_printed}
    )  # type: ignore


@app.get("/deleted", response_class=HTMLResponse)
def deleted_jobs(
    request: Request,
    show_printed: bool = False,
    show_skipped: bool = False,
    show_deleted: bool = False,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Render the deleted jobs view, filtered by type."""
    # If this is the initial page load (not an HTMX request), default to showing everything
    is_htmx = request.headers.get("hx-request") == "true"
    if not is_htmx and not request.query_params:
        show_printed = True
        show_skipped = True
        show_deleted = True

    query = db.query(PrintJob)

    status_filters = []
    if show_printed:
        status_filters.append(PrintStatus.PRINTED)
    if show_skipped:
        status_filters.append(PrintStatus.SKIPPED)
    if show_deleted:
        status_filters.append(PrintStatus.DELETED)

    if not status_filters:
        jobs = []
    else:
        jobs = (
            query.filter(PrintJob.status.in_(status_filters))
            .order_by(PrintJob.deleted_at.desc().nullslast())
            .all()
        )

    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(
            request=request, name="deleted_job_list.html", context={"jobs": jobs}
        )  # type: ignore

    return templates.TemplateResponse(
        request=request,
        name="deleted_jobs.html",
        context={
            "jobs": jobs,
            "show_printed": show_printed,
            "show_skipped": show_skipped,
            "show_deleted": show_deleted,
        },
    )  # type: ignore


def _normalize_priorities_sync(db: Session) -> None:
    """
    Normalize the user_priority values for all active PrintJobs synchronously.

    This is called when a priority collision is detected during drag-and-drop reordering.
    """
    jobs = (
        db.query(PrintJob)
        .filter(PrintJob.status != PrintStatus.DELETED)
        .order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc())
        .all()
    )

    for index, j in enumerate(jobs, start=1):
        setattr(j, "user_priority", float(index))

    db.commit()


@app.post("/jobs/{job_id}/reorder", response_class=HTMLResponse)
def reorder_job(
    job_id: int,
    request: Request,
    above_id: Optional[int] = Form(None),
    below_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Update the priority of a specific job via drag-and-drop.

    Accepts the IDs of the jobs above and below the new position to calculate
    a new user_priority float value. If the gap between items is too small or
    a collision exists, forces a sync normalization to guarantee distinct ordering.
    """
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if not job:
        return HTMLResponse(status_code=404)

    # Fetch reference jobs
    above_job = db.query(PrintJob).filter(PrintJob.id == above_id).first() if above_id else None
    below_job = db.query(PrintJob).filter(PrintJob.id == below_id).first() if below_id else None

    # Detect priority collisions or inversions that prevent calculating a midpoint
    if above_job and below_job:
        above_priority = getattr(above_job, "user_priority")
        below_priority = getattr(below_job, "user_priority")

        # If priorities are identical or inverted, normalize the entire list first
        if above_priority >= below_priority:
            _normalize_priorities_sync(db)
            db.refresh(above_job)
            db.refresh(below_job)

    # Re-calculate with normalized (or distinct) values
    if above_job and below_job:
        above_priority = getattr(above_job, "user_priority")
        below_priority = getattr(below_job, "user_priority")
        setattr(job, "user_priority", (above_priority + below_priority) / 2.0)
    elif above_job:
        above_priority = getattr(above_job, "user_priority")
        setattr(job, "user_priority", above_priority + 1.0)
    elif below_job:
        below_priority = getattr(below_job, "user_priority")
        setattr(job, "user_priority", below_priority - 1.0)

    # Note: If both are None, this is either a single-item list or an error.
    # The job remains at its current priority.

    db.commit()
    return HTMLResponse("")


@app.post("/jobs/{job_id}/delete", response_class=HTMLResponse)
def delete_job(job_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """
    Mark a job as DELETED.

    Instead of hard-deleting the row, this soft-deletes the job by updating its status,
    removing it from the active UI while preserving historical data.
    Returns an empty string for HTMX to remove the target HTML row dynamically.
    """
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        job.status = PrintStatus.DELETED  # type: ignore
        job.deleted_at = datetime.utcnow()  # type: ignore
        db.commit()
    return HTMLResponse("")


@app.post("/jobs/{job_id}/undelete", response_class=HTMLResponse)
def undelete_job(job_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """
    Restore a deleted job.

    If it was PRINTED, it becomes PRINT AGAIN.
    Otherwise (SKIPPED or DELETED), it becomes TO BE PRINTED.
    Returns an empty string to remove it from the deleted jobs view via HTMX.
    """
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        if job.status is PrintStatus.PRINTED or getattr(job, "status") == PrintStatus.PRINTED:
            job.status = PrintStatus.PRINT_AGAIN  # type: ignore
        elif getattr(job, "status") in [PrintStatus.SKIPPED, PrintStatus.DELETED]:
            job.status = PrintStatus.TO_BE_PRINTED  # type: ignore

        job.deleted_at = None  # type: ignore
        db.commit()
    return HTMLResponse("")


@app.post("/jobs/{job_id}/status", response_class=HTMLResponse)
def update_status(
    job_id: int, request: Request, status: str = Form(...), db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Update the printing status of a specific job.

    Accepts the new status state via form submission (triggered by HTMX onChange),
    updates the database, and returns the re-rendered template row to seamlessly
    update the UI without a full page refresh.
    """
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        try:
            enum_status = PrintStatus(status)
            job.status = enum_status  # type: ignore
            if enum_status in [PrintStatus.PRINTED, PrintStatus.SKIPPED, PrintStatus.DELETED]:
                if job.deleted_at is None:
                    job.deleted_at = datetime.utcnow()  # type: ignore
            else:
                job.deleted_at = None  # type: ignore
            db.commit()
        except ValueError:
            pass  # Invalid status submitted
        return templates.TemplateResponse(
            request=request, name="job_row.html", context={"job": job}
        )  # type: ignore
    return HTMLResponse("")


@app.post("/jobs/{job_id}/notes", response_class=HTMLResponse)
def update_notes(
    job_id: int,
    request: Request,
    material_notes: str = Form(""),
    timing_notes: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Update the material and timing notes of a print job.

    Triggered dynamically via HTMX when the user blurs away from the input fields.
    Does not rerender the row, just acknowledges the save.
    """
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        job.material_notes = material_notes  # type: ignore
        job.timing_notes = timing_notes  # type: ignore
        db.commit()
        return HTMLResponse("Saved")
    return HTMLResponse("")


@app.post("/sync/{platform}", response_class=HTMLResponse)
def trigger_sync(platform: str) -> HTMLResponse:
    """Manually trigger a background Celery task to synchronize a specific platform."""
    tasks = {
        "makerworld": sync_makerworld,
        "printables": sync_printables,
        "thingiverse": sync_thingiverse,
        "cults3d": sync_cults3d,
        "minihoarder": sync_minihoarder,
        "local": sync_local,
    }

    task = tasks.get(platform.lower())
    if task:
        task.delay()
        msg = f"Sync started for {platform.capitalize()}!"
        return HTMLResponse(
            f'<div class="sync-toast" style="color: var(--pico-primary); '
            f'font-weight: bold; margin-bottom: 1rem;">{msg}</div>'
        )
    return HTMLResponse(
        f'<div class="sync-toast" style="color: var(--pico-del-color); '
        f'font-weight: bold; margin-bottom: 1rem;">Unknown platform: {platform}</div>'
    )
