import hashlib
import math


def embed(text):
    vector = [0.0] * 128
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:4], "big") % len(vector)
        vector[slot] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def create_embedder():
    return embed
