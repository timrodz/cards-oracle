# Card Oracle

Monorepo for a multi-purpose RAG project.

## Initial focus

I developed an MVP using a scryfall dataset for Magic: The Gathering cards, so that'll be what I build on for technology. As more features get added, the project will hopefully find a more mature shape.

## Risks

- Creating embeddings is a resource-intensive task, and running workers (Celery) requires a separate app acting as the worker queue. Remediation: Task worker (Celery)

## Features

### RAG search powered by LLMs

#### Supported

- Llama.cpp
- Ollama
- Z.ai (API key)

#### Database: MongoDB

- Convert a JSON dataset to a Mongo collection
- Generate embeddings + vector search indexes for any collection

#### Backend: Python + FastAPI

- Runs all inference and training

#### Frontend: NextJs

- ElevenLabs SDK for real-time calling
- Consumes the backend API

## Development

### Frontend

1. Install the appropriate NPM version found in `.nvmrc`
2. Install `bun`
3. `bun install`

```bash
> bun dev
```

### Backend

1. Install `uv`
2. Install the appropriate Python version found in `.python-version`
3. `uv sync`

```bash
> fastapi dev app/main.py
```

### Database (MongoDB)

Spin up the MongoDB instance with `docker compose`, as it requires a specific deployment that isn't compatible with the generic mongo install. Then connect via `mongosh` or Mongo Compass to verify it works:

```bash
mongosh "mongodb://user:pass@localhost:27017/?directConnection=true"
```

## Build the app

If you just want to run the app, here's the easiest setup:

```bash
> docker-compose up -d --build
> docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```
