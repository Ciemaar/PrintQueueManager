"""FastAPI application entrypoint and route definitions."""

from typing import Any
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.app.database import get_db, Base, engine
from src.app.models import PrintJob, PrintStatus
from src.app.temporal_client import get_temporal_client
from src.worker.temporal_workflows import (
    SyncMakerworldWorkflow,
    SyncPrintablesWorkflow,
    SyncThingiverseWorkflow,
    SyncCults3dWorkflow,
    SyncMinihoarderWorkflow,
    SyncLocalWorkflow,
)

app = FastAPI(title="Print Queue Manager")


@app.on_event("startup")
async def startup_event() -> None:
    """Create database tables on application startup and trigger local sync."""
    Base.metadata.create_all(bind=engine)
    try:
        client = await get_temporal_client()
        await client.execute_workflow(
            SyncLocalWorkflow.run,
            id="sync-local-startup",
            task_queue="sync-task-queue",
        )
    except Exception as e:
        print(f"Failed to trigger initial SyncLocalWorkflow: {e}")


templates = Jinja2Templates(directory="src/app/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the main dashboard by fetching all non-deleted PrintJobs from the database."""
    jobs = (
        db.query(PrintJob)
        .filter(PrintJob.status != PrintStatus.DELETED)
        .order_by(PrintJob.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(request=request, name="index.html", context={"jobs": jobs})  # type: ignore


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
async def trigger_sync(platform: str) -> HTMLResponse:
    """Manually trigger a background Temporal workflow to synchronize a specific platform."""
    workflows: dict[str, Any] = {
        "makerworld": SyncMakerworldWorkflow,
        "printables": SyncPrintablesWorkflow,
        "thingiverse": SyncThingiverseWorkflow,
        "cults3d": SyncCults3dWorkflow,
        "minihoarder": SyncMinihoarderWorkflow,
        "local": SyncLocalWorkflow,
    }

    workflow_cls = workflows.get(platform.lower())
    if workflow_cls:
        try:
            client = await get_temporal_client()
            import uuid
            await client.start_workflow(
                workflow_cls.run,
                id=f"sync-{platform.lower()}-{uuid.uuid4()}",
                task_queue="sync-task-queue",
            )
            msg = f"Sync started for {platform.capitalize()}!"
            return HTMLResponse(
                f'<div class="sync-toast" style="color: var(--pico-primary); '
                f'font-weight: bold; margin-bottom: 1rem;">{msg}</div>'
            )
        except Exception as e:
            return HTMLResponse(
                f'<div class="sync-toast" style="color: var(--pico-del-color); '
                f'font-weight: bold; margin-bottom: 1rem;">Error: {e}</div>'
            )
    return HTMLResponse(
        f'<div class="sync-toast" style="color: var(--pico-del-color); '
        f'font-weight: bold; margin-bottom: 1rem;">Unknown platform: {platform}</div>'
    )
