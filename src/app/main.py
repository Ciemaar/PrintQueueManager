from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.app.database import get_db, Base, engine
from src.app.models import PrintJob

app = FastAPI(title="Print Queue Manager")

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="src/app/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    # Filter out DELETED jobs from the main view
    jobs = db.query(PrintJob).filter(PrintJob.status != 'DELETED').order_by(PrintJob.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs}) # type: ignore

@app.post("/jobs/{job_id}/delete", response_class=HTMLResponse)
def delete_job(job_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        # Instead of deleting from DB, mark as DELETED per new requirements
        job.status = "DELETED"
        db.commit()
    return HTMLResponse("")

@app.post("/jobs/{job_id}/status", response_class=HTMLResponse)
def update_status(job_id: int, request: Request, status: str = Form(...), db: Session = Depends(get_db)) -> HTMLResponse:
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        job.status = status
        db.commit()
        return templates.TemplateResponse("job_row.html", {"request": request, "job": job}) # type: ignore
    return HTMLResponse("")

@app.post("/jobs/{job_id}/notes", response_class=HTMLResponse)
def update_notes(job_id: int, request: Request, material_notes: str = Form(""), timing_notes: str = Form(""), db: Session = Depends(get_db)) -> HTMLResponse:
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        job.material_notes = material_notes
        job.timing_notes = timing_notes
        db.commit()
        return HTMLResponse("Saved")
    return HTMLResponse("")
