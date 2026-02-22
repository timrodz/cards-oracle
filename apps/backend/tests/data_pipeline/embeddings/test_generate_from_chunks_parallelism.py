from types import SimpleNamespace

from app.data_pipeline.embeddings import generate_from_chunks as pipeline


class _DummyPool:
    used = False

    def __init__(self, *, processes: int) -> None:
        self.processes = processes
        self.__class__.used = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def map(self, func, batches) -> None:
        for batch in batches:
            func(batch)


def test_run_pipeline_uses_sequential_for_openai(monkeypatch) -> None:
    _DummyPool.used = False
    calls: list[tuple[list[str], str, bool]] = []

    monkeypatch.setattr(
        pipeline,
        "transformer_settings",
        SimpleNamespace(provider="openai"),
    )
    monkeypatch.setattr(
        pipeline,
        "__load_db_records",
        lambda _collection, *, limit=None: iter([["a"], ["b"]]),
    )
    monkeypatch.setattr(
        pipeline,
        "process_batch",
        lambda records, *, target_collection, normalize_embeddings=True: calls.append(
            (records, target_collection, normalize_embeddings)
        ),
    )
    monkeypatch.setattr(pipeline.multiprocessing, "Pool", _DummyPool)

    pipeline.run_pipeline_generate_embeddings_from_chunks(
        target_collection="target",
        normalize_embeddings=False,
        limit=None,
    )

    assert _DummyPool.used is False
    assert calls == [(["a"], "target", False), (["b"], "target", False)]


def test_run_pipeline_uses_multiprocessing_for_sentence_transformers(monkeypatch) -> None:
    _DummyPool.used = False
    calls: list[tuple[list[str], str, bool]] = []

    monkeypatch.setattr(
        pipeline,
        "transformer_settings",
        SimpleNamespace(provider="sentence_transformers"),
    )
    monkeypatch.setattr(
        pipeline,
        "__load_db_records",
        lambda _collection, *, limit=None: iter([["a"], ["b"]]),
    )
    monkeypatch.setattr(
        pipeline,
        "process_batch",
        lambda records, *, target_collection, normalize_embeddings=True: calls.append(
            (records, target_collection, normalize_embeddings)
        ),
    )
    monkeypatch.setattr(pipeline.multiprocessing, "Pool", _DummyPool)
    monkeypatch.setattr(pipeline.os, "cpu_count", lambda: 2)

    pipeline.run_pipeline_generate_embeddings_from_chunks(
        target_collection="target",
        normalize_embeddings=True,
        limit=None,
    )

    assert _DummyPool.used is True
    assert calls == [(["a"], "target", True), (["b"], "target", True)]
