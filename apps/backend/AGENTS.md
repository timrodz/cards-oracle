# Repository Guidelines

## Project Structure & Module Organization

Core backend code lives in `app/`.

- `app/main.py`: FastAPI entrypoint and routes.
- `app/core`: Core app logic and integrations.
- `app/core/config.py`: Environment variables.
- `app/core/llms/`: LLM provider interfaces and implementations.
- `app/core/embeddings/`: Embedding provider interfaces and implementations.
- `app/core/rag/`: Retrieval and response orchestration.
- `app/models/`: Pydantic models for API, dataset, embeddings, and LLM payloads.
- `app/data_pipeline/`: ingestion and embedding creation pipelines.

Supporting resources:

- `models/`: local embedding model artifacts.
- `docs/`: architecture diagrams, RAG notes, and index specs.
- `tests/`: mirrors `app/` with `core/`, `core/embeddings/`, `core/rag/`, and `data_pipeline/`.

## Build, Test, and Development Commands

Use Python 3.12 and `uv`.

- `uv venv && source .venv/bin/activate`: create and activate local environment.
- `uv sync` (or `uv pip install -r requirements.txt`): install dependencies.
- `fastapi dev app/main.py`: run the API locally.
- `uv run ruff check .`: lint.
- `uv run mypy app`: type-check.
- `uv run pytest`: run test suite.

Always run `ruff`, `mypy`, and `pytest` before confirming work is complete.

## Development Workflow Rules

- Services must be accessed through generic interfaces; providers must remain hot-swappable.
- For external APIs, implement rate-limit handling (catch + retry/backoff) instead of one-shot calls.
- Add logging across important flows:
  - `debug`: provider instantiation and provider-selection details.
  - `info`: major path execution milestones and high-value operations.
- Prefer Pydantic models/types over untyped structures, and avoid `Any` whenever practical.

## Coding Style & Naming Conventions

- Follow PEP 8, 4-space indentation, and explicit type hints.
- Use `snake_case` for functions/modules, `PascalCase` for classes, and descriptive config names.
- Keep FastAPI route handlers thin; move logic into `app/core.py` or pipeline modules.
- Validate and serialize data through Pydantic models in `app/models/`.
- Use Pydantic utilities and custom types aggressively.
- Avoid `Any` unless there is no practical typed alternative.
- Use `loguru` as the logger.
- Functions that have more than 1 parameter must declare named parameters (excluding `self`).

## Testing Guidelines

`pytest` is the expected test runner.

- Place tests under `tests/` mirroring `app/` paths (example: `tests/data_pipeline/test_create_embeddings.py`).
- Name tests `test_*.py` and prefer behavior-focused test names.
- Run `uv run pytest` locally; add regression tests for parser, embedding, and query logic changes.

## Commit & Pull Request Guidelines

Repository history uses Conventional Commits (`feat:`, `refactor:`, `chore:`, `docs:`).

- Keep commit messages imperative and scoped (example: `feat: add pydantic search response model`).
- In PRs, include: summary, key changes, validation steps run (`ruff`, `mypy`, `pytest`), and linked issue/ticket.
- For API or pipeline behavior changes, include sample request/response or log snippets.

## Security & Configuration Tips

- Copy `.env.example` to `.env`; never commit secrets.
- Keep `MONGODB_URI`, model settings, and provider settings environment-driven via `app/core/config.py`.
- Large local artifacts (`datasets/`, `models/`, `logs/`) should stay out of git.
