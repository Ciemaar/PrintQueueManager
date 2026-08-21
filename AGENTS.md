# Agent Instructions: PrintQueueManager

Welcome! If you are an AI assistant working on this repository, please read these instructions carefully before proposing changes.

## General Directives & Planning

- **Deep Planning Mode**: Before making any changes, you must enter 'deep planning mode': actively use `message_user` or `request_user_input` tools to fully clarify requirements and test assumptions. Do not start work until all assumptions are confirmed. Only once you are absolutely certain, create an execution plan using `set_plan`, and then execute it autonomously without asking for further confirmation.
- **Pre-commit Step Requirement**: When using the `request_plan_review` tool in this environment, the plan's pre-commit step description must perfectly match "Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done." without any extra text, nested bullets, or variations in phrasing.
- **License**: The project is licensed under the GNU General Public License v3 (GPLv3).

## Architectural Philosophy

1. **Local-First & Private:** This application handles sensitive user data (3D print collections, local directories). Never send data to third-party cloud LLM APIs. We strictly rely on local inference servers like Ollama.
2. **Pydantic AI over Beautiful Soup:** When scraping dynamic or unstructured web content (e.g., MakerWorld, Printables), use `pydantic-ai` with local LLMs to map the HTML string into a defined Pydantic schema (`ScrapedPageData`). Avoid writing CSS selector logic that easily breaks.
3. **Structured APIs First:** If an official API exists (e.g., Thingiverse), fetch data directly via `httpx` and bypass the LLM agent to save compute time. Only fallback to the LLM agent if the API fails or no token is provided.
4. **FastAPI & HTMX Backend:** Avoid complex JS frameworks. The user interface uses server-side rendered Jinja2 templates via FastAPI and `htmx` for dynamic frontend interactions.
5. **Worker Synchronization:** Worker synchronization logic for external platforms must follow a batch-query pattern: deduplicate API response data first, then perform a single SQLAlchemy `.in_()` query to find existing records. Wrap the batch query in a conditional guard (e.g., `if items_to_check:`) to avoid execution when the input batch is empty. Use a Python `set` for O(1) existence checks inside the processing loop, and immediately update this set after calling `db.add()` to handle potential duplicate entries within the same batch.

## Coding Conventions & Style

- **Types:** Use Python type hints (`pyright` is enforced). Strictly avoid using `Any`. Try to be as specific as possible. When type hinting the return type of SQLAlchemy query methods returning multiple model instances, use `collections.abc.Sequence['ModelName']` instead of `list['ModelName']` to avoid Pyright variance errors regarding `Self`.
- **Ternary Operators:** Never use the `x or y` shortcut syntax for non-boolean results (e.g., `value or 0.0`). Python evaluates values like `0.0` or `""` as falsy, leading to unintended behavior. Instead, always use explicit ternary operations like `x if x is not None else y`.
- **Linters & Formatting:** The repository uses `uv run ruff check` and `uv run ruff format` for linting and formatting, and `uv run pyright` for static type checking. You must resolve all warnings.
  - The Ruff configuration enforces a 100-character line length limit (E501). Ensure all code and docstrings are wrapped to comply.
  - Strict docstring rules are enforced (e.g., D213, D400, D415), requiring multi-line docstring summaries to start on the second line and end with a period or appropriate punctuation.
- **Line Endings:** Ensure Python files have Unix (LF) line endings (e.g., using `dos2unix`) to prevent Pyright 'Unexpected indentation' errors on Windows GitHub Actions runners.
- **Dependencies & Environment:** The project uses `uv`. Ensure development dependencies (e.g., `hypothesis`, `pytest-asyncio`) are placed in the `[dependency-groups] dev` section of `pyproject.toml`. Update the lockfile using `uv lock`.
- **Logging vs. Print:** Always use the Python `logging` module instead of `print()` statements for debugging and output. Use `logger.info()`, `logger.debug()`, `logger.error()`, etc.
- **Performance:** For O(1) membership lookups of static elements like Enums or constants (e.g., `enum_status in {PrintStatus.PRINTED, ...}`), use Python sets rather than lists.
- **File System Traversal:** When using `pathlib`, `is_file()` evaluates to `False` for broken symlinks in modern Python. Explicitly check `is_symlink()` alongside `is_file()` to handle broken symlinks.
- **Configuration:** When configuring default values in pydantic-settings (e.g., `src/app/config.py`), omit sensitive credentials like passwords from default strings and rely on environment variable overrides instead.

## Backend, API, & AI

