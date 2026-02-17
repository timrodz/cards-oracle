from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from loguru import logger

from app.core.chunk_mappings import extract_chunk_mapping_fields
from app.core.db import database
from app.data_pipeline.create_embeddings import Embeddings
from app.models.api import (
    CreateJsonEmbeddingParams,
    CreateSearchIndexParams,
    OperationMessageResponse,
)
from app.models.embedding import Similarity

router = APIRouter(prefix="/embeddings", tags=["Data pipeline"])


def _create_embeddings_params(
    source_collection: Annotated[str, Form()],
    target_collection: Annotated[str, Form()],
    chunk_mappings: Annotated[str | None, Form()] = None,
    limit: Annotated[int | None, Query()] = None,
    normalize: Annotated[bool, Form()] = True,
) -> CreateJsonEmbeddingParams:
    return CreateJsonEmbeddingParams(
        source_collection=source_collection,
        target_collection=target_collection,
        chunk_mappings=chunk_mappings,
        limit=limit,
        normalize=normalize,
    )


def _create_search_index_params(
    collection_name: Annotated[str, Form()],
    collection_embeddings_field: Annotated[str, Form()],
    similarity: Annotated[Similarity, Form()] = "dot_product",
) -> CreateSearchIndexParams:
    return CreateSearchIndexParams(
        collection_name=collection_name,
        collection_embeddings_field=collection_embeddings_field,
        similarity=similarity,
    )


@router.post("", response_model=OperationMessageResponse)
async def create_embeddings(
    params: Annotated[CreateJsonEmbeddingParams, Depends(_create_embeddings_params)],
) -> OperationMessageResponse:
    logger.info(
        "Starting embeddings creation: "
        f"source={params.source_collection}, target={params.target_collection}"
    )

    try:
        # Validate mappings to verify requested fields exist in the DB
        if params.chunk_mappings is not None:
            collection_properties = set(
                database.get_collection_properties(
                    collection_name=params.source_collection
                )
            )
            mapped_fields = extract_chunk_mapping_fields(
                chunk_mappings=params.chunk_mappings
            )
            missing_fields = sorted(mapped_fields - collection_properties)
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid chunk_mappings fields for collection "
                        f"{params.source_collection}: {', '.join(missing_fields)}"
                    ),
                )

        embeddings = Embeddings()
        # Synchronous call as requested for MVP, though long-running
        embeddings.run_pipeline(
            source_collection=params.source_collection,
            target_collection=params.target_collection,
            chunk_mappings=params.chunk_mappings,
            limit=params.limit,
            normalize=params.normalize,
        )
        return OperationMessageResponse(
            message="Embeddings creation completed successfully."
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
            collection_embeddings_field=params.collection_embeddings_field,
            similarity=params.similarity,
        )
        return OperationMessageResponse(message="Search index creation initiated.")
    except Exception as e:
        logger.error(f"Search index creation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Search index creation failed: {str(e)}"
        )
