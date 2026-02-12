from fastapi import APIRouter

from app.api.routes import cards, ingest, search, embeddings

api_router = APIRouter()
api_router.include_router(cards.router)
api_router.include_router(search.router)
api_router.include_router(ingest.router)
api_router.include_router(embeddings.router)
