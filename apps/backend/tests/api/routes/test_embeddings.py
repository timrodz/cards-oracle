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

    monkeypatch.setattr(
        embeddings_route.database,
        "get_collection_properties",
        lambda *, collection_name: ["_id", "name", "type_line"],
    )

    def _fake_submit_job(*, params):
        return {
            "message": "Embeddings task accepted.",
            "job_id": "job_123",
            "status": "queued",
            "dagster_run_id": "run_123",
        }

    monkeypatch.setattr(
        embeddings_route.embeddings_job_service, "submit_job", _fake_submit_job
    )

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

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"] == "job_123"
    assert body["status"] == "queued"


def test_get_embeddings_job_status(monkeypatch) -> None:
    from app.api.routes import embeddings as embeddings_route

    monkeypatch.setattr(
        embeddings_route.embeddings_job_service,
        "get_job",
        lambda *, job_id: {
            "job_id": job_id,
            "status": "running",
            "dagster_run_id": "run_123",
            "dagster_status": "STARTED",
            "source_collection": "cards",
            "target_collection": "card_embeddings",
            "chunk_mappings": None,
            "limit": None,
            "normalize": True,
            "error": None,
        },
    )

    client = TestClient(app)
    response = client.get("/embeddings/jobs/job_123")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == "job_123"
    assert body["status"] == "running"
    assert body["dagster_status"] == "STARTED"
