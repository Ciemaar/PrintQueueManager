"""FastAPI application entrypoint and route definitions."""

import html
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.app.database import Base, SessionLocal, engine, get_db
from src.app.logging_config import setup_logging
from src.app.models import PrintJob, PrintStatus, ServiceConfig
from src.worker.celery_app import (
    sync_cults3d,
    sync_local,
    sync_makerworld,
    sync_minihoarder,
    sync_printables,
    sync_thingiverse,
)

SKIPPED_OR_DELETED = frozenset({PrintStatus.SKIPPED, PrintStatus.DELETED})
PRINTED_SKIPPED_DELETED = frozenset({PrintStatus.PRINTED, PrintStatus.SKIPPED, PrintStatus.DELETED})  # noqa: E501

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

    # Normalize priorities synchronously so the first page load has valid integer sorting
    try:
        db = SessionLocal()
        _normalize_priorities_sync(db)
        db.close()
    except Exception as e:
        logger.error(f"Failed to normalize priorities during startup: {e}")

    try:
        sync_local.delay()
    except Exception as e:
        logger.error(f"Failed to trigger initial sync_local task: {e}")

    yield


app = FastAPI(title="Print Queue Manager", lifespan=lifespan)

current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request, show_printed: bool = False, db: Session = Depends(get_db)
) -> HTMLResponse:
    """Render the main dashboard by fetching non-deleted PrintJobs from the database."""
    jobs = PrintJob.get_active_jobs(db, show_printed)

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

    jobs = PrintJob.get_deleted_jobs(db, show_printed, show_skipped, show_deleted)

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
    jobs = PrintJob.get_jobs_for_normalization(db)

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
    job = PrintJob.get_by_id(db, job_id)
    if not job:
        return HTMLResponse(status_code=404)

    # Fetch reference jobs
    above_job = PrintJob.get_by_id(db, above_id) if above_id else None
    below_job = PrintJob.get_by_id(db, below_id) if below_id else None

    # Detect priority collisions or inversions that prevent calculating a midpoint
    if above_job and below_job:
        above_priority = float(getattr(above_job, "user_priority"))
        below_priority = float(getattr(below_job, "user_priority"))

        # If priorities are identical or inverted, normalize the entire list first
        if above_priority >= below_priority:
            _normalize_priorities_sync(db)
            db.refresh(above_job)
            db.refresh(below_job)

    # Re-calculate with normalized (or distinct) values
    new_priority = float(getattr(job, "user_priority"))

    if above_job and below_job:
        above_priority = float(getattr(above_job, "user_priority"))
        below_priority = float(getattr(below_job, "user_priority"))
        new_priority = (above_priority + below_priority) / 2.0
    elif above_job:
        above_priority = float(getattr(above_job, "user_priority"))
        new_priority = above_priority + 1.0
    elif below_job:
        below_priority = float(getattr(below_job, "user_priority"))
        new_priority = below_priority - 1.0

    # Note: If both are None, this is either a single-item list or an error.
    # The job remains at its current priority.

    setattr(job, "user_priority", new_priority)
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
    job = PrintJob.get_by_id(db, job_id)
    if job:
        job.status = PrintStatus.DELETED  # type: ignore
        job.deleted_at = datetime.now(timezone.utc)  # type: ignore
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
    job = PrintJob.get_by_id(db, job_id)
    if job:
        if job.status is PrintStatus.PRINTED or getattr(job, "status") == PrintStatus.PRINTED:
            job.status = PrintStatus.PRINT_AGAIN  # type: ignore
        elif getattr(job, "status") in SKIPPED_OR_DELETED:
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
    job = PrintJob.get_by_id(db, job_id)
    if job:
        try:
            enum_status = PrintStatus(status)
            job.status = enum_status  # type: ignore
            if enum_status in PRINTED_SKIPPED_DELETED:
                if job.deleted_at is None:
                    job.deleted_at = datetime.now(timezone.utc)  # type: ignore
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
    job = PrintJob.get_by_id(db, job_id)
    if job:
        job.material_notes = material_notes  # type: ignore
        job.timing_notes = timing_notes  # type: ignore
        db.commit()
        return HTMLResponse("Saved")
    return HTMLResponse("")


