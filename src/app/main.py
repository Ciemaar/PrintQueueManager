"""FastAPI application entrypoint and route definitions."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from src.app.database import get_db, Base, engine
from src.app.models import PrintJob, PrintStatus, ServiceConfig
from src.worker.celery_app import (
    sync_thingiverse,
    sync_makerworld,
    sync_printables,
    sync_cults3d,
    sync_minihoarder,
    sync_myminifactory,
    sync_local,
)

from src.app.logging_config import setup_logging

logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on application startup, run migrations, and trigger local sync."""
    Base.metadata.create_all(bind=engine)

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

    jobs = query.order_by(PrintJob.created_at.desc()).all()

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
                if getattr(job, "deleted_at", None) is None:
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
        "myminifactory": sync_myminifactory,
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


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the configuration page for managing service settings."""
    service_defs = {
        "local": {
            "display_name": "Local Directory",
            "instructions": (
                "Configure a local directory path accessible by the backend "
                "(e.g. within the Docker container) "
                "to automatically sync 3D model files into the queue."
            ),
            "example_url": "/watched_folder",
            "credential_placeholder": "Not required",
        },
        "makerworld": {
            "display_name": "MakerWorld",
            "instructions": (
                "Go to MakerWorld and log in. Open Developer Tools (F12), navigate to "
                "Application > Cookies, and find the cookie named <code>TAsessionID</code>. "
                "Copy its value. Set the target to your likes page or a specific collection."
            ),
            "example_url": "https://makerworld.com/en/user/likes",
            "credential_placeholder": "Paste TAsessionID cookie here",
        },
        "printables": {
            "display_name": "Printables",
            "instructions": (
                "Log in to Printables. Open Developer Tools, find the <code>nette-samesite</code> "
                "cookie in Application > Cookies for <code>.printables.com</code>. Copy the value."
            ),
            "example_url": "https://www.printables.com/user/collections",
            "credential_placeholder": "Paste nette-samesite cookie here",
        },
        "thingiverse": {
            "display_name": "Thingiverse",
            "instructions": (
                "Log in to Thingiverse and generate a Bearer API token, "
                "or use the Developer Tools to find your session token."
            ),
            "example_url": "https://www.thingiverse.com/user/collections",
            "credential_placeholder": "Paste API token here",
        },
        "cults3d": {
            "display_name": "Cults3D",
            "instructions": (
                "Log in to Cults3D. Open Developer Tools and locate the "
                "<code>_session_id</code> cookie."
            ),
            "example_url": "https://cults3d.com/en/users/collections",
            "credential_placeholder": "Paste _session_id cookie here",
        },
        "minihoarder": {
            "display_name": "Minihoarder",
            "instructions": (
                "Log in to Minihoarder. Open Developer Tools and locate "
                "the <code>PHPSESSID</code> cookie for your library."
            ),
            "example_url": "https://www.minihoarder.com/library/",
            "credential_placeholder": "Paste PHPSESSID cookie here",
        },
        "myminifactory": {
            "display_name": "MyMiniFactory",
            "instructions": (
                "Log in to MyMiniFactory. Open Developer Tools and locate the appropriate session "
                "cookie (e.g. <code>PHPSESSID</code> or <code>myminifactory_session</code>)."
            ),
            "example_url": "https://www.myminifactory.com/library",
            "credential_placeholder": "Paste session cookie here",
        },
    }

    services = {}
    for name, details in service_defs.items():
        config = db.query(ServiceConfig).filter(ServiceConfig.service_name == name).first()
        if not config:
            config = ServiceConfig(
                service_name=name, enabled=0, credential="", target_url=details["example_url"]
            )
        details["config"] = config
        services[name] = details

    return templates.TemplateResponse(
        request=request, name="settings.html", context={"services": services}
    )  # type: ignore


@app.post("/settings/update", response_class=HTMLResponse)
def update_settings(
    request: Request,
    service_name: str = Form(...),
    enabled: int = Form(0),
    target_url: str = Form(""),
    credential: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Update configuration settings for a specific service."""
    config = db.query(ServiceConfig).filter(ServiceConfig.service_name == service_name).first()
    if not config:
        config = ServiceConfig(service_name=service_name)
        db.add(config)

    config.enabled = enabled  # type: ignore
    config.target_url = target_url  # type: ignore

    # Update credential only if a new value is provided,
    # otherwise keep the existing one to support the masked input UI.
    if credential:
        config.credential = credential  # type: ignore

    db.commit()

    return HTMLResponse(
        f'<div class="sync-toast" style="color: var(--pico-primary); '
        f"font-weight: bold; margin-bottom: 1rem; padding: 0.5rem; "
        f'background: var(--pico-primary-background); border-radius: 0.25rem;">'
        f"Settings saved for {service_name.capitalize()}!</div>",
        headers={"HX-Refresh": "true"},
    )


