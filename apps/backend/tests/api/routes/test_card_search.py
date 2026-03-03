import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
import io

from app.main import app
from app.core.elasticsearch import get_es
from app.core.db import get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_es():
    return AsyncMock()


@pytest.fixture
def sample_card():
    return {
        "_id": "69a6bb5dbac7899cb88f2cab",
        "id": "123",
        "object": "card",
        "oracle_id": "ora1",
        "multiverse_ids": [1],
        "name": "Lightning Bolt",
        "lang": "en",
        "released_at": "1993-08-05",
        "uri": "https://api.scryfall.com/cards/123",
        "scryfall_uri": "https://scryfall.com/card/lea/123",
        "layout": "normal",
        "highres_image": True,
        "image_status": "highres",
        "cmc": 1.0,
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "colors": ["R"],
        "color_identity": ["R"],
        "keywords": [],
        "produced_mana": [],
        "legalities": {},
        "games": ["paper"],
        "reserved": False,
        "game_changer": False,
        "foil": True,
        "nonfoil": True,
        "finishes": ["foil"],
        "oversized": False,
        "promo": False,
        "reprint": True,
        "variation": False,
        "set_id": "set1",
        "set": "lea",
        "set_name": "Limited Edition Alpha",
        "set_type": "core",
        "set_uri": "https://api.scryfall.com/sets/set1",
        "set_search_uri": "https://api.scryfall.com/cards/search?q=e%3Alea",
        "scryfall_set_uri": "https://api.scryfall.com/sets/lea",
        "rulings_uri": "https://api.scryfall.com/cards/123/rulings",
        "prints_search_uri": "https://api.scryfall.com/cards/search?q=oracle_id%3Aora1",
        "collector_number": "1",
        "digital": False,
        "rarity": "common",
        "artist": "Christopher Rush",
        "prices": {"usd": "100.00"},
        "border_color": "black",
        "frame": "1993",
        "full_art": False,
        "textless": False,
        "booster": True,
        "story_spotlight": False,
    }


def test_ingestion_mongodb_only(client, mock_es, sample_card):
    """
    Test that the JSON ingestion endpoint only updates MongoDB and doesn't touch ES.
    """
    app.dependency_overrides[get_es] = lambda: mock_es
    
    file_content = json.dumps([sample_card]).encode("utf-8")
    file_obj = io.BytesIO(file_content)

    with patch("app.data_pipeline.ingestion.json_records._get_db") as mock_get_db:
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance
        
        response = client.post(
            "/data-pipeline/ingestion/json-records",
            files={"file": ("test.json", file_obj, "application/json")},
            data={"collection": "cards"}
        )
        assert response.status_code == 200
        
        # Verify MongoDB was called
        mock_db_instance.get_collection.assert_called()
        
        # Verify ES was NOT called (no indexing happened)
        assert mock_es.search.call_count == 0

    app.dependency_overrides.clear()


def test_elasticsearch_indexing_endpoint(client, mock_es, sample_card):
    """
    Test that the dedicated ES indexing endpoint reads from DB and calls async_bulk.
    """
    app.dependency_overrides[get_es] = lambda: mock_es
    
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Mock MongoDB collection.find
    mock_collection = MagicMock()
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find.return_value = [sample_card]

    with patch("app.services.card_indexer.async_bulk") as mock_bulk:
        mock_bulk.return_value = (1, []) # (success_count, errors)
        
        response = client.post("/cards/search/index")
        assert response.status_code == 200
        assert "Indexing completed: 1 succeeded, 0 failed." in response.json()["message"]
        
        # Verify MongoDB was queried
        mock_db.get_collection.assert_called()
        mock_collection.find.assert_called_with({})
        
        # Verify async_bulk was called
        mock_bulk.assert_called_once()

    app.dependency_overrides.clear()


def test_search_endpoint(client, mock_es, sample_card):
    """
    Test the search endpoint functionality.
    """
    app.dependency_overrides[get_es] = lambda: mock_es
    
    mock_es.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "123",
                    "_source": sample_card,
                }
            ],
        }
    }

    # Test fuzzy match
    response = client.get("/cards/search/", params={"query": "Ligtning"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Lightning Bolt"

    # Test filters
    response = client.get("/cards/search/", params={"cmc": 1.0})
    assert response.status_code == 200
    
    # Verify the call to ES for CMC
    args, kwargs = mock_es.search.call_args
    filter_clauses = kwargs["body"]["query"]["bool"]["filter"]
    assert any(f.get("term", {}).get("cmc") == 1.0 for f in filter_clauses)

    app.dependency_overrides.clear()
