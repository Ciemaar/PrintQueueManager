# Agent Instructions: PrintQueueManager

Welcome! If you are an AI assistant working on this repository, please read these instructions carefully before proposing changes.

## Architectural Philosophy

1. **Local-First & Private:** This application handles sensitive user data (3D print collections, local directories). Never send data to third-party cloud LLM APIs. We strictly rely on local inference servers like Ollama.
2. **Pydantic AI over Beautiful Soup:** When scraping dynamic or unstructured web content (e.g., MakerWorld, Printables), use `pydantic-ai` with local LLMs to map the HTML string into a defined Pydantic schema (`ScrapedPageData`). Avoid writing CSS selector logic that easily breaks.
3. **Structured APIs First:** If an official API exists (e.g., Thingiverse), fetch data directly via `httpx` and bypass the LLM agent to save compute time. Only fallback to the LLM agent if the API fails or no token is provided.
4. **FastAPI & HTMX Backend:** Avoid complex JS frameworks. The user interface uses server-side rendered Jinja2 templates via FastAPI and `htmx` for dynamic frontend interactions.

## Coding Conventions

- **Types:** Use Python type hints (`pyright` is enforced). Use `typing.Any` or `Optional` sparingly, and try to be as specific as possible.
- **Linters:** The repository uses `ruff` for formatting and linting. You must resolve all warnings.
- **Database:** Use PostgreSQL `JSONB` columns in SQLAlchemy models for unstructured data storage (e.g., raw API responses, agent metadata) to ensure future flexibility without frequent schema migrations.

## Testing & Verification

Before submitting any code, you MUST run the following static analysis tools and tests to verify your changes:

```bash
# Set PYTHONPATH for tests
export PYTHONPATH=src

# Run tests
pytest tests/

# Run static analysis
tox -e ruff,pyright
```

All new features and API routes should include property-based tests using `pytest` and `hypothesis` when appropriate.

## Local Services

When instructed to run or mock services, be aware that the `docker-compose.yml` spins up:

- PostgreSQL (`db` on `5432`)
- Redis (`redis` on `6379`)
- Ollama (`ollama` on `11434`)
- Celery Worker & Beat scheduler
- Watchdog Local File Monitor

Thank you for contributing to the PrintQueueManager!
