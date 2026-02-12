from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.params import Query
from loguru import logger

from app.data_pipeline.dataset_ingest_json import DatasetIngestJSON

router = APIRouter(prefix="/ingest", tags=["Data pipeline"])


@router.post("/json-dataset")
async def ingest_json_dataset(
    collection: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    limit: Annotated[int | None, Query()] = None,
):
    logger.info(f"Ingesting JSON dataset into collection: {collection}")

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
            file_obj=file.file, collection_name=collection, limit=limit
        )
        return {"message": "Dataset ingestion completed successfully."}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
