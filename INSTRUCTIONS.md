# Temporal Migration Instructions

Your goal is to migrate the background job orchestration for this FastAPI 3D Print Queue Manager from Celery/Redis to Temporal.

1. **Update Dependencies:**
   - Remove `celery` and `redis` from `pyproject.toml`.
   - Add `temporalio` to `pyproject.toml`.
2. **Update Configuration:**
   - Remove `redis_url` from `src/app/config.py`.
   - Add `temporal_target` to `src/app/config.py` with a default of `localhost:7233`.
3. **Implement Temporal Workflows and Activities:**
   - Create `src/worker/temporal_workflows.py`.
   - Move the platform synchronization logic (e.g., `sync_makerworld`, `sync_printables`, `sync_local`) from `src/worker/celery_app.py` into this new file, decorating them with `@activity.defn`.
   - Create corresponding Temporal Workflows (e.g., `SyncMakerworldWorkflow`, `SyncLocalWorkflow`) decorated with `@workflow.defn` that execute these activities using `workflow.execute_activity`.
   - Ensure you delete the old `src/worker/celery_app.py` file.
4. **Update the FastAPI Application (`src/app/main.py`):**
   - Create a helper to initialize the Temporal Client (e.g., `src/app/temporal_client.py`).
   - Replace Celery's `.delay()` calls in the startup event and the `/sync/{platform}` endpoints with Temporal client calls to `execute_workflow` (for synchronous startup) or `start_workflow` (for asynchronous endpoint triggers) on a specified task queue (e.g., `"sync-task-queue"`).
5. **Create the Temporal Worker (`src/worker/main.py`):**
   - Write an entrypoint script that connects to the Temporal server.
   - Registers all Workflows and Activities with a `Worker` instance listening on the `"sync-task-queue"`.
   - Implement logic to programmatically register Temporal Cron Schedules (using `Client.create_schedule`) for the periodic syncing tasks, replacing Celery's `@on_after_configure.connect`.
6. **Update CLI Commands (`src/app/cli.py`):**
   - Add a `worker` subcommand to the `printqueue` CLI that starts the Temporal worker (running the `src/worker/main.py` main loop).
7. **Update Tests:**
   - Ensure to mock `Client.connect` and `Worker` when testing `src/worker/main.py`.
   - Mock the `get_temporal_client` dependency in FastAPI endpoint tests (`tests/unit/test_main_sync.py`) instead of mocking Celery's `.delay()`.
   - Rename tests referencing Celery to Temporal, and ensure `pytest` coverage tests pass. Ensure any `argparse` `SystemExit` handling in `test_cli.py` is appropriately caught using `pytest.raises(SystemExit)`.
   - Fix linting and formatting issues carefully using `ruff check --fix` and `ruff format`. Do not use `--unsafe-fixes` in pre-commit hooks.
8. **Developer Documentation:**
   - Create or update `DEVELOPMENT.md` to explain the Temporal architecture, how to run the Temporal CLI Server locally, and how to debug via the Temporal Web UI.
