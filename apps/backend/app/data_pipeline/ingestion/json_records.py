import json
from typing import IO, Any, Dict, Iterator, Optional

from elasticsearch import AsyncElasticsearch
from loguru import logger
from pymongo import UpdateOne

from app.core.config import db_settings
from app.core.db import Database
from app.models.scryfall import ScryfallCard
from app.services.card_indexer import index_cards

json_type = Dict[str, Any]

_db_instance: Optional[Database] = None


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


def _get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


async def __upsert_records(
    *, records: list[json_type], collection: str, es: Optional[AsyncElasticsearch] = None
) -> bool:
    """
    Upserts records into MongoDB and optionally indexes them in Elasticsearch.
    """
    if not records:
        return False

    # Prepare MongoDB operations
    operations = []
    cards_for_es = []

    for record in records:
        # For Scryfall cards, we use 'id' as the unique identifier
        record_id = record.get("id")
        if record_id:
            operations.append(
                UpdateOne({"id": record_id}, {"$set": record}, upsert=True)
            )
            if collection == db_settings.cards_collection:
                try:
                    cards_for_es.append(ScryfallCard(**record))
                except Exception as e:
                    logger.warning(f"Failed to parse record as ScryfallCard: {e}")
        else:
            # Fallback for non-Scryfall records if any
            operations.append(UpdateOne(record, {"$set": record}, upsert=True))

    db_collection = _get_db().get_collection(collection)
    db_collection.bulk_write(operations, ordered=False)
    logger.info(f"Upserted {len(records)} records into MongoDB collection: {collection}")

    # Index in Elasticsearch if it's the cards collection and ES client is provided
    if es and cards_for_es and collection == db_settings.cards_collection:
        logger.info(f"Indexing {len(cards_for_es)} cards into Elasticsearch")
        await index_cards(cards_for_es, es)

    return True


async def run_pipeline_insert_json_dataset(
    *,
    file_obj: IO,
    collection: str,
    limit: Optional[int],
    es: Optional[AsyncElasticsearch] = None,
) -> None:
    """
    Inserts a JSON dataset into a MongoDB collection and syncs with Elasticsearch.
    """

    total_records_processed = 0
    record_batch: list[json_type] = []

    dataset = __load_json_file_as_list(file_obj)
    for parsed_record in __parse_dataset(dataset, limit=limit):
        total_records_processed += 1
        record_batch.append(parsed_record)
        if len(record_batch) >= db_settings.batch_size:
            await __upsert_records(records=record_batch, collection=collection, es=es)
            record_batch.clear()

    if record_batch:
        await __upsert_records(records=record_batch, collection=collection, es=es)
        record_batch.clear()

    logger.info(f"Total records processed: {total_records_processed}")