- **FastAPI Templates:** When converting FastAPI `HTMLResponse` string responses to Jinja2 `TemplateResponse`s, ensure `request: Request` is added to the route function's signature. Construct the `Jinja2Templates` directory path using absolute paths (e.g., `os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')`) to ensure correct resolution regardless of current working directory.
- **HTMX Handling:** In HTMX-driven endpoints (such as deleting or undeleting items), returning an empty string (`""`) or `HTMLResponse("")` is the standard pattern to instruct the frontend to remove the corresponding element from the UI.
- **Security:** When introducing cross-site scripting (XSS) protections in FastAPI responses or templates, ensure the `html` module is explicitly imported at the top of the file before using `html.escape`.
- **Playwright Operations:** Explicitly catch `playwright.sync_api.Error` and `playwright.sync_api.TimeoutError` instead of generic `Exception`s to prevent masking unrelated system exceptions. Ensure unit tests verify these failure states by raising `Error` from `playwright.sync_api`.
- **Pydantic AI:** When dynamically configuring Pydantic AI agents for external OpenAI-compatible providers in pydantic-ai v1.73.0+, `OpenAIModel` is deprecated. Use `OpenAIChatModel`. If standard provider imports are blocked by strict reviews, implement a custom provider subclassing `pydantic_ai.providers.Provider[AsyncOpenAI]` that securely initializes an `AsyncOpenAI` client internally, and pass this to `OpenAIChatModel`.

## Database & SQLAlchemy

- **Database Types:** Use PostgreSQL `JSONB` columns in SQLAlchemy models for unstructured data storage (e.g., raw API responses, agent metadata) to ensure future flexibility without frequent schema migrations.
- **Database Transactions:** In worker scripts and Celery tasks, catch expected exceptions (like `SQLAlchemyError` or `OSError`) to log and rollback. For unknown exceptions, ensure they are caught, logged, rolled back (`db.rollback()`), and explicitly re-raised (`raise`) to prevent masking critical errors.
- **Query Refactoring:** Encapsulate complex SQLAlchemy database queries from FastAPI route handlers as `@classmethod`s directly on the relevant SQLAlchemy model class (e.g., in `src/app/models/__init__.py`).
- **Database Indexing:** To prevent performance degradation during background synchronization, columns used for existence checks (e.g., `source_url` and `file_path` in `PrintJob`) must be indexed.
- **Manual Data Insertion:** When manually inserting records into SQLite (e.g., via `sqlite3`), use the Enum's attribute name (e.g., `TO_BE_PRINTED`) instead of its string value, or SQLAlchemy will throw a `KeyError`.
- **Priority Sorting:** Backend logic for print job priority sorting is normalized and processed using `_normalize_priorities_sync` and PostgreSQL's `nullsfirst()` ordering for deterministic results.

## Testing & Verification

Before submitting any code, you MUST run the following static analysis tools and tests to verify your changes:

```bash
# Set PYTHONPATH for tests
export PYTHONPATH=src

# Run tests
pytest tests/
# If tests fail with "ModuleNotFoundError: No module named 'src'", run:
PYTHONPATH=. uv run pytest

# Run static analysis
tox -e ruff,pyright
```

- **Code Coverage:** The test suite enforces a minimum code coverage requirement of 85% (`--cov-fail-under=85`). Ensure tests are added or updated to meet this threshold. All new features and API routes should include property-based tests using `pytest` and `hypothesis` when appropriate.
- **Test Structure & Mock Data:** Large mock HTML templates and fallback datasets should be relocated to a dedicated `src/worker/mock_data.py` file. If externalizing mock data for classes defined in the same module (e.g., Pydantic models in `llm_scraper.py`), store the data as raw dictionaries and instantiate the models at the call site to prevent circular import issues. Security-related unit tests should be placed in `tests/unit/test_security.py`.
- **Mocking Strategy:**
  - When mocking SQLAlchemy models instantiated with keywords, prefer using a simple class that assigns `**kwargs` to `self` in `__init__` rather than `MagicMock`.
  - To test database rollback behavior in Celery tasks using `unittest.mock`, mock `SessionLocal` to return a mock database object, simulate an exception on a specific method, and assert that `mock_db.rollback.assert_called_once()` and `mock_db.close.assert_called_once()` were executed.
  - When mocking Celery tasks with decorators like `@celery_app.task`, configure the mock's `.task()` method to return a decorator that returns the original function (e.g., `lambda *args, **kwargs: lambda func: func`).
  - When mocking generic classes (like `pydantic_ai.Agent`) in restricted test environments where the library is unavailable, define a mock class inheriting from `typing.Generic` to support subscripting.
- **SQLAlchemy Mocking Verification:** Filter expressions on mocked database sessions can be verified by converting the filter call arguments to a string (e.g., `str(mock_query.filter.call_args[0][0])`) and asserting the presence of expected SQL-like clauses.
- **API Tests:** Tests for operations that should gracefully fail (e.g., operating on non-existent resources) must include negative assertions to verify the absence of database side effects.
- **Network-Restricted Environments:**
  - Specific functions can be tested by reading the source file and using `exec(code, globals_dict)` to run the function in isolation.
  - Unit tests can be executed by identifying the local `pytest` environment and running with `-c /dev/null` to bypass unresolvable configurations like coverage in `pyproject.toml`. Heavy external dependencies should be mocked via `sys.modules` using `types.ModuleType` with `__path__ = []`.
- **Tox:** When configuring `tox` test environments via `pyproject.toml`, ensure `setenv = PYTHONPATH = {toxinidir}` is included in the `[testenv]` section. If `tox` fails with `runner 'uv-venv-lock-runner' ... is not available`, remove the `runner = uv-venv-lock-runner` line from the `[testenv]` configuration.

## Frontend UI

- **Reordering:** Drag-and-drop job reordering in the frontend UI is implemented using `Sortable.js` and `.drag-handle` classes within the PicoCSS-based templates.
- **UI Verification:** Frontend UI changes require visual verification via Playwright scripts. For local verification using an SQLite database, set `DATABASE_URL=sqlite:///./test_ui.db` and `PYTHONPATH=..`. To run the FastAPI application locally without a running Redis instance, set `REDIS_URL=memory://` to bypass Celery broker connection errors.

