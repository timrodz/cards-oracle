import json
from typing import IO, Any, Dict, Iterator, Optional

from loguru import logger
from pymongo import InsertOne

from app.core.config import db_settings
from app.core.db import database

json_type = Dict[str, Any]


def __load_json_file_as_list(file_obj: IO) -> list[json_type]:
    logger.info("Loading dataset from stream into list of JSON records")

    data = json.load(file_obj)
    if not isinstance(data, list):
        raise ValueError(f"Expected record list, got {type(data)}")
    return data


def __parse_dataset(
    dataset: list[json_type], *, limit: Optional[int]
) -> Iterator[json_type]:
    logger.debug(f"Parsing dataset (limit={limit})")
    yielded = 0
    for data in dataset:
        yield data
        yielded += 1
        if limit is not None and yielded >= limit:
            return


def __upsert_records(*, records: list[json_type], collection: str) -> bool:
    """
    TODO:
    1. If the record has a non-mongo ID field (id) map it to `_id` (Mongo compatible)
    """
    operations = [InsertOne(record) for record in records]
    if not operations:
        return False

    db_collection = database.get_collection(collection)
    db_collection.bulk_write(operations, ordered=False)
    logger.info(f"Upserted {len(records)} cards")
    return True


def run_pipeline_insert_json_dataset(
    *, file_obj: IO, collection: str, limit: Optional[int]
) -> None:
    """
    Inserts a JSON dataset into a MongoDB collection.
    TODO
    1. Parameterize for:
        - single/list of JSON records
        - model to parse for data validation (optional, maybe users don't want to parse)
    """

    total_records_processed = 0
    record_batch: list[json_type] = []

    dataset = __load_json_file_as_list(file_obj)
    for parsed_record in __parse_dataset(dataset, limit=limit):
        total_records_processed += 1
        record_batch.append(parsed_record)
        if len(record_batch) >= db_settings.batch_size:
            __upsert_records(records=record_batch, collection=collection)
            record_batch.clear()

    if record_batch:
        __upsert_records(records=record_batch, collection=collection)
        record_batch.clear()

    logger.info(f"Total cards read: {total_records_processed}")
