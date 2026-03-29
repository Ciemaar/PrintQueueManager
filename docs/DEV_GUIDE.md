# Developer Guide

Welcome to the development of **Print Queue Manager**! This guide details how the system is structured, tested, and expanded.

## Architecture

The system is a Python-based backend that uses:

- **FastAPI:** To build the core server and API endpoints.
- **SQLAlchemy & PostgreSQL:** For robust structured data storage. The `PrintJob` model utilizes `JSONB` to store raw, unstructured data returned by local AI agents, allowing future-proofing for dynamic platform changes.
- **HTMX + Jinja2:** To provide a responsive, reactive single-page dashboard without the overhead of heavy JavaScript frameworks.

If you are new to HTMX, please read the [HTMX Tutorial](HTMX_TUTORIAL.md) for examples of how it is used in this codebase.

If you are editing the frontend HTML templates, read the [Styling Guide](STYLING_GUIDE.md) to understand how the classless Pico CSS framework works.

If you are new to background tasks, please read the [Celery & Redis Tutorial](CELERY_REDIS_TUTORIAL.md) for an explanation of the asynchronous scraping architecture.

- **Celery & Redis:** To execute asynchronous tasks in the background, like web scraping and syncing models from online sources.
- **Watchdog:** A standalone process to monitor a local directory (`watched_folder/`) for 3D model files (`.stl`, `.3mf`) and insert them into the database.
- **Pydantic AI & Ollama:** To power the "Source Specialist" agent. It extracts structured JSON data from raw HTML without requiring brittle CSS selectors.

## Setup Development Environment

Ensure you have Python 3.10+ and a local PostgreSQL + Redis instance running. We recommend using `docker-compose` to spin up your databases and then running your web/worker/watchdog locally using [uv](https://docs.astral.sh/uv/) for incredibly fast dependency management. (See the [Docker Compose Guide](DOCKER_GUIDE.md) for detailed container instructions.)

```bash
# Install uv if you haven't already (https://docs.astral.sh/uv/getting-started/installation/)
# This command automatically creates a managed environment and installs all dependencies and dev tools
uv sync --all-extras --dev

# Activate the virtual environment:
source .venv/bin/activate

# Run any python script directly:
pytest tests/
uvicorn src.app.main:app --reload
```

## Running Static Analysis & Tests

We rely on `tox` for automation. Running `tox` will check the code quality across the entire project. Ensure you have activated your virtual environment before running tox.

- `tox -e pyright`: Runs Pyright type checking.
- `tox -e ruff`: Runs Ruff linter and formatter.
- `pytest tests/`: Runs unit and integration tests with `hypothesis` for property-based generation and testing of schema components.

```bash
# Run all static analysis
tox -e ruff,pyright
```

## Integrating a New 3D Platform

To integrate a new 3D Model Platform:

1. Open `src/worker/llm_scraper.py`.
2. Modify `run_scraper` or create a new wrapper specifically for your new site. Ensure that the Agent uses an appropriate Local LLM system prompt to parse the specific page HTML.
3. In `src/worker/celery_app.py`, define a new Celery task (`@celery_app.task`) to fetch the target HTML and execute the LLM scraper, then set up Celery beat scheduling to call your function periodically.
