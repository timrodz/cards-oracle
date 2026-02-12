import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Iterator, List, Optional

from loguru import logger
from pymongo import ReplaceOne

from app.core.config import app_settings, db_settings
from app.core.db import database
from app.data_pipeline.sentence_transformers import (
    embed_text,
    load_transformer,
)
from app.models.db import CardEmbeddingRecord, ScryfallCardRecord
from app.models.scryfall import ScryfallCardFace


def _process_and_upsert_batch(
    records: List[CardEmbeddingRecord], collection_name: str, normalize_embeddings: bool
) -> None:
    """
    Top-level function for ProcessPoolExecutor.
    Loads model (cached per process), embeds, and upserts.
    """
    if not records:
        return

    # Load model (will be fast if cached)
    model = load_transformer()

    # Embed
    for record in records:
        record.embeddings = embed_text(
            model=model,
            text=record.summary,
            normalize=normalize_embeddings,
        )

    # Upsert
    # database instance is global in app.core.db, initialized on import
    # This is safe in a new process as it's a fresh instance per process
    collection = database.get_collection(collection_name)

    operations = [
        ReplaceOne(
            {"_id": rec.mongo_id},
            rec.model_dump(by_alias=True, exclude_none=True),
            upsert=True,
        )
        for rec in records
    ]

    if operations:
        collection.bulk_write(operations, ordered=False)
        logger.info(f"Upserted {len(records)} chunks")


class Embeddings:
    def __load_db_records(
        self, *, source_collection: str, limit: Optional[int]
    ) -> Iterator[List[ScryfallCardRecord]]:
        collection = database.get_collection(source_collection)
        cursor = collection.find()

        if limit is not None:
            cursor = cursor.limit(limit)

        batch = []
        for card in cursor:
            batch.append(ScryfallCardRecord.model_validate(card))
            if len(batch) >= db_settings.batch_size:
                yield batch
                batch = []

        if batch:
            yield batch

    def __normalize_mana_symbols(self, text: str | None) -> str | None:
        if text is None:
            return None
        normalized = text.replace("{", " ").replace("}", " ")
        return re.sub(r"\s+", " ", normalized).strip()

    def __is_empty_face(self, face: ScryfallCardFace) -> bool:
        is_empty_mana_cost = face.mana_cost == ""
        if isinstance(face.colors, list):
            is_empty_colors = len(face.colors) == 0
        else:
            is_empty_colors = face.colors is None
        return is_empty_mana_cost and is_empty_colors

    def __is_empty_card(self, card: ScryfallCardRecord) -> bool:
        is_empty_cmc = card.cmc == 0
        is_empty_colors = len(card.colors) == 0
        is_empty_color_identity = len(card.color_identity) == 0
        is_empty_keywords = len(card.keywords) == 0
        is_empty_mana_cost = card.mana_cost in {"", None}
        return (
            is_empty_cmc
            and is_empty_colors
            and is_empty_color_identity
            and is_empty_keywords
            and is_empty_mana_cost
        )

    def __should_filter_out_empty_card(self, card: ScryfallCardRecord) -> bool:
        type_line = card.type_line
        if type_line not in {"Card", "Card // Card"}:
            return False

        faces = card.card_faces
        if faces:
            return any(self.__is_empty_face(face) for face in faces)

        return self.__is_empty_card(card)

    def __build_scryfall_embedding_chunk(self, card: ScryfallCardRecord) -> str:
        name = card.name
        type_line = card.type_line
        mana_cost = self.__normalize_mana_symbols(card.mana_cost)
        cmc = card.cmc
        oracle_text = self.__normalize_mana_symbols(card.oracle_text)
        flavor_text = card.flavor_text
        price_usd = card.prices.usd
        set_name = card.set_name

        cost_parts: List[str] = []
        if mana_cost:
            cost_parts.append(f"Cost: {mana_cost}")
        if cmc is not None:
            cost_parts.append(f"(CMC or mana value {cmc})")
        cost_section = " ".join(cost_parts) if cost_parts else "Cost: None"

        abilities_section = (
            f"Abilities: {oracle_text}" if oracle_text else "Abilities: None"
        )

        # Unused
        if price_usd is None:
            _price_section = "Current Price: None"
        else:
            _price_section = f"Current Price: ${price_usd} USD"

        _flavor_section = f"Flavor: {flavor_text}" if flavor_text else "Flavor: None"

        return f"Card Name: {name}. Type: {type_line}. Set: {set_name}. {cost_section}. {abilities_section}. "

    def __build_scryfall_embedding_record(
        self, card: ScryfallCardRecord
    ) -> CardEmbeddingRecord | None:
        searchable_representation = self.__build_scryfall_embedding_chunk(card)
        return CardEmbeddingRecord(
            _id=card.mongo_id,
            source_id=card.mongo_id,
            summary=searchable_representation,
        )

    def run_pipeline(
        self,
        *,
        source_collection: str,
        target_collection: str,
        limit: Optional[int],
        normalize: bool = True,
    ) -> None:
        max_workers = app_settings.embeddings_max_workers

        total_records = 0
        total_invalid_records = 0
        total_chunks = 0

        logger.info(
            f"Starting embeddings pipeline: source={source_collection}, target={target_collection}, workers={max_workers}, limit={limit}, normalize={normalize}"
        )

        # NOTE: Using ProcessPoolExecutor for CPU/GPU intensive tasks (embedding generation)
        # Passing batches of records to worker processes.
        # Worker processes will initialize the model (if not cached) and run inference + upsert.

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for record_batch in self.__load_db_records(
                source_collection=source_collection, limit=limit
            ):
                logger.debug(f"Loading batch with {len(record_batch)} records")
                embeddings_to_process = []
                for db_record in record_batch:
                    total_records += 1

                    # TODO: This will have to be a custom filtering function
                    if self.__should_filter_out_empty_card(db_record):
                        # logger.debug(f"Empty card {db_card.mongo_id}")
                        total_invalid_records += 1
                        continue

                    embedding_record = self.__build_scryfall_embedding_record(db_record)
                    if embedding_record is None:
                        continue
                    embeddings_to_process.append(embedding_record)
                    total_chunks += 1

                if not embeddings_to_process:
                    continue

                # Submit to process pool
                future = executor.submit(
                    _process_and_upsert_batch,
                    embeddings_to_process,
                    target_collection,
                    normalize,
                )
                futures.append(future)

            # Wait for all futures to complete and check for exceptions
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in batch processing: {e}")
                    raise e

        logger.info(f"Total cards read: {total_records}")
        logger.info(f"Total empty cards: {total_invalid_records}")
        logger.info(f"Total chunks processed: {total_chunks}")
