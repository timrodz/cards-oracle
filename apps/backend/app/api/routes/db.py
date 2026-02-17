from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.db import database

router = APIRouter(prefix="/db", tags=["Database"])


@router.get("/collections/{collection_name}/properties", response_model=list[str])
async def get_collection_properties(collection_name: str) -> list[str]:
    try:
        return database.get_collection_properties(collection_name=collection_name)
    except Exception as e:
        logger.error(f"Collection property retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Collection property retrieval failed: {str(e)}"
        )
