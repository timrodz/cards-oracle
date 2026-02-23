# Backend Python Standards Review 001 (`apps/backend`)

## Summary
The backend is readable and typed in many places, but there are several standards gaps around async design, error handling, model defaults, and dependency lifecycle management that will make reliability and maintainability harder as the service grows.

## Findings

### PY-001: Blocking/long-running work is executed directly in async route handlers
- Severity: High
- Evidence:
  - `apps/backend/app/api/routes/ingest.py:26`
  - `apps/backend/app/api/routes/ingest.py:46`
  - `apps/backend/app/api/routes/embeddings.py:52`
  - `apps/backend/app/api/routes/embeddings.py:81`
  - `apps/backend/app/api/routes/embeddings.py:102`
  - `apps/backend/app/api/routes/embeddings.py:106`
- Why this matters:
  - Handlers are `async`, but they call heavy synchronous pipelines directly. This blocks the event loop and degrades API concurrency under load.
- Recommendation:
  - Move heavy jobs to background workers/queues, or offload synchronous work with `asyncio.to_thread` where appropriate.

### PY-002: Response model contract mismatch on search endpoint
- Severity: High
- Evidence:
  - `apps/backend/app/api/routes/search.py:55`
  - `apps/backend/app/api/routes/search.py:64`
  - `apps/backend/app/core/rag/search.py:131`
  - `apps/backend/app/core/rag/search.py:143`
  - `apps/backend/app/core/rag/search.py:152`
- Why this matters:
  - The route declares `response_model=SearchResponse`, but the underlying search returns `None` when no result/context is found. `SearchResponse.model_validate(result)` can fail at runtime.
- Recommendation:
  - Return a typed empty/no-result response or raise a specific HTTP status (for example 404/204) and align route typing to actual behavior.

### PY-003: Mutable defaults in Pydantic models
- Severity: Medium
- Evidence:
  - `apps/backend/app/models/db.py:16`
  - `apps/backend/app/models/db.py:22`
  - `apps/backend/app/models/db.py:29`
  - `apps/backend/app/models/scryfall.py:80`
- Why this matters:
  - Using `[]` as a class-level default is a Python anti-pattern and can lead to shared-state surprises depending on model behavior/usage.
- Recommendation:
  - Use `Field(default_factory=list)` for list defaults.

### PY-004: Over-broad `except Exception` usage across API boundaries
- Severity: Medium
- Evidence:
  - `apps/backend/app/api/routes/ingest.py:52`
  - `apps/backend/app/api/routes/embeddings.py:94`
  - `apps/backend/app/api/routes/embeddings.py:118`
  - `apps/backend/app/api/routes/db.py:32`
  - `apps/backend/app/api/routes/db.py:50`
- Why this matters:
  - Catch-all exception handling makes failure modes ambiguous, mixes operational and validation failures, and complicates observability and retries.
- Recommendation:
  - Catch expected exception types explicitly and centralize error translation via shared exception handlers.

### PY-005: Stateful singletons initialized at import time
- Severity: Medium
- Evidence:
  - `apps/backend/app/core/db.py:82`
  - `apps/backend/app/api/routes/search.py:23`
- Why this matters:
  - Import-time initialization of DB client and service objects reduces test isolation and makes lifecycle management (startup/shutdown, reconnect, override) harder.
- Recommendation:
  - Use FastAPI dependency injection and lifespan hooks for managed instantiation and teardown.

### PY-006: Full dataset materialization before multiprocessing
- Severity: Medium
- Evidence:
  - `apps/backend/app/data_pipeline/embeddings/create_chunks.py:104`
  - `apps/backend/app/data_pipeline/embeddings/generate_from_chunks.py:123`
- Why this matters:
  - `batches = list(...)` loads all records into memory before processing, increasing memory pressure and reducing scalability.
- Recommendation:
  - Stream batches to workers incrementally (for example `imap_unordered`) instead of pre-materializing all batches.
