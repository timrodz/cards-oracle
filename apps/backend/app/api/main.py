from fastapi import APIRouter

from app.api.routes import cards, db, embeddings, ingest, search

api_router = APIRouter()
api_router.include_router(cards.router)
api_router.include_router(search.router)
api_router.include_router(ingest.router)
api_router.include_router(embeddings.router)
api_router.include_router(db.router)
