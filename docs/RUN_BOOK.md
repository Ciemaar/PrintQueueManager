# Comprehensive Run Book

This document provides clear, role-based instructions for running, operating, and extending the Print Queue Manager.

---

## 1. End User Guide

_If you are simply using the system to track your 3D printing pipeline._

**Accessing the System:**
Navigate your web browser to the configured host (e.g., `http://localhost:8000`). You will see a combined list of all 3D models waiting to be printed.

**Managing Jobs:**

- **Add Local Files:** Simply drag-and-drop or save your `.stl` or `.3mf` files into the designated `watched_folder` directory on your computer or NAS. They will automatically appear on the dashboard in seconds. Symlinks are supported but they must point to files that exist and are accessible from within the container context. Broken symlinks will be flagged as such in the system.
- **Change Status:** Use the dropdown in the 'Status' column to select between `TO BE PRINTED`, `PRINT IN PROGRESS`, `PRINT AGAIN`, `PRINTED`, and `SKIPPED`.
- **Take Notes:** Add information about which filament you want to use in the `Material` box, or how long the slice says it takes in the `Timing` box. Changes are saved the moment you click away.
- **Remove Jobs:** Click the red `Delete` button to permanently mark a job as removed from the active queue.

_(For detailed info on how the system automatically scrapes sites like Printables and MakerWorld, see `USER_GUIDE.md`)_.

---

## 2. Operator & Administrator Guide

_If you are deploying, monitoring, or managing the production infrastructure._

The system is deployed using `docker compose`. It consists of an orchestrator for a PostgreSQL database, a Redis cache, an Ollama LLM server, the FastAPI backend, a Dramatiq worker, a Dramatiq beat scheduler, and a file watchdog.

**Startup:**

```bash
docker compose up -d --build
```

**First-Time Setup (Crucial):**
The background worker requires a local LLM to parse raw HTML from unsupported websites. Once the system is running, you must download the `llama3.2` model into the Ollama container:

```bash
docker compose exec ollama ollama pull llama3.2
```

**Monitoring and Logs:**
If a user complains that models from a specific website aren't syncing, check the logs of the background worker:

```bash
docker compose logs -f worker
```

To check if the periodic tasks are actually firing every 30 minutes, check the scheduler logs:

```bash
docker compose logs -f beat
```

**Shutdown:**

```bash
docker compose down
```

_Note: This command shuts down the containers but preserves your database volumes so your print queue is not lost._

---

## 3. Developer Guide

_If you are writing code, modifying the UI, or adding new websites to scrape._

**Local Setup:**
We recommend developing locally on your host machine while pointing to the Docker containers for the database and Redis cache.

1. Ensure Python 3.10+ is installed.
2. Set up a virtual environment (e.g. using `pyenv` or `python3 -m venv`):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Install Playwright system dependencies (required for the headless browser testing):
   ```bash
   playwright install --with-deps chromium
   ```

**Running Components Locally:**
Ensure you stop any conflicting Docker containers (e.g., `docker compose stop worker web watchdog`) if you intend to run those components locally, otherwise you may face port conflicts or double-processing of events.
The project uses a unified CLI to launch components individually if you don't want to use Docker for the Python code:

- **Start Web Server:** `printqueue web` (or `uvicorn src.app.main:app --reload`)
- **Start Watchdog:** `printqueue watchdog`
- **Start Worker:** `dramatiq -A src.worker.dramatiq_app worker --loglevel=info`

_(Ensure `DATABASE_URL` and `REDIS_URL` are set as environment variables to point to your local development containers!)_

**Testing and Static Analysis:**
Before committing code, verify it against the project's strict rules using `tox`. This will run the `ruff` linter/formatter, the `pyright` type-checker, and the `pytest` suite with coverage.

```bash
export PYTHONPATH=src
tox -e ruff,pyright
pytest tests/ --cov=src --cov-fail-under=85
```

_(For detailed architectural decisions regarding HTMX and Pyright, see `DEV_GUIDE.md` and `HTMX_TUTORIAL.md`)_.
