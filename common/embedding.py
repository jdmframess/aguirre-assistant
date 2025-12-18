import hashlib
import math
from typing import Iterable, List

VECTOR_DIM = 256


def _hash_token(token: str) -> int:
    digest = hashlib.md5(token.encode("utf-8")).digest()
    return int.from_bytes(digest, "big")


def embed_text(text: str, *, dim: int = VECTOR_DIM) -> List[float]:
    """Create a simple hashed bag-of-words embedding.

    This is deterministic and lightweight so it can run without external models.
    """
    if not text:
        return [0.0] * dim

    vector = [0.0] * dim
    tokens = text.lower().split()
    for token in tokens:
        bucket = _hash_token(token) % dim
        vector[bucket] += 1.0

    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    a_list = list(a)
    b_list = list(b)
    if len(a_list) != len(b_list):
        raise ValueError("Vectors must have the same length")

    dot_product = sum(x * y for x, y in zip(a_list, b_list))
    norm_a = math.sqrt(sum(x * x for x in a_list))
    norm_b = math.sqrt(sum(y * y for y in b_list))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)