## Local Services & Docker

When instructed to run or mock services, be aware that `docker-compose.yml` spins up: PostgreSQL (`db` on `5432`), Redis (`redis` on `6379`), Ollama (`ollama` on `11434`), Celery Worker & Beat scheduler, and a Watchdog Local File Monitor.

- **Verbose Logging:** To run Docker containers in verbose mode, set the `VERBOSE` environment variable to `"true"`.
- **Environment Variables:** When editing `docker-compose.yml`, always preserve environment variable fallbacks (e.g., `${POSTGRES_PASSWORD:-password}`) rather than hardcoding passwords to avoid security regressions.
- **Headless Rendering:** When using `trimesh` and `pyglet` for headless 3D model rendering in a Dockerized environment, ensure the system packages `xvfb` and `libgl1` are installed in the `Dockerfile`. Furthermore, the execution command must be prefixed with `xvfb-run` (e.g., `xvfb-run celery ...` in `docker-compose.yml`) to utilize the virtual framebuffer.

## Version Control Guidelines

When working on an existing, previous branch (e.g., rebasing or merging), you must ensure that features added to the main branch in the intermediate interval are not removed. Additionally, all branches being merged in, as well as their matching PRs, must be referenced in the commit comments and any new PRs.

## Database Migrations (Alembic)

This project uses `Alembic` to manage database schema updates. If you modify any SQLAlchemy models, you **MUST** generate an Alembic migration:

1. Start your task by defining your changes in `src/app/models/__init__.py`.
2. Create a migration file automatically:
   ```bash
   PYTHONPATH=. DATABASE_URL="sqlite:///./test.db" alembic revision --autogenerate -m "Describe your changes"
   ```
3. Inspect the generated migration in `alembic/versions/` to verify it correctly implements the changes.
4. The migration will be automatically applied when the FastAPI application starts, or you can apply it locally to test:
   ```bash
   PYTHONPATH=. DATABASE_URL="sqlite:///./test.db" alembic upgrade head
   ```

- **Restricted Sandbox:** If the `alembic` CLI tool is unavailable, database migrations can be manually authored in `alembic/versions/` by identifying the current head revision and providing the `revision` and `down_revision` strings manually in the new file.
- **SQLite Migrations:** When writing Alembic migrations for SQLite, `op.alter_column` does not natively support making existing columns non-nullable. Instead, use `with op.batch_alter_table('table_name') as batch_op:` and apply `batch_op.alter_column` to ensure cross-database compatibility. Do not rely solely on `Base.metadata.create_all()` for schema updates.

## Pull Requests & Workflows

- **Continuing Work:** When opening a new Pull Request that continues, supersedes, or rebases previous work, explicitly list the prior PR numbers or branch names in the PR description to preserve context and traceability. When rebasing or merging an existing, previous branch, features added to the main branch in the intermediate interval must not be removed. All branches being merged in and their matching PRs must be referenced in the commit comments and any new PRs.
- **Testing Improvements:** PR titles must be prefixed with the '🧪' emoji (e.g., '🧪 [testing improvement description]'). The description must include dedicated sections for 'What' (the testing gap addressed), 'Coverage' (scenarios covered), and 'Result' (improvement in reliability or coverage).
- **Security Fixes:** PR titles should be prefixed with the '🔒' emoji (e.g., '🔒 [security fix description]'). The description must include dedicated sections for 'What' (vulnerability details), 'Risk' (impact assessment), and 'Solution' (remediation steps).

Thank you for contributing to the PrintQueueManager!
