import json
from collections.abc import Iterator
from typing import IO, Any, Dict, Optional

from loguru import logger
from pydantic import ValidationError
from pymongo import ReplaceOne

from app.core.config import db_settings
from app.core.db import database
from app.models.scryfall import ScryfallCard


class DatasetIngestJSON:
    def __load_json_file_as_record(self, file_obj: IO) -> Dict[str, Any]:
        logger.info("Loading dataset from stream into single JSON record")

        data = json.load(file_obj)
        if isinstance(data, list):
            raise ValueError(f"Expected single record, got {type(data)}")
        return data

    def __load_json_file_as_list(self, file_obj: IO) -> list[Dict[str, Any]]:
        logger.info("Loading dataset from stream into list of JSON records")

        data = json.load(file_obj)
        if not isinstance(data, list):
            raise ValueError(f"Expected record list, got {type(data)}")
        return data

    def __parse_dataset(
        self, dataset: list[Dict[str, Any]], *, limit: Optional[int]
    ) -> Iterator[ScryfallCard]:
        """
        Converts objects of the same data shape into an iterable class

        TODO:
        1. Pass custom validator - identify using literal as parameter. How would it work for typing?
        """
        logger.debug(f"Parsing dataset (limit={limit})")
        yielded = 0
        for card in dataset:
            try:
                validated_card = ScryfallCard.model_validate(card)
            except ValidationError as exc:
                logger.warning("Invalid record", exc)
                continue
            yield validated_card
            yielded += 1
            if limit is not None and yielded >= limit:
                return

    def __upsert_records(
        self, *, records: list[ScryfallCard], collection_name: str
    ) -> bool:
        """
        TODO:
        1. If the record has a non-mongo ID field (id) map it to `_id` (Mongo compatible)
        """
        operations = [
            ReplaceOne(
                {"_id": record.id},
                record.model_dump(exclude={"id"}),
                upsert=True,
            )
            for record in records
        ]
        if not operations:
            return False

        collection = database.get_collection(collection_name)
        collection.bulk_write(operations, ordered=False)
        logger.info(f"Upserted {len(records)} cards")
        return True

    def run_pipeline(
        self, *, file_obj: IO, collection_name: str, limit: Optional[int]
    ) -> None:
        """
        TODO
        1. Parameterize for:
            - single/list of JSON records
            - model to parse for data validation (optional, maybe users don't want to parse)
        """

        total_records_processed = 0
        record_batch: list[ScryfallCard] = []

        dataset = self.__load_json_file_as_list(file_obj)
        for parsed_record in self.__parse_dataset(dataset, limit=limit):
            total_records_processed += 1
            record_batch.append(parsed_record)
            if len(record_batch) >= db_settings.batch_size:
                self.__upsert_records(
                    records=record_batch, collection_name=collection_name
                )
                record_batch.clear()

        if record_batch:
            self.__upsert_records(records=record_batch, collection_name=collection_name)
            record_batch.clear()

        logger.info(f"Total cards read: {total_records_processed}")
