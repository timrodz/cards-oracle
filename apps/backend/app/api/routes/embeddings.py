from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from loguru import logger

from app.core.chunk_mappings import extract_chunk_mapping_fields
from app.core.db import database
from app.data_pipeline.embeddings.create_chunks import (
    run_pipeline_create_embedding_chunks,
)
from app.data_pipeline.embeddings.generate_from_chunks import (
    run_pipeline_generate_embeddings_from_chunks,
)
from app.models.api import (
    CreateEmbeddingChunksParams,
    GenerateEmbeddingsParams,
    OperationMessageResponse,
)

router = APIRouter(
    prefix="/data-pipeline/embeddings", tags=["Data pipeline", "Embeddings"]
)


def __create_embedding_chunks_params(
    source_collection: Annotated[str, Form()],
    target_collection: Annotated[str, Form()],
    chunk_mappings: Annotated[str, Form()],
    limit: Annotated[int | None, Query()] = None,
) -> CreateEmbeddingChunksParams:
    return CreateEmbeddingChunksParams(
        source_collection=source_collection,
        target_collection=target_collection,
        chunk_mappings=chunk_mappings,
        limit=limit,
    )


def __generate_embeddings_params(
    target_collection: Annotated[str, Form()],
    limit: Annotated[int | None, Query()] = None,
    normalize: Annotated[bool, Form()] = True,
) -> GenerateEmbeddingsParams:
    return GenerateEmbeddingsParams(
        collection=target_collection,
        limit=limit,
        normalize_embeddings=normalize,
    )


@router.post("/chunks", response_model=OperationMessageResponse)
async def create_embedding_chunks(
    params: Annotated[
        CreateEmbeddingChunksParams, Depends(__create_embedding_chunks_params)
    ],
) -> OperationMessageResponse:
    logger.info(
        "Starting embedding chunks creation: "
        f"source={params.source_collection}, target={params.target_collection}"
    )

    try:
        # Validate mappings to verify requested fields exist in the DB
        collection_properties = set(
            database.get_collection_properties(collection=params.source_collection)
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

        # Synchronous call as requested for MVP, though long-running
        run_pipeline_create_embedding_chunks(
            source_collection=params.source_collection,
            target_collection=params.target_collection,
            chunk_mappings=params.chunk_mappings,
            limit=params.limit,
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


@router.post("/generate-from-chunks", response_model=OperationMessageResponse)
async def generate_embeddings_from_chunks(
    params: Annotated[GenerateEmbeddingsParams, Depends(__generate_embeddings_params)],
) -> OperationMessageResponse:
    try:
        run_pipeline_generate_embeddings_from_chunks(
            target_collection=params.collection,
            normalize_embeddings=params.normalize_embeddings,
            limit=params.limit,
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
