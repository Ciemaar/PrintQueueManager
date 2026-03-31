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
**Decision:** **Introduce `uv` to speed up CI/CD, keep `tox` for orchestration.**

- _Reasoning:_ `uv` (by Astral, makers of Ruff) is a drop-in replacement for `pip` that resolves and installs dependencies 10-100x faster. We can use `tox-uv` to make our Tox runs instantaneous.
- _Action:_ Update GitHub actions to use `uv pip install` if desired, or simply document `uv` usage for local developers.

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
