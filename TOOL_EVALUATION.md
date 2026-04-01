# Tool Evaluation & Recommendations

This document outlines the evaluation of modern Python tooling for the PrintQueueManager project to ensure speed, correctness, and developer experience.

## Linting & Formatting

**Current:** `ruff` (linting) + `pylint` (linting) + `no strict formatter`
**Alternatives:** `black`, `isort`, `flake8`
**Decision:** **Standardize entirely on `ruff`.**

- _Reasoning:_ Ruff has effectively replaced `flake8`, `isort`, `black`, and `pylint` in the modern Python ecosystem. It runs in milliseconds (written in Rust) and covers >95% of Pylint's rules. Running `pylint` alongside `ruff` adds duplicate CI time for diminishing returns.
- _Action:_ Drop `pylint`. Enable `ruff format` to replace the need for `black`.

## Type Checking

**Current:** `mypy`
**Alternatives:** `pyright`, `basedpyright`, `pyre`
**Decision:** **Migrate to `pyright`.**

- _Reasoning:_ `mypy` is the classic standard, but `pyright` (maintained by Microsoft) is significantly faster, handles complex generic inference better, and integrates perfectly with `pydantic` (which this project relies on heavily for agentic extraction).
- _Action:_ Remove `mypy` from dependencies and CI, configure `pyproject.toml` for `pyright`, and update the `tox.ini`.

## Testing

**Current:** `pytest` + `pytest-cov` + `hypothesis`
**Alternatives:** `unittest`, `nose`
**Decision:** **Keep `pytest` stack.**

- _Reasoning:_ `pytest` is undeniably the industry standard. `hypothesis` is perfect for property-based testing on the Pydantic schema validation.

## Environment Management & Automation

**Current:** `pip` + `tox`
**Alternatives:** `uv`, `poetry`, `hatch`, `nox`

**Evaluation of Alternatives:**

- `pip`: The default standard. Reliable but notoriously slow at resolving dependencies and lacks built-in lockfile or project management capabilities out of the box (requires `pip-tools` or `venv` orchestration).
- `poetry`: Excellent for dependency management and publishing. However, dependency resolution can be slow on larger projects, and its custom lockfile format isn't universally standard.
- `hatch`: A great modern build backend and environment manager, but it delegates dependency resolution to `pip` internally, meaning it doesn't gain the speed advantages of Rust-based tools.
- `nox`: A modern alternative to `tox` that uses Python scripts instead of INI files. While powerful, we are sticking to `tox` due to its simplicity and the availability of `tox-uv`.
- `uv`: An incredibly fast, Rust-based Python package and project manager by Astral. It can act as a drop-in replacement for `pip`, but also supports full project management via `uv sync` and a strict `uv.lock` file.

**Decision:** **Migrate entirely to `uv` and adopt `uv sync`. Keep `tox` for multi-environment orchestration using `tox-uv`.**

- _Pros of `uv sync`:_
  - **Speed:** Dependency resolution and installation are 10-100x faster than `pip`.
  - **Reproducibility:** `uv sync` reads from `uv.lock`, guaranteeing exact dependency versions across environments, Docker builds, and CI pipelines.
  - **Simplicity:** Eliminates the need to manually manage virtual environments (`python -m venv` and `source venv/bin/activate`). `uv run` handles execution automatically.
- _Cons of `uv sync`:_
  - **Developer Onboarding:** Requires developers to install a new tool (`uv`) rather than relying on Python's built-in `pip` and `venv`.
- _Action:_ Adopt `uv.lock`, update Docker multi-stage builds to utilize Astral's caching recommendations, update CI pipelines to use `astral-sh/setup-uv`, and adopt `tox-uv` to make our Tox runs instantaneous.

## Documentation

**Current:** Markdown (`README.md`, `USER_GUIDE.md`, etc.)
**Alternatives:** `mkdocs` (with Material theme), `Sphinx`
**Decision:** **Keep Markdown for now.**

