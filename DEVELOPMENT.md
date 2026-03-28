# Print Queue Manager - Development Guide

Welcome to the development guide for the Print Queue Manager. This document provides instructions for setting up your local environment, running the services, and debugging the system, particularly focusing on the Temporal architecture.

## Architecture Overview

This project uses a modern, local-first architecture to manage a 3D print queue, scrape data, and synchronize with external platforms.

- **FastAPI**: Serves the web dashboard (HTMX/Jinja2) and API endpoints.
- **PostgreSQL**: Local database storing print jobs and metadata.
- **Watchdog**: A background service that monitors a local directory for new `.stl` or `.3mf` files and auto-adds them to the queue.
- **Temporal**: An orchestration engine used for background tasks, cron jobs, and asynchronous scraping. It replaces Celery/Redis for reliable workflow execution.
- **Pydantic AI (Ollama)**: Local LLMs are used to parse complex HTML from external platform pages (when official APIs are unavailable).
- **Playwright**: Headless browser automation used alongside Ollama to fetch authenticated user data.

## Temporal Integration

We use Temporal to reliably execute and retry background tasks, such as scanning directories or scraping remote websites (MakerWorld, Printables, Thingiverse, Cults3D, Minihoarder).

Temporal consists of three main parts:
1. **Temporal Server**: The central orchestrator that keeps track of state, history, and queues.
2. **Temporal Client**: Our FastAPI application, which submits workflows (like triggering a manual sync).
3. **Temporal Worker**: Our background process (`printqueue worker`) that executes the actual Workflow and Activity code.

### Running Temporal Locally

The easiest way to run the Temporal Server locally for development is using the Temporal CLI:

```bash
# Install Temporal CLI (macOS example)
brew install temporal

# Start the local Temporal server on default port 7233
temporal server start-dev
```

When running `temporal server start-dev`, it also spins up the **Temporal Web UI** at `http://localhost:8233`. This UI is essential for debugging.

### Starting the Services

To fully test the application locally, you need to run several components concurrently. Ensure your Python virtual environment is activated and dependencies are installed (`pip install -e ".[dev]"`).

1. **Start PostgreSQL**: Make sure you have a local postgres instance running.
2. **Start Temporal Server**: `temporal server start-dev`
3. **Start the Web Server**:
   ```bash
   printqueue web
   ```
4. **Start the Temporal Worker**:
   ```bash
   printqueue worker
   ```
   *Note: This worker connects to Temporal on `localhost:7233` (configurable via `TEMPORAL_TARGET` in env).*
5. **Start the Watchdog (Optional)**:
   ```bash
   printqueue watchdog
   ```

### Debugging Temporal Workflows

If a synchronization task fails or hangs, you can use the Temporal Web UI (`http://localhost:8233`) to inspect it:

1. Navigate to the **Workflows** tab.
2. Search or find the workflow by ID (e.g., `sync-makerworld-xxx`).
3. View the **History** to see exactly which Activity failed and why.
4. You can view input/output variables, stack traces of errors, and retry attempts.
5. Because Temporal persists state, if your worker crashes, you can simply restart the worker and it will pick up exactly where it left off.

## Testing

We use `pytest` for unit testing. The Temporal client is mocked in unit tests to ensure they remain fast and isolated.

```bash
# Run tests with coverage
pytest tests/
```

## Linting and Formatting

We use `ruff` and `pyright` for linting, formatting, and type checking.

```bash
# Check formatting and linting
ruff check src/ tests/
ruff format --check src/ tests/

# Check types
pyright src/ tests/
```
