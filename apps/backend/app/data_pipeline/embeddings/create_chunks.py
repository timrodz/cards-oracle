import multiprocessing
import os
from functools import partial
from typing import Iterator, Optional

from loguru import logger
from pymongo import ReplaceOne

from app.core.chunk_mappings import render_chunk_mapping
from app.core.config import db_settings
from app.core.db import database
from app.models.db import (
    EmptyEmbeddingRecord,
    MongoCollectionRecord,
)


def __upsert_records(
    collection: str,
    records: list[EmptyEmbeddingRecord],
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
) -> Iterator[list[MongoCollectionRecord]]:
    db_collection = database.get_collection(source_collection)
    logger.debug(
        f"Loading records from collection: {source_collection} with limit {limit}"
    )
    cursor = db_collection.find()

    if limit is not None:
        cursor = cursor.limit(limit)

    batch: list[MongoCollectionRecord] = []
    for record in cursor:
        mongo_rec = MongoCollectionRecord.model_validate(record, extra="allow")
        batch.append(mongo_rec)
        if len(batch) >= db_settings.batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def __create_empty_embedding_chunks(
    source_record: MongoCollectionRecord, chunk_mappings: str
) -> EmptyEmbeddingRecord:
    summary = render_chunk_mapping(
        chunk_mappings=chunk_mappings,
        source_record=source_record,
    )
    return EmptyEmbeddingRecord(
        _id=source_record.mongo_id, summary=summary, embeddings=[]
    )


def process_batch_empty_embeddings(
    records: list[MongoCollectionRecord],
    *,
    target_collection: str,
    chunk_mappings: str,
):
    chunks = [
        __create_empty_embedding_chunks(
            db_record,
            chunk_mappings=chunk_mappings,
        )
        for db_record in records
    ]
    __upsert_records(target_collection, chunks)


def run_pipeline_create_embedding_chunks(
    *,
    source_collection: str,
    target_collection: str,
    chunk_mappings: str,
    limit: Optional[int] = None,
) -> None:
    logger.info(
        "Starting embeddings pipeline. Creating record chunks:",
        f"source={source_collection}, target={target_collection}, limit={limit}",
    )

    batches = list(__load_db_records(source_collection, limit=limit))
    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        partial_worker = partial(
            process_batch_empty_embeddings,
            target_collection=target_collection,
            chunk_mappings=chunk_mappings,
        )
        pool.map(partial_worker, batches)
