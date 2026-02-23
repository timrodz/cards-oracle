# Backend Security Review 001 (`apps/backend`)

## Executive summary
Using your stated threat model (single-user/local host or private Docker usage, not internet-exposed), this review excludes authentication hardening as an immediate finding. The highest remaining risks are denial-of-service paths and error-detail leakage that can still impact local stability and become high risk if exposure assumptions change.

## Scope note
Authentication/authorization controls were intentionally excluded per your instruction for non-deployed/local-only operation. If this service is ever exposed beyond a trusted local boundary, missing auth becomes a critical issue and should be addressed before exposure.

## Major findings

### SEC-002: Unbounded file ingestion enables memory-exhaustion DoS
- Severity: Major
- Evidence:
  - `apps/backend/app/api/routes/ingest.py:28`
  - `apps/backend/app/api/routes/ingest.py:38`
  - `apps/backend/app/data_pipeline/ingestion/json_records.py:16`
- Why this is risky:
  - Upload validation only checks filename extension.
  - `json.load(file_obj)` fully materializes attacker-supplied content into memory.
  - There are no request size/multipart limits in app configuration.
- Recommended remediation:
  - Enforce max request body and multipart size limits.
  - Parse JSON incrementally/streaming, not full-buffer.
  - Validate content-type and schema before heavy processing.

### SEC-003: Unthrottled compute-heavy endpoints allow CPU exhaustion
- Severity: Major
- Evidence:
  - `apps/backend/app/api/routes/embeddings.py:51`
  - `apps/backend/app/api/routes/embeddings.py:101`
  - `apps/backend/app/data_pipeline/embeddings/create_chunks.py:105`
  - `apps/backend/app/data_pipeline/embeddings/generate_from_chunks.py:124`
- Why this is risky:
  - Public endpoints trigger multiprocessing pools sized to CPU count.
  - Calls are synchronous and not rate-limited, so repeated requests can starve service resources.
- Recommended remediation:
  - Protect these endpoints with admin-only auth.
  - Add per-client/global rate limiting and concurrency caps.
  - Move long-running work to a queue/background worker with job admission controls.

### SEC-004: Internal error details are returned directly to clients
- Severity: Major
- Evidence:
  - `apps/backend/app/api/routes/ingest.py:54`
  - `apps/backend/app/api/routes/embeddings.py:97`
  - `apps/backend/app/api/routes/embeddings.py:121`
  - `apps/backend/app/api/routes/db.py:35`
  - `apps/backend/app/api/routes/db.py:53`
- Why this is risky:
  - `detail=f"...{str(e)}"` may leak backend internals (collection names, driver messages, infrastructure details) useful for attacker recon.
- Recommended remediation:
  - Return generic client-safe error messages.
  - Log full exception details server-side with correlation IDs.
  - Standardize exception mapping with typed/domain exceptions.
