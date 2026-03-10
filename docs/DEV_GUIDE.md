# Developer Guide

Welcome to the development of **Print Queue Manager**! This guide details how the system is structured, tested, and expanded.

## Architecture

The system is a Python-based backend that uses:

- **FastAPI:** To build the core server and API endpoints.
- **SQLAlchemy & PostgreSQL:** For robust structured data storage. The `PrintJob` model utilizes `JSONB` to store raw, unstructured data returned by local AI agents, allowing future-proofing for dynamic platform changes.
- **HTMX + Jinja2:** To provide a responsive, reactive single-page dashboard without the overhead of heavy JavaScript frameworks.

If you are new to HTMX, please read the [HTMX Tutorial](HTMX_TUTORIAL.md) for examples of how it is used in this codebase.
- **Celery & Redis:** To execute asynchronous tasks in the background, like web scraping and syncing models from online sources.
- **Watchdog:** A standalone process to monitor a local directory (`watched_folder/`) for 3D model files (`.stl`, `.3mf`) and insert them into the database.
- **Pydantic AI & Ollama:** To power the "Source Specialist" agent. It extracts structured JSON data from raw HTML without requiring brittle CSS selectors.

## Setup Development Environment

Ensure you have Python 3.10+ and a local PostgreSQL + Redis instance running. We recommend using `docker-compose` to spin up your databases and then running your web/worker/watchdog locally via virtual environment.

```bash
# Set up a virtual environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Running Static Analysis & Tests

We rely on `tox` for automation. Running `tox` will check the code quality across the entire project.

- `tox -e mypy`: Runs MyPy type checking
- `tox -e ruff`: Runs Ruff linter
- `tox -e pylint`: Runs Pylint code checking
- `pytest tests/`: Runs unit/integration tests with `hypothesis` for property-based generation and testing of schema components.

```bash
# Run all static analysis
tox -e ruff,mypy,pylint
```

## Integrating a New 3D Platform

To integrate a new 3D Model Platform:
1. Open `src/worker/llm_scraper.py`.
2. Modify `run_scraper` or create a new wrapper specifically for your new site. Ensure that the Agent uses an appropriate Local LLM system prompt to parse the specific page HTML.
3. In `src/worker/celery_app.py`, define a new Celery task (`@celery_app.task`) to fetch the target HTML and execute the LLM scraper, then set up Celery beat scheduling to call your function periodically.
