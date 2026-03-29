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

---

**Summary of Changes Adopted:**

- Removed `pylint` and `mypy`.
- Added `pyright`.
- Configured `ruff format`.
- Migrated environment management from `pip` to `uv sync` + `uv.lock`.
- Integrated `tox-uv` for fast test execution.
