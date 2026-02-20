# ──────────────────────────────────────────────
# Stage 1: Install dependencies with uv
# ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# llama-cpp-python builds from source on many platforms and requires a compiler toolchain.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (cached unless lock files change)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .
RUN uv sync --frozen --no-dev

# ──────────────────────────────────────────────
# Stage 2: Slim runtime image
# ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PORT=8000

# Copy the virtual environment and app code from the builder
COPY --from=builder /app /app

# Place the venv's bin on PATH so `uvicorn` is found
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE ${PORT}

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
