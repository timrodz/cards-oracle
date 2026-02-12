from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Query
from loguru import logger

from app.core.db import database
from app.data_pipeline.create_embeddings import Embeddings
from app.models.embedding import Similarity

router = APIRouter(prefix="/embeddings", tags=["Data pipeline"])


@router.post("")
async def create_embeddings(
    source_collection: Annotated[str, Form()],
    target_collection: Annotated[str, Form()],
    limit: Annotated[int | None, Query()] = None,
    normalize: Annotated[bool, Form()] = True,
):
    logger.info(
        f"Starting embeddings creation: source={source_collection}, target={target_collection}"
    )

    try:
        embeddings = Embeddings()
        # Synchronous call as requested for MVP, though long-running
        embeddings.run_pipeline(
            source_collection=source_collection,
            target_collection=target_collection,
            limit=limit,
            normalize=normalize,
        )
        return {"message": "Embeddings creation completed successfully."}
    except Exception as e:
        logger.error(f"Embeddings creation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Embeddings creation failed: {str(e)}"
        )


@router.post("/search_index")
async def create_search_index_endpoint(
    collection_name: Annotated[str, Form()],
    collection_field: Annotated[str, Form()],
    similarity: Annotated[Similarity, Form()] = "dot_product",
):
    try:
        database.create_vector_search_index(
            collection_name=collection_name,
            collection_field=collection_field,
            similarity=similarity,
        )
        return {"message": "Search index creation initiated."}
    except Exception as e:
        logger.error(f"Search index creation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Search index creation failed: {str(e)}"
        )
