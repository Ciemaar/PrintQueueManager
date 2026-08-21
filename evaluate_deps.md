# Python 3.15 Compatibility Evaluation

During testing with Python 3.15.0a6, several core dependencies failed to build due to major changes in the Python C-API (such as the removal of `_PyCFrame` and changes to frame evaluation/ownership). Below is an evaluation of the blocking packages and potential alternatives:

### 1. `greenlet`
* **Issue:** Fails to compile because it heavily relies on CPython frame internals (`_PyCFrame`), which were drastically altered or removed in 3.15.
* **Impact:** `greenlet` is deeply embedded in the async ecosystem, notably used by `SQLAlchemy` for its async engine support.
* **Alternatives/Mitigation:**
    * We cannot easily swap out `greenlet` if we want to continue using SQLAlchemy's async features.
    * We must wait for the `greenlet` maintainers to release a patch supporting the 3.15 frame evaluation API.

### 2. `pydantic-core` (via `pyo3`)
* **Issue:** PyO3 `v0.26.x` and `v0.27.x` explicitly block compilation on Python versions greater than 3.14. Furthermore, forcing compilation with `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` results in trait implementation errors for new internal types.
* **Impact:** `pydantic-core` is the rust backend for `pydantic`, which is the foundation of `FastAPI` and `pydantic-ai` in our stack.
* **Alternatives/Mitigation:**
    * No alternatives exist; `pydantic` is non-negotiable for this stack.
    * PyO3 maintainers typically release support for new Python versions during the beta phases. Once PyO3 updates, `pydantic-core` will need to release a new wheel compiled against the updated PyO3.

### 3. `psycopg2-binary`
* **Issue:** Fails to build from source because it requires system-level PostgreSQL development headers (`libpq-dev`). Even when headers are provided, pre-compiled wheels for 3.15 do not exist yet.
* **Impact:** Blocks PostgreSQL connectivity.
* **Alternatives/Mitigation:**
    * **Alternative:** We can migrate to `psycopg` (version 3), which is the modern, pure-Python (with optional C optimizations) rewrite of `psycopg2`. `psycopg` (v3) is generally more forward-compatible with new Python versions because its pure-Python fallback (`psycopg[binary]`) does not strictly require C-API compilation. SQLAlchemy already natively supports `psycopg` v3.

### 4. `hypothesis`
* **Issue:** Fails to import `hypothesis._native` because the C-extension slot IDs have changed or are incompatible.
* **Impact:** Property-based testing fails.
* **Alternatives/Mitigation:**
    * We can set `HYPOTHESIS_NO_NATIVE=1` to force `hypothesis` to use its pure-Python fallback, which works perfectly fine (albeit slightly slower) on 3.15. This is a viable long-term mitigation for the CI pipeline until native wheels are available.

### 5. `coverage`
* **Issue:** Similar to hypothesis, `coverage.tracer` C-extension fails due to unknown slot IDs.
* **Impact:** Cannot generate test coverage reports on 3.15.
* **Alternatives/Mitigation:**
    * Coverage can also run in a pure-Python mode, or we can simply disable coverage tracking specifically for the 3.15 pre-release test job, as we only need to verify that the logic executes successfully.

### Summary Recommendation
The primary blockers are `greenlet` and `pydantic-core`. Because these are foundational to `SQLAlchemy` and `FastAPI`/`pydantic-ai`, we cannot migrate away from them. We must maintain the `continue-on-error: true` strategy in the 3.15 CI workflow until the PyO3 and greenlet teams finalize their 3.15 support.

We should, however, consider migrating from `psycopg2-binary` to `psycopg` (v3) in the main branch, as it is a modernization step that also aids forward compatibility.

### Evaluating Alternatives to SQLAlchemy

If `greenlet` remains a blocker for async database access in 3.15, we might need to consider alternatives to `SQLAlchemy`'s async engine (which heavily depends on `greenlet` to bridge synchronous DBAPI calls to asyncio).

