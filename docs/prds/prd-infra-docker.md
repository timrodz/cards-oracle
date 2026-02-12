# PRD: Infrastructure - Docker

Goals: setup this monorepo so that it can be deployed in a k8s container.

The frontend will be served with NextJS and handles interactivity. The backend is a bit more complex, and it will handle business logic
with Python, FastAPI. The database is MongoDB.

Scope

- Create Dockerfile for building the frontend
- Create Dockerfile for building the backend
- Create docker compose for local development. It needs to run both applications and provision a MongoDB database

## Tech requirements

### Frontend

- Node: 22.18.0
- NextJS: 16.1.6
- Package manager: `bun`

### Backend

- Python: 3.12
- Package manager: `uv`
- Server: `fastAPI`

### Database

- Provider: MongoDB cluster
- Mongo version: 8.2.4
- Atlas CLI: 1.52.0
