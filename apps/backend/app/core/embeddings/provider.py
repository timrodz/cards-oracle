from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str, *, normalize: bool) -> list[float]:
        ...

    def embed_texts(self, texts: list[str], *, normalize: bool) -> list[list[float]]:
        ...
