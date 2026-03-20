"""FastAPI application entrypoint and route definitions."""

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.app.database import get_db, Base, engine
from src.app.models import PrintJob, PrintStatus

app = FastAPI(title="Print Queue Manager")


@app.on_event("startup")
def startup_event():
    """Create database tables on application startup."""
    Base.metadata.create_all(bind=engine)


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
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})  # type: ignore


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
        return templates.TemplateResponse("job_row.html", {"request": request, "job": job})  # type: ignore
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
