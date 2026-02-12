from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from loguru import logger

from app.core.db import database
from app.data_pipeline.create_embeddings import Embeddings
from app.models.api import (
    CreateEmbeddingsParams,
    CreateSearchIndexParams,
    OperationMessageResponse,
)
from app.models.embedding import Similarity

router = APIRouter(prefix="/embeddings", tags=["Data pipeline"])


def _create_embeddings_params(
    source_collection: Annotated[str, Form()],
    target_collection: Annotated[str, Form()],
    limit: Annotated[int | None, Query()] = None,
    normalize: Annotated[bool, Form()] = True,
) -> CreateEmbeddingsParams:
    return CreateEmbeddingsParams(
        source_collection=source_collection,
        target_collection=target_collection,
        limit=limit,
        normalize=normalize,
    )


def _create_search_index_params(
    collection_name: Annotated[str, Form()],
    collection_field: Annotated[str, Form()],
    similarity: Annotated[Similarity, Form()] = "dot_product",
) -> CreateSearchIndexParams:
    return CreateSearchIndexParams(
        collection_name=collection_name,
        collection_field=collection_field,
        similarity=similarity,
    )


@router.post("", response_model=OperationMessageResponse)
async def create_embeddings(
    params: Annotated[CreateEmbeddingsParams, Depends(_create_embeddings_params)],
) -> OperationMessageResponse:
    logger.info(
        "Starting embeddings creation: "
        f"source={params.source_collection}, target={params.target_collection}"
    )

    try:
        embeddings = Embeddings()
        # Synchronous call as requested for MVP, though long-running
        embeddings.run_pipeline(
            source_collection=params.source_collection,
            target_collection=params.target_collection,
            limit=params.limit,
            normalize=params.normalize,
        )
        return OperationMessageResponse(
            message="Embeddings creation completed successfully."
        )
    except Exception as e:
        logger.error(f"Embeddings creation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Embeddings creation failed: {str(e)}"
        )


@router.post("/search_index", response_model=OperationMessageResponse)
async def create_search_index_endpoint(
    params: Annotated[CreateSearchIndexParams, Depends(_create_search_index_params)],
) -> OperationMessageResponse:
    try:
        database.create_vector_search_index(
            collection_name=params.collection_name,
            collection_field=params.collection_field,
            similarity=params.similarity,
        )
        return OperationMessageResponse(message="Search index creation initiated.")
    except Exception as e:
        logger.error(f"Search index creation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Search index creation failed: {str(e)}"
        )
