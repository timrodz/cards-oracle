# Card Oracle backend

An application that lets users retrieve data about Magic: The Gathering cards.

![image](docs/architecture/high-level-architecture.png)

![image](docs/architecture/application-features.png)

## Development Setup

### Environment

- Python `3.12`
- MongoDB `8.2+` (Vector Search)
- Mongo Atlas CLI `1.52`
- LLM provider (`LLM_PROVIDER`):
  - Ollama (`ollama`) for local inference
  - Z.ai (`zai`) for hosted inference
- Embedding provider (`EMBEDDING_PROVIDER`):
  - Sentence Transformers (`sentence_transformers`) for local embeddings
  - OpenAI (`openai`) for hosted embeddings

### Embeddings

Embedding generation is provider-agnostic in code paths (data pipeline + query-time RAG).

Provider selection:

- `EMBEDDING_PROVIDER="sentence_transformers"` (default)
- `EMBEDDING_PROVIDER="openai"`

Model settings:

- `EMBEDDING_MODEL_NAME`
- `EMBEDDING_MODEL_PATH` (ignored by OpenAI provider)
- `EMBEDDING_MODEL_DIMENSIONS`
- `EMBEDDING_VECTOR_SEARCH_LIMIT`

Backward-compatible env aliases still supported:

- `EMBEDDING_TRANSFORMER_MODEL_NAME`
- `EMBEDDING_TRANSFORMER_MODEL_PATH`
- `EMBEDDING_TRANSFORMER_MODEL_DIMENSIONS`

For local Sentence Transformers models:

```bash
uvx hf auth login
uvx hf download <model> --local-dir models/<model>
```

For OpenAI embeddings:

- Uses `LLM_API_KEY` for authentication.
- Uses optional `LLM_ENDPOINT` as OpenAI `base_url`.
- Sends configured dimensions directly with the OpenAI embeddings request.

Current limitation: because OpenAI embeddings reuse `LLM_API_KEY`, running `LLM_PROVIDER=zai` with `EMBEDDING_PROVIDER=openai` requires a single shared key value and does not support separate remote provider keys.

### RAG LLMs

The backend requires `LLM_PROVIDER` to be explicitly set. See root docs in `docs/llms` for provider setup.

`LLM_MODEL_NAME` is the model identifier.

### Installation

1. Install `uv`
2. Install Python: `uv python install`

```bash
uv venv
source .venv/bin/activate
uv sync
```

**Note:** This backend connects to MongoDB. Prefer running via `docker compose`.

### Development

Run the FastAPI server:

```bash
fastapi dev app/main.py
```

Navigate to `http://localhost:8000/docs` and use the endpoints there.