1. **SQLModel**:
    * **Pros:** Built on top of SQLAlchemy and Pydantic. It provides a more modern, type-hinted approach to ORM.
    * **Cons:** Because it uses SQLAlchemy under the hood, it still relies on `greenlet` for async operations. It also inherits the `pydantic-core` 3.15 blocker. It is not a viable alternative to escape these specific blockers.
2. **Tortoise ORM**:
    * **Pros:** An async-first ORM inspired by Django. It uses `asyncpg` directly for PostgreSQL, bypassing the need for `greenlet` entirely.
    * **Cons:** Requires a complete rewrite of our database models, query logic, and migration systems (moving from Alembic to Aerich).
3. **Prisma Client Python**:
    * **Pros:** A fully async, auto-generated query builder based on a Prisma schema. Completely bypasses SQLAlchemy/greenlet.
    * **Cons:** Shifts the source of truth to a non-Python schema file (`schema.prisma`). Requires a massive rewrite of all DB interaction logic.
4. **asyncpg (Raw SQL)**:
    * **Pros:** Extremely fast, pure async PostgreSQL driver. No ORM overhead, no `greenlet`.
    * **Cons:** Loss of ORM benefits (type safety, automated migrations, query building). Maintenance burden increases significantly.

**Conclusion on SQLAlchemy:** Moving away from SQLAlchemy would require a near-total rewrite of the application's data layer. Given that Python 3.15 is still in pre-release, the immense cost of replacing SQLAlchemy strongly outweighs the benefit of having tests pass a few months earlier.

### Evaluating Alternatives to FastAPI

FastAPI is blocked because it relies on `pydantic` (and therefore `pydantic-core`/PyO3).

1. **Litestar (formerly Starlite)**:
    * **Pros:** Highly performant, modern async framework. It has first-class support for `msgspec` and `attrs` for validation, meaning it can operate without `pydantic` entirely.
    * **Cons:** While the routing syntax is somewhat similar, transitioning requires rewriting all endpoints, dependency injections, and validation models.
2. **Starlette**:
    * **Pros:** This is the underlying toolkit FastAPI is built on. It is pure Python and highly compatible.
    * **Cons:** It lacks automatic data validation, serialization, and OpenAPI documentation generation. We would have to build these features manually or integrate an alternative validator (like `msgspec`).
3. **Sanic**:
    * **Pros:** A mature, fast async framework. Does not rely on Pydantic.
    * **Cons:** Radically different routing and request handling paradigms compared to FastAPI. Loss of automatic OpenAPI generation.
4. **Django (Async) / Flask**:
    * **Pros:** Massive ecosystems.
    * **Cons:** Much heavier, less performant for pure API use cases, and adopting their async capabilities often feels bolted-on compared to ASGI-native frameworks.

**Conclusion on FastAPI:** Replacing FastAPI would require rewriting the entire routing and validation layer. Furthermore, our project heavily uses `pydantic-ai`, which inherently ties us to the `pydantic` ecosystem regardless of the web framework. Therefore, replacing FastAPI does not solve the underlying `pydantic-core` blocker unless we also rip out our core LLM agent logic (`pydantic-ai`).

### Upgrading Pydantic
In an attempt to resolve the `pydantic-core` 3.15 compilation failure, we upgraded `pydantic-core` to its absolute latest version (`v2.48.0` / PyO3 `v0.27.x`) and downgraded it to older versions (`v2.27.2` / PyO3 `v0.22.x`).

Both approaches fail, but for different reasons that point to the same underlying problem:
1. **Latest Versions (PyO3 v0.27):** Fail because `_PyCFrame` and internal type structures (`tp_new`, `tp_base`) were removed or altered in CPython 3.15.
2. **Older Versions (PyO3 v0.22 via `jiter`):** Fail because CPython 3.15 completely removed the `PyUnicode_New`, `PyUnicode_KIND`, and `PyUnicode_1BYTE_KIND` macros from the C-API.

Therefore, upgrading or downgrading Pydantic and `pydantic-core` does not resolve the Python 3.15 compatibility issue. We are fundamentally blocked until `PyO3` releases a patch that correctly implements the new Python 3.15 C-API, and `pydantic-core` subsequently upgrades to use that new version of PyO3.
