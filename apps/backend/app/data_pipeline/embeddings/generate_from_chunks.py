import multiprocessing
import os
from functools import partial
from typing import Iterator, Optional

from loguru import logger
from pymongo import ReplaceOne

from app.core.config import db_settings
from app.core.db import database
from app.core.embeddings.utils import get_embedding_provider
from app.models.db import (
    EmptyEmbeddingRecord,
    GeneratedEmbeddingRecord,
)


def __upsert_records(
    collection: str,
    records: list[GeneratedEmbeddingRecord],
) -> None:
    if not records:
        return

    db_collection = database.get_collection(collection)

    operations = [
        ReplaceOne(
            {"_id": rec.mongo_id},
            rec.model_dump(by_alias=True, exclude_none=True),
            upsert=True,
        )
        for rec in records
    ]

    db_collection.bulk_write(operations, ordered=False)
    logger.info(f"Upserted {len(records)} records ready for embeddings")


def __load_db_records(
    source_collection: str, *, limit: Optional[int] = None
) -> Iterator[list[EmptyEmbeddingRecord]]:
    collection = database.get_collection(source_collection)
    logger.debug(
        f"Loading records with chunks from collection: {source_collection} with limit {limit}"
    )
    cursor = collection.find()

    if limit is not None:
        cursor = cursor.limit(limit)

    batch: list[EmptyEmbeddingRecord] = []
    for record in cursor:
        mongo_rec = EmptyEmbeddingRecord.model_validate(record, extra="ignore")
        batch.append(mongo_rec)
        if len(batch) >= db_settings.batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def __generate_and_create_embeddings(
    record: EmptyEmbeddingRecord,
    *,
    embedding_vector: list[float],
) -> GeneratedEmbeddingRecord:
    """
    Resource intensive operation due to generating embeddings.
    """
    return GeneratedEmbeddingRecord(
        _id=record.mongo_id,
        summary=record.summary,
        embeddings=embedding_vector,
    )


def process_batch(
    records: list[EmptyEmbeddingRecord],
    *,
    target_collection: str,
    normalize_embeddings: bool = True,
):
    embedder = get_embedding_provider()
    summaries = [record.summary for record in records]
    embedding_vectors = embedder.embed_texts(summaries, normalize=normalize_embeddings)

    embeddings = [
        __generate_and_create_embeddings(
            db_record,
            embedding_vector=embedding_vector,
        )
        for db_record, embedding_vector in zip(records, embedding_vectors, strict=True)
    ]
    __upsert_records(target_collection, embeddings)


def run_pipeline_generate_embeddings_from_chunks(
    *,
    target_collection: str,
    normalize_embeddings: bool = True,
    limit: Optional[int] = None,
) -> None:
    logger.info(
        "Starting embeddings pipeline: Generate embeddings from chunks"
        f"target collection={target_collection}, limit={limit}, normalize embeddings={normalize_embeddings}"
    )

    batches = list(__load_db_records(target_collection, limit=limit))
    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        partial_worker = partial(
            process_batch,
            target_collection=target_collection,
            normalize_embeddings=normalize_embeddings,
        )
        pool.map(partial_worker, batches)
