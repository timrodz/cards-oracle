import math


def normalize_l2(values: list[float]) -> list[float]:
    """L2 normalization helper adapted from OpenAI embeddings documentation examples."""
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        return values
    return [v / norm for v in values]
