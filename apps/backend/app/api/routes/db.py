from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from loguru import logger

from app.core.db import Database, get_db
from app.models.api import (
    CreateSearchIndexParams,
    OperationMessageResponse,
)
from app.models.embedding import Similarity

router = APIRouter(prefix="/db", tags=["Database"])


def __create_search_index_params(
    collection: Annotated[str, Form()],
    collection_embeddings_field: Annotated[str, Form()],
    similarity: Annotated[Similarity, Form()] = "dot_product",
) -> CreateSearchIndexParams:
    return CreateSearchIndexParams(
        collection=collection,
        collection_embeddings_field=collection_embeddings_field,
        similarity=similarity,
    )


@router.get("/collections/{collection}/properties", response_model=list[str])
async def get_collection_properties(
    collection: str,
    db: Database = Depends(get_db),
) -> list[str]:
    try:
        return db.get_collection_properties(collection=collection)
    except Exception as e:
        logger.error(f"Collection property retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Collection property retrieval failed: {str(e)}"
        )


@router.post("/search-index", response_model=OperationMessageResponse)
async def create_search_index_endpoint(
    params: Annotated[CreateSearchIndexParams, Depends(__create_search_index_params)],
    db: Database = Depends(get_db),
) -> OperationMessageResponse:
    try:
        db.create_vector_search_index(
            collection=params.collection,
            collection_embeddings_field=params.collection_embeddings_field,
            similarity=params.similarity,
        )
        return OperationMessageResponse(message="Search index creation initiated.")
    except Exception as e:
        logger.error(f"Search index creation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Search index creation failed: {str(e)}"
        )
