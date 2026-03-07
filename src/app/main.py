from fastapi import FastAPI, Request, Depends
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
    jobs = db.query(PrintJob).order_by(PrintJob.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs}) # type: ignore

@app.post("/jobs/{job_id}/delete", response_class=HTMLResponse)
def delete_job(job_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        db.delete(job)
        db.commit()
    return HTMLResponse("")

@app.post("/jobs/{job_id}/toggle", response_class=HTMLResponse)
def toggle_job(job_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if job:
        job.is_printed = not job.is_printed
        db.commit()
        return templates.TemplateResponse("job_row.html", {"request": request, "job": job}) # type: ignore
    return HTMLResponse("")
