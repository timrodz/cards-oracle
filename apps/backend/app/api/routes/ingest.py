from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.params import Query
from loguru import logger

from app.data_pipeline.dataset_ingest_json import DatasetIngestJSON
from app.models.api import IngestJsonDatasetParams, OperationMessageResponse

router = APIRouter(prefix="/ingest", tags=["Data pipeline"])


def _ingest_json_dataset_params(
    collection: Annotated[str, Form()],
    limit: Annotated[int | None, Query()] = None,
) -> IngestJsonDatasetParams:
    return IngestJsonDatasetParams(collection=collection, limit=limit)


@router.post("/json-dataset", response_model=OperationMessageResponse)
async def ingest_json_dataset(
    params: Annotated[IngestJsonDatasetParams, Depends(_ingest_json_dataset_params)],
    file: Annotated[UploadFile, File()],
) -> OperationMessageResponse:
    logger.info(f"Ingesting JSON dataset into collection: {params.collection}")

    if not file.filename:
        # Should not happen with UploadFile unless client behaves weirdly
        raise HTTPException(status_code=400, detail="Filename is missing.")

    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")

    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are supported.")

    try:
        ingestion = DatasetIngestJSON()
        # file.file is a SpooledTemporaryFile which is file-like
        # We need to ensure we're at the beginning of the file, though usually we are
        file.file.seek(0)

        ingestion.run_pipeline(
            file_obj=file.file, collection_name=params.collection, limit=params.limit
        )
        return OperationMessageResponse(
            message="Dataset ingestion completed successfully."
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
