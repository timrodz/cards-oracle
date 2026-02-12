"""
This router is currently focused to a "card" resource
Eventually it will become a generic resource getter, where you can pass the name of the collection
"""

import asyncio
import json
import re

from fastapi import APIRouter, HTTPException

from app.core.db import database
from app.models.db import ScryfallCardRecord

router = APIRouter(prefix="/cards", tags=["Cards"])


def _normalize_card_id(raw_id: str) -> str:
    value = raw_id.strip()

    match = re.fullmatch(r"\{\s*source_id\s*:\s*([^}]+)\s*\}", value)
    if match:
        return match.group(1).strip().strip('"').strip("'")

    if value.startswith("{") and value.endswith("}"):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(parsed, dict):
            source_id = parsed.get("source_id")
            if isinstance(source_id, str) and source_id.strip():
                return source_id.strip()
    return value


@router.get("/{id}", response_model=ScryfallCardRecord)
async def fetch_card(id: str) -> ScryfallCardRecord:

    normalized_id = _normalize_card_id(id)
    query = {"_id": normalized_id}
    card = await asyncio.to_thread(database.cards_collection.find_one, query)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return ScryfallCardRecord.model_validate(card)