- _Reasoning:_ Given the currently small scope of the project, raw Markdown files rendered natively by GitHub are sufficient. Moving to MkDocs introduces build steps that aren't strictly necessary yet.

## Agentic Coding Tools

**Current:** None (Manual coding / traditional autocomplete)
**Alternatives:** Jules (Google), GitHub Copilot (Agent Mode), Claude Code (Anthropic)
**Decision:** **Adopt GitHub Copilot (Agent Mode) or Claude Code based on team preference, while keeping an eye on Jules.**

This section compares autonomous agentic coding tools to evaluate which one best fits our stack (FastAPI, Python, GitHub) and developer workflows.

### Jules (Google)

- **Features:** Jules is an asynchronous coding agent powered by Gemini 2.5 Pro. It connects through CLI tools and APIs to GitHub, Slack, Jira, and Linear. Jules operates within existing workflows rather than requiring process changes. It runs tasks in the background while developers continue other work, presenting code diffs for review before merging. It plans, executes, and iterates on complete tasks autonomously.
- **Pricing:** Jules offers a free tier for individual developers and small teams. Paid plans, like Pro and Ultra, are accessed through a Google One subscription.
- **Integration with Current Stack:** Integrates natively with GitHub via CLI and API. Jules is well-suited for Python and FastAPI projects, as its underlying Gemini models have strong Python capabilities. The asynchronous "background task" approach fits well with PR-based workflows.

### GitHub Copilot (Agent Mode)

- **Features:** GitHub Copilot Agents can handle busywork, review code, write pull requests, and respond to @mentions in real time. It allows developers to delegate tasks from GitHub Issues, IDEs (VS Code), or the CLI. Copilot integrates tightly with GitHub projects and issues. Developers can pick between first-party Copilot models or third-party agents like Claude and OpenAI Codex.
- **Pricing:** Copilot Free (limited access), Copilot Pro ($10/month), Copilot Pro+ ($39/month). It has premium request limits for features like chat, agent mode, and coding agent.
- **Integration with Current Stack:** Very deep integration with GitHub (which this project uses). Copilot integrates natively into the developer's IDE (VS Code/PyCharm) and GitHub UI (Issues, Pull Requests), providing a seamless experience for a Python/FastAPI project hosted on GitHub.

### Claude Code (Anthropic)

- **Features:** Claude Code operates via a CLI interface and uses Anthropic's Claude models (e.g., Sonnet 3.7). It is an autonomous agent that can navigate repositories, plan complex refactors, run multiple agents in parallel, and even watch application logs to autonomously fix errors. It relies heavily on local context files (like `CLAUDE.md`).
- **Pricing:** Pay-as-you-go based on API token usage. Claude Sonnet 3.7 costs $3 per million input tokens and $15 per million output tokens. There are also Claude subscription plans (Pro at $20/month, Team at $25/user/month) that provide access to the developer environment for high usage.
- **Integration with Current Stack:** Integrates well via the CLI for Python projects. Its ability to read local Markdown instructions (`CLAUDE.md` or `AGENTS.md`) aligns perfectly with our use of agentic instruction files in the repository.

- _Reasoning:_ GitHub Copilot offers the most seamless integration with our existing GitHub-based workflow. Claude Code is highly praised for its autonomous CLI capabilities and works great with repository-level instructions (`AGENTS.md`). Both are excellent for FastAPI/Python.
- _Action:_ Encourage developers to use Copilot Pro or Claude Code locally. Evaluate Jules once it becomes more widely available outside of personal Google accounts.

---

**Summary of Changes Adopted:**

- Removed `pylint` and `mypy`.
- Added `pyright`.
- Configured `ruff format`.
- Migrated environment management from `pip` to `uv sync` + `uv.lock`.
- Integrated `tox-uv` for fast test execution.

## Background Job Orchestration & Task Queues

**Current:** `Celery`
**Alternatives:** `RQ`, `Huey`, `Dramatiq`, `Temporal`
**Decision:** **Migrate to `RQ` (Redis Queue) or `Dramatiq`.**

