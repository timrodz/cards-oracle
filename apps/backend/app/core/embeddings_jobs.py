import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from dagster import DagsterInstance
from loguru import logger
from pymongo.collection import Collection

from app.core.config import dagster_settings
from app.core.db import database
from app.dagster.jobs import create_embeddings_job
from app.models.api import (
    CreateEmbeddingsJobResponse,
    CreateJsonEmbeddingParams,
    GetEmbeddingsJobResponse,
)


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


class EmbeddingsJobService:
    def __init__(self):
        self._job_collection: Collection = database.get_collection("embedding_jobs")
        self._executor = ThreadPoolExecutor(
            max_workers=dagster_settings.embeddings_max_workers
        )

    def submit_job(
        self, *, params: CreateJsonEmbeddingParams
    ) -> CreateEmbeddingsJobResponse:
        job_id = str(uuid4())
        dagster_run_id = str(uuid4())
        now = _utc_now()

        self._job_collection.insert_one(
            {
                "_id": job_id,
                "status": "queued",
                "dagster_run_id": dagster_run_id,
                "request": params.model_dump(),
                "error": None,
                "created_at": now,
                "updated_at": now,
            }
        )

        try:
            self._executor.submit(
                self._run_embeddings_job,
                job_id=job_id,
                dagster_run_id=dagster_run_id,
                payload=params.model_dump(),
            )
        except Exception as exc:
            logger.exception("Failed to submit embeddings background task")
            self._update_job_status(
                job_id=job_id,
                status="failed_submission",
                error=str(exc),
            )
            raise

        return CreateEmbeddingsJobResponse(
            message="Embeddings task accepted.",
            job_id=job_id,
            status="queued",
            dagster_run_id=dagster_run_id,
        )

    def get_job(self, *, job_id: str) -> GetEmbeddingsJobResponse | None:
        document = self._job_collection.find_one({"_id": job_id})
        if document is None:
            return None

        request: dict[str, Any] = document.get("request", {})

        return GetEmbeddingsJobResponse(
            job_id=str(document["_id"]),
            status=document["status"],
            dagster_run_id=document["dagster_run_id"],
            dagster_status=self._get_dagster_run_status(
                dagster_run_id=document["dagster_run_id"]
            ),
            source_collection=request["source_collection"],
            target_collection=request["target_collection"],
            chunk_mappings=request.get("chunk_mappings"),
            limit=request.get("limit"),
            normalize=request.get("normalize", True),
            error=document.get("error"),
        )

    def _run_embeddings_job(
        self,
        *,
        job_id: str,
        dagster_run_id: str,
        payload: dict[str, Any],
    ) -> None:
        params = CreateJsonEmbeddingParams.model_validate(payload)
        self._update_job_status(job_id=job_id, status="running")

        instance = _get_dagster_instance()
        run_config = {
            "ops": {
                "create_embeddings_op": {
                    "config": {
                        "source_collection": params.source_collection,
                        "target_collection": params.target_collection,
                        "chunk_mappings": params.chunk_mappings,
                        "limit": params.limit,
                        "normalize": params.normalize,
                    }
                }
            }
        }

        try:
            result = create_embeddings_job.execute_in_process(
                run_config=run_config,
                instance=instance,
                run_id=dagster_run_id,
                raise_on_error=True,
                tags={
                    "job_id": job_id,
                    "source_collection": params.source_collection,
                    "target_collection": params.target_collection,
                },
            )
        except Exception as exc:
            logger.exception("Embeddings Dagster execution failed")
            self._update_job_status(job_id=job_id, status="failed", error=str(exc))
            return

        if result.success:
            self._update_job_status(job_id=job_id, status="succeeded")
            return

        self._update_job_status(
            job_id=job_id,
            status="failed",
            error="Dagster run completed without success.",
        )

    def _get_dagster_run_status(self, *, dagster_run_id: str) -> str | None:
        try:
            instance = _get_dagster_instance()
            dagster_run = instance.get_run_by_id(dagster_run_id)
            if dagster_run is None:
                return None
            return dagster_run.status.value
        except Exception:
            logger.exception("Failed to read Dagster run status")
            return None

    def _update_job_status(
        self,
        *,
        job_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        update_payload: dict[str, Any] = {
            "status": status,
            "updated_at": _utc_now(),
        }
        if error is not None:
            update_payload["error"] = error

        self._job_collection.update_one(
            {"_id": job_id},
            {"$set": update_payload},
        )


def _get_dagster_instance() -> DagsterInstance:
    dagster_home = Path(dagster_settings.home)
    dagster_home.mkdir(parents=True, exist_ok=True)
    os.environ["DAGSTER_HOME"] = str(dagster_home)
    return DagsterInstance.get()


embeddings_job_service = EmbeddingsJobService()