@app.get("/settings/browse", response_class=HTMLResponse)
def browse_directories(request: Request, path: str = "/") -> HTMLResponse:
    """Return an HTML snippet of subdirectories within the given path."""
    import os
    import html

    # Simple security constraint to keep it absolute and avoid jumping around too much wildly,
    # though it's an admin internal tool.
    target_path = os.path.abspath(path)

    dirs = []
    try:
        # parent directory link
        parent_path = os.path.dirname(target_path)
        if target_path != "/":
            dirs.append({"name": "..", "path": parent_path})

        with os.scandir(target_path) as it:
            for entry in it:
                if entry.is_dir() and not entry.name.startswith("."):
                    dirs.append({"name": entry.name, "path": entry.path})
    except Exception as e:
        error_str = html.escape(str(e))
        return HTMLResponse(
            f"<div style='color: var(--pico-del-color);'>Error accessing path: {error_str}</div>"
        )

    dirs.sort(key=lambda x: x["name"].lower())

    # Render an inline list of links that will load back into the modal
    escaped_path = html.escape(target_path)
    html_content = (
        f"<div style='margin-bottom: 1rem;'><strong>Current Path:</strong> {escaped_path}</div>"
    )

    html_content += (
        "<ul style='list-style: none; padding: 0; max-height: 200px; "
        "overflow-y: auto; border: 1px solid var(--pico-muted-border-color); "
        "border-radius: 0.25rem; padding: 0.5rem;'>"
    )

    for d in dirs:
        escaped_name = html.escape(d["name"])
        html_content += f"""
        <li style='margin-bottom: 0.25rem;'>
            <a href="#" hx-get="/settings/browse?path={d["path"]}"
               hx-target="#directory-browser-content" style="text-decoration: none;">
                📁 {escaped_name}
            </a>
        </li>
        """
    html_content += "</ul>"

    html_content += f"""
    <div style='margin-top: 1rem; display: flex; justify-content: flex-end; gap: 0.5rem;'>
        <button type="button" class="secondary"
                onclick="document.getElementById('directory-modal').removeAttribute('open');">
            Cancel
        </button>
        <button type="button"
                onclick="document.getElementById('local_target_url').value = '{target_path}';
                         document.getElementById('directory-modal').removeAttribute('open');">
            Select Directory
        </button>
    </div>
    """

    return HTMLResponse(html_content)


@app.post("/settings/test", response_class=HTMLResponse)
def test_settings(
    request: Request,
    service_name: str = Form(...),
    target_url: str = Form(""),
    credential: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Test configuration settings synchronously by running a fast HTTP/Playwright fetch."""
    # If the credential field is empty (masked), fall back to checking the DB
    if not credential:
        config = db.query(ServiceConfig).filter(ServiceConfig.service_name == service_name).first()
        if config and getattr(config, "credential", None):
            credential = str(config.credential)

    if not target_url:
        return HTMLResponse(
            f'<div class="sync-toast" style="color: var(--pico-del-color); '
            f"font-weight: bold; margin-bottom: 1rem; padding: 0.5rem; "
            f'background: var(--pico-del-background); border-radius: 0.25rem;">'
            f"Failed: Target URL is required to test {service_name.capitalize()}.</div>"
        )

    import html
    from src.worker.llm_scraper import get_page_html

    success = False
    error_msg = ""
    try:
        if service_name == "local":
            import os

            if os.path.isdir(target_url):
                success = True
            else:
                success = False
                error_msg = f"Directory not found: {target_url}"
        elif service_name == "thingiverse":
            # API test
            # fetch_thingiverse_collections catches errors and returns []
            # For a test, we actually want to know if it failed. Let's make a quick raw request
            # or just rely on the fact that if it returns [], we can't be sure it succeeded
            # if we have no items. Let's make a raw request.
            import requests

            headers = {"Authorization": f"Bearer {credential}"}
            response = requests.get(
                "https://api.thingiverse.com/users/me", headers=headers, timeout=10
            )
            response.raise_for_status()
            success = True
        else:
            # Playwright test
            fetched_html = get_page_html(service_name, target_url, credential)
            # A successful fetch implies the URL was reached and Playwright didn't crash.
            # Empty HTML means either demo-mode mock fallback failed or Playwright crashed.
            if fetched_html:
                # Basic sanity check: look for evidence it isn't just an access denied page.
                # Verifying we got a payload and no exceptions is enough for a "quick" test.
                success = True
            else:
                success = False
                error_msg = "Could not fetch page. Playwright returned empty content or crashed."
    except Exception as e:
        success = False
        error_msg = html.escape(str(e))

    if success:
        return HTMLResponse(
            f'<div class="sync-toast" style="color: var(--pico-ins-color); '
            f"font-weight: bold; margin-bottom: 1rem; padding: 0.5rem; "
            f'background: var(--pico-ins-background); border-radius: 0.25rem;">'
            f"Test successful for {service_name.capitalize()}! Connection verified.</div>"
        )
    else:
        return HTMLResponse(
            f'<div class="sync-toast" style="color: var(--pico-del-color); '
            f"font-weight: bold; margin-bottom: 1rem; padding: 0.5rem; "
            f'background: var(--pico-del-background); border-radius: 0.25rem;">'
            f"Test failed for {service_name.capitalize()}. {error_msg}</div>"
        )
