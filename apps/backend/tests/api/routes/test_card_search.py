import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
import io

from app.main import app
from app.core.elasticsearch import get_es


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_es():
    return AsyncMock()


@pytest.fixture
def mock_db():
    with patch("app.data_pipeline.ingestion.json_records._get_db") as mock:
        db = MagicMock()
        mock.return_value = db
        yield db


def test_search_workflow_integration(client, mock_es):
    """
    Test the ingestion and search workflow by mocking Elasticsearch.
    """
    # 1. Mock ES search response for Lightning Bolt
    mock_es.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "123",
                    "_source": {
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
                    },
                }
            ],
        }
    }

    # Override the ES dependency
    app.dependency_overrides[get_es] = lambda: mock_es

    # 2. Test Ingestion (Mocking DB)
    sample_card = {
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

    file_content = json.dumps([sample_card]).encode("utf-8")
    file_obj = io.BytesIO(file_content)

    with patch("app.data_pipeline.ingestion.json_records._get_db") as mock_get_db:
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance
        
        response = client.post(
            "/data-pipeline/ingestion/json-records?collection=cards",
            files={"file": ("test.json", file_obj, "application/json")},
            data={"collection": "cards"}
        )
        assert response.status_code == 200

    # 3. Test Search - Fuzzy match
    response = client.get("/cards/search/", params={"query": "Ligtning"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Lightning Bolt"

    # 4. Test Search - Filter by CMC
    response = client.get("/cards/search/", params={"cmc": 1.0})
    assert response.status_code == 200
    
    # Verify the call to ES for CMC
    args, kwargs = mock_es.search.call_args
    filter_clauses = kwargs["body"]["query"]["bool"]["filter"]
    assert any(f.get("term", {}).get("cmc") == 1.0 for f in filter_clauses)

    # Clean up
    app.dependency_overrides.clear()