@app.post("/sync/{platform}", response_class=HTMLResponse)
def trigger_sync(request: Request, platform: str) -> HTMLResponse:
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
        return templates.TemplateResponse(  # type: ignore
            request=request, name="sync_toast.html", context={"message": msg, "is_error": False}
        )
    return templates.TemplateResponse(  # type: ignore
        request=request,
        name="sync_toast.html",
        context={"message": f"Unknown platform: {platform}", "is_error": True},
    )


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the configuration settings page for all platform integrations."""
    service_defs = {
        "local": {
            "display_name": "Local Directory",
            "instructions": "Specify an absolute path to a local directory containing 3D models.",
            "example_url": "/path/to/your/3d_models",
            "credential_placeholder": "Not required",
        },
        "makerworld": {
            "display_name": "MakerWorld",
            "instructions": (
                "Log in to MakerWorld. Open Developer Tools (F12) > Application > Cookies, "
                "and locate the <code>TAsessionID</code> cookie."
            ),
            "example_url": "https://makerworld.com/en/u/username/collections",
            "credential_placeholder": "Paste TAsessionID cookie here",
        },
        "printables": {
            "display_name": "Printables",
            "instructions": (
                "Log in to Printables. Open Developer Tools and locate the "
                "<code>__Host-next-auth.csrf-token</code> cookie."
            ),
            "example_url": "https://www.printables.com/user/collections",
            "credential_placeholder": "Paste csrf-token cookie here",
        },
        "thingiverse": {
            "display_name": "Thingiverse",
            "instructions": (
                "For robust scraping, provide an official API token. If omitted, the tool "
                "will fallback to an LLM-based web scraper."
            ),
            "example_url": "https://www.thingiverse.com/username/collections",
            "credential_placeholder": "Optional: Paste API Token here",
        },
        "cults3d": {
            "display_name": "Cults3D",
            "instructions": (
                "Log in to Cults3D. Open Developer Tools and locate the "
                "<code>_cults_session</code> cookie."
            ),
            "example_url": "https://cults3d.com/en/users/collections",
            "credential_placeholder": "Paste _cults_session cookie here",
        },
        "minihoarder": {
            "display_name": "Minihoarder",
            "instructions": (
                "Log in to Minihoarder. Open Developer Tools and locate the "
                "<code>wordpress_logged_in_xyz</code> cookie."
            ),
            "example_url": "https://www.minihoarder.com/library/",
            "credential_placeholder": "Paste wordpress_logged_in cookie here",
        },
        "myminifactory": {
            "display_name": "MyMiniFactory",
            "instructions": (
                "Log in to MyMiniFactory. Open Developer Tools and locate the "
                "<code>myminifactory_session</code> cookie."
            ),
            "example_url": "https://www.myminifactory.com/library",
            "credential_placeholder": "Paste session cookie here",
        },
    }

    # Fetch all existing configs from DB
    configs = db.query(ServiceConfig).all()
    config_map = {str(c.service_name): c for c in configs}

    # Merge static definitions with dynamic DB config state
    for s_name, s_def in service_defs.items():
        s_def["config"] = config_map.get(s_name, ServiceConfig())  # type: ignore

    return templates.TemplateResponse(
        request=request, name="settings.html", context={"services": service_defs}
    )



@app.post("/settings/update", response_class=HTMLResponse)
def update_settings(
    request: Request,
    service_name: str = Form(...),
    enabled: int = Form(0),
    target_url: str = Form(None),
    credential: str = Form(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Update configuration details for a specific service."""
    config = db.query(ServiceConfig).filter(ServiceConfig.service_name == service_name).first()

    if not config:
        config = ServiceConfig(service_name=service_name)
        db.add(config)

    config.enabled = enabled  # type: ignore
    if target_url:
        config.target_url = target_url  # type: ignore
    if credential:
        config.credential = credential  # type: ignore

    db.commit()

    return HTMLResponse(
        f'<div style="color: var(--pico-ins-color); font-weight: bold;">'
        f"Settings saved for {html.escape(service_name).capitalize()}!</div>"
    )


