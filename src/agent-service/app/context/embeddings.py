import hashlib
import math
import re

VECTOR_DIMENSION = 64


def embed_text(text: str) -> list[float]:
    vector = [0.0] * VECTOR_DIMENSION
    tokens = re.findall(r"[a-z0-9]+", text.lower())

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % VECTOR_DIMENSION
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector

    return [value / magnitude for value in vector]