- _Reasoning:_ While Celery is the de facto standard for distributed task processing in Python, it carries significant complexity and operational overhead. PrintQueueManager is a local-first application designed for easy deployment via Docker Compose on user hardware.
  - **Celery:** Highly feature-rich but comes with a steep learning curve and operational complexity. It is arguably overkill for a single-node, local-first queue system.
  - **RQ (Redis Queue):** Extremely lightweight and simple. It uses Redis as both the queue broker and storage. It lacks built-in scheduling (requiring a separate package like `rq-scheduler`), but its simplicity makes it highly attractive for local deployments.
  - **Huey:** Another lightweight, Redis-backed task queue. It is simpler than Celery but offers built-in scheduling. However, it has a smaller community compared to RQ and Dramatiq.
  - **Dramatiq:** Focused on simplicity, reliability, and performance. It supports both RabbitMQ and Redis. It is often considered a modern alternative to Celery that is easier to operate while still being highly performant.
  - **Temporal:** A powerful workflow orchestration engine. However, Temporal requires running a separate Temporal Server (which involves a database and multiple services), adding massive infrastructure complexity that fundamentally violates the "Local Inference First" and lightweight Docker Compose goals of PrintQueueManager.
- _Action:_ Given that we already use Redis, **RQ** is the simplest drop-in replacement that drastically reduces cognitive and operational load. Alternatively, **Dramatiq** is a strong modern choice if higher performance is needed in the future. We propose migrating from Celery to RQ.

## Message Brokers

**Current:** `Redis`
**Alternatives:** `RabbitMQ`, `Amazon SQS`
**Decision:** **Keep `Redis`.**

- _Reasoning:_
  - **Redis:** Simple, fast, and easily deployable via a single Docker container. We already use it for Celery, and it is the native broker for RQ.
  - **RabbitMQ:** Offers durable message delivery and advanced routing, but operating RabbitMQ in Docker is significantly more complex than Redis and uses more memory.
  - **Amazon SQS:** A managed cloud service. This violates the project's "Local Inference First" and offline-capable design.
- _Action:_ Continue using Redis as the primary message broker and cache.

## Web Frameworks

**Current:** `FastAPI`
**Alternatives:** `Django`, `Flask`
**Decision:** **Keep `FastAPI`.**

- _Reasoning:_
  - **FastAPI:** Built on modern Python type hints and Pydantic. Since PrintQueueManager heavily utilizes `Pydantic AI` for agentic scraping, the shared Pydantic ecosystem makes data validation seamless between the scraping layer and the web API. It also supports async out of the box, which is vital for non-blocking local LLM requests.
  - **Django:** A robust, "batteries-included" framework. However, its ORM and synchronous legacy design make it less ideal for the highly asynchronous, HTMX-driven, and Pydantic-heavy architecture we have adopted.
  - **Flask:** A lightweight microframework. While simple, it lacks the built-in async support, automatic OpenAPI documentation, and native Pydantic integration that FastAPI provides.
- _Action:_ Retain FastAPI as the core web framework.

## Autoscaling & Cloud Hosting Platforms

**Current:** `Docker Compose` (Local)
**Alternatives:** `Judoscale` (Autoscaling), `Amazon ECS`, `Fly.io`, `Heroku`, `Railway`, `Render`
**Decision:** **Reject Cloud Hosting and Autoscaling.**

- _Reasoning:_
  - The PrintQueueManager is explicitly designed as a **Local, Agentic 3D Print Queue Management System**. The primary value proposition is preserving privacy by running models locally (via Ollama) and operating offline.
  - **Amazon ECS, Fly.io, Heroku, Railway, Render:** Deploying to these cloud platforms would require exposing local 3D printer APIs over the internet and paying for expensive cloud GPU instances to run local LLMs. This fundamentally contradicts the project's core philosophy.
  - **Judoscale:** While excellent for autoscaling task queues based on latency in cloud environments (like Heroku or Render), horizontal autoscaling of worker nodes is unnecessary for a local-first system running on a single user's machine.
- _Action:_ Continue relying solely on `docker-compose.yml` for orchestration and local deployment.