@app.post("/settings/test", response_class=HTMLResponse)
def test_settings(
    request: Request,
    service_name: str = Form(...),
    target_url: str = Form(None),
    credential: str = Form(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Run a live connection test for a configured service."""
    if not target_url:
        return HTMLResponse(
            '<div style="color: var(--pico-del-color);">Target URL is required.</div>'
        )

    try:
        if service_name == "local":
            import os

            if os.path.isdir(target_url):
                return HTMLResponse(
                    f'<div style="color: var(--pico-ins-color);">Test successful! Directory found.</div><span id="status-indicator-{html.escape(service_name)}" hx-swap-oob="true">✅</span>'  # noqa: E501
                )
            else:
                return HTMLResponse(
                    f'<div style="color: var(--pico-del-color);">Test failed: Directory not found: {html.escape(target_url)}</div><span id="status-indicator-{html.escape(service_name)}" hx-swap-oob="true">❌</span>'  # noqa: E501
                )
        elif service_name == "thingiverse":
            import requests

            response = requests.get(target_url)
            if response.status_code == 200:
                return HTMLResponse(
                    '<div style="color: var(--pico-ins-color);">Test successful for Thingiverse!</div><span id="status-indicator-thingiverse" hx-swap-oob="true">✅</span>'  # noqa: E501
                )
            return HTMLResponse(
                f'<div style="color: var(--pico-del-color);">Test failed for Thingiverse. Status: {response.status_code}</div><span id="status-indicator-thingiverse" hx-swap-oob="true">❌</span>'  # noqa: E501
            )
        else:
            # Note: We must import run_scraper inline because celery_app.py relies on
            # PrintJob models, and importing it at the module level creates a circular
            # import loop with llm_scraper -> celery_app -> main.
            from src.worker.llm_scraper import run_scraper

            if not credential:
                config = (
                    db.query(ServiceConfig)
                    .filter(ServiceConfig.service_name == service_name)
                    .first()  # noqa: E501
                )
                if config and getattr(config, "credential"):
                    credential = getattr(config, "credential")

            # Run a limited test fetch to verify connectivity
            run_scraper(service_name, target_url)  # type: ignore

            return HTMLResponse(
                f'<div style="color: var(--pico-ins-color);">Test successful for {html.escape(service_name).capitalize()}!</div><span id="status-indicator-{html.escape(service_name)}" hx-swap-oob="true">✅</span>'  # noqa: E501
            )

    except Exception as e:
        logger.exception(f"Settings test failed for {service_name}")
        return HTMLResponse(
            f'<div style="color: var(--pico-del-color);">Test failed: {html.escape(str(e))}</div><span id="status-indicator-{html.escape(service_name)}" hx-swap-oob="true">❌</span>'  # noqa: E501
        )


@app.get("/settings/browse", response_class=HTMLResponse)
def browse_directories(path: str = "/") -> HTMLResponse:
    """Browse local filesystem directories for the UI path picker."""
    import os

    try:
        path = os.path.abspath(path)
        parent_dir = os.path.dirname(path) if path != "/" else None

        directories = []
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir() and not entry.name.startswith("."):
                    directories.append((entry.name, entry.path))

        directories.sort(key=lambda x: x[0].lower())

        html_parts = []
        html_parts.append(
            f'<div style="margin-bottom: 1rem;"><strong>Current:</strong> {html.escape(path)}</div>'  # noqa: E501
        )
        html_parts.append(
            f"<div style=\"margin-bottom: 1rem;\"><button type=\"button\" class=\"outline\" onclick=\"document.getElementById('local_target_url').value='{html.escape(path)}'; document.getElementById('directory-modal').removeAttribute('open')\">Select This Directory</button></div>"  # noqa: E501
        )

        html_parts.append('<ul style="list-style-type: none; padding: 0;">')
        if parent_dir:
            html_parts.append(
                f'<li style="margin-bottom: 0.5rem;"><a href="#" hx-get="/settings/browse?path={parent_dir}" hx-target="#directory-browser-content">📁 ..</a></li>'  # noqa: E501
            )

        for name, dir_path in directories:
            html_parts.append(
                f'<li style="margin-bottom: 0.5rem;"><a href="#" hx-get="/settings/browse?path={dir_path}" hx-target="#directory-browser-content">📁 {html.escape(name)}</a></li>'  # noqa: E501
            )

        html_parts.append("</ul>")
        return HTMLResponse("".join(html_parts))

    except Exception as e:
        return HTMLResponse(
            f'<div style="color: var(--pico-del-color);">Error accessing path: {html.escape(str(e))}</div>'  # noqa: E501
        )
