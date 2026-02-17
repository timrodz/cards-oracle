from fastapi.testclient import TestClient

from app.main import app


def test_get_collection_properties_endpoint_returns_list(monkeypatch) -> None:
    from app.api.routes import db as db_route

    monkeypatch.setattr(
        db_route.database,
        "get_collection_properties",
        lambda *, collection_name: ["_id", "name", "type_line"],
    )

    client = TestClient(app)
    response = client.get("/db/collections/cards/properties")

    assert response.status_code == 200
    assert response.json() == ["_id", "name", "type_line"]


def test_create_embeddings_rejects_invalid_chunk_mapping_fields(monkeypatch) -> None:
    from app.api.routes import embeddings as embeddings_route

    monkeypatch.setattr(
        embeddings_route.database,
        "get_collection_properties",
        lambda *, collection_name: ["_id", "name"],
    )

    client = TestClient(app)
    response = client.post(
        "/embeddings",
        data={
            "source_collection": "cards",
            "target_collection": "card_embeddings",
            "chunk_mappings": "{name} - {invalid_field}",
            "normalize": "true",
        },
    )

    assert response.status_code == 400
    assert "invalid_field" in response.json()["detail"]


def test_create_embeddings_accepts_valid_chunk_mapping_fields(monkeypatch) -> None:
    from app.api.routes import embeddings as embeddings_route

    captured: dict = {}

    monkeypatch.setattr(
        embeddings_route.database,
        "get_collection_properties",
        lambda *, collection_name: ["_id", "name", "type_line"],
    )

    def _fake_run_pipeline(self, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(embeddings_route.Embeddings, "run_pipeline", _fake_run_pipeline)

    client = TestClient(app)
    response = client.post(
        "/embeddings",
        data={
            "source_collection": "cards",
            "target_collection": "card_embeddings",
            "chunk_mappings": "{name} - {type_line}",
            "normalize": "true",
        },
    )

    assert response.status_code == 200
    assert captured["source_collection"] == "cards"
    assert captured["target_collection"] == "card_embeddings"
    assert captured["chunk_mappings"] == "{name} - {type_line}"
