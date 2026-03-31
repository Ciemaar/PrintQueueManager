# Temporal Migration Plan

1. *Update dependencies in `pyproject.toml`.*
   - Remove `celery` and `redis`.
   - Add `temporalio`.
2. *Update `src/app/config.py`.*
   - Remove `redis_url`.
   - Add `temporal_target` defaulting to `localhost:7233`.
3. *Implement Temporal Workflows and Activities.*
   - Create `src/worker/temporal_workflows.py`.
   - Move the sync logic (`sync_makerworld`, `sync_printables`, etc.) from `src/worker/celery_app.py` to `src/worker/temporal_workflows.py` as Temporal Activities.
   - Create a Temporal Workflow (e.g., `SyncPlatformWorkflow`) that calls these activities.
   - Delete `src/worker/celery_app.py`.
4. *Update `src/app/main.py`.*
   - Replace Celery task imports with Temporal workflow triggers.
   - For `/sync/{platform}` and startup event, connect to the Temporal Client and asynchronously start the workflow using `client.execute_workflow` (with an appropriate task queue).
5. *Create Temporal Worker.*
   - Create `src/worker/main.py` to initialize and run the Temporal Worker, registering the workflows and activities.
   - This script will connect to the Temporal Server and listen on a specific Task Queue.
6. *Update CLI commands in `src/app/cli.py`.*
   - Add `worker` command to start the Temporal worker (running `src/worker/main.py`).
7. *Setup Temporal Cron Schedules.*
   - Create a script or add logic to the Temporal Worker startup to register Cron Schedules for the periodic syncing, replacing the Celery `@on_after_configure.connect` logic. Alternatively, use a setup script that registers the schedules via the Temporal Client when the worker starts.
8. *Update Tests.*
   - Fix `tests/unit/test_main_sync.py` to mock Temporal client calls instead of `celery.delay`.
   - Rename `tests/unit/test_celery.py` to `tests/unit/test_temporal_workflows.py` and update tests to test Temporal activities instead of Celery tasks.
   - Rename `tests/unit/test_celery_registration.py` to `tests/unit/test_temporal_registration.py` and update accordingly.
9. *Create Developer Documentation.*
   - Create a `DEVELOPMENT.md` explaining the Temporal architecture, how to run the Temporal Server locally (using Docker/CLI), how to start the worker, and how to debug using the Temporal UI.
10. *Complete pre commit steps.*
    - Complete pre commit steps to ensure proper testing, verifications, reviews and reflections are done.
11. *Submit the change.*
    - Once all tests pass and documentation is added, I will submit the change with a descriptive commit message.
