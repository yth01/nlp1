import hashlib
import importlib
import importlib.util
import math
import os
import re
from collections import Counter


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z']*|\d+")

SYNONYMS = {
    "booked": "reservation",
    "booking": "reservation",
    "reserved": "reservation",
    "reserve": "reservation",
    "room": "room",
    "hotel": "hotel",
    "name": "name",
    "under": "under",
    "confirm": "confirm",
    "confirmation": "confirmation",
    "number": "number",
    "id": "id",
    "passport": "id",
    "help": "help",
    "check": "check",
    "please": "polite",
    "sorry": "polite",
    "mistake": "issue",
    "problem": "issue",
    "record": "record",
    "records": "record",
    "manager": "manager",
}

POLITE_MARKERS = {
    "please",
    "could",
    "would",
    "may",
    "thanks",
    "thank",
    "sorry",
    "appreciate",
}

ESCALATION_MARKERS = {
    "manager",
    "supervisor",
    "confirm",
    "confirmation",
    "email",
    "voucher",
    "id",
    "passport",
}

AGGRESSIVE_MARKERS = {
    "stupid",
    "ridiculous",
    "angry",
    "liar",
    "hate",
    "fault",
    "your fault",
    "unacceptable",
}


class LocalIntentEmbedder:
    """Small deterministic text embedder based on normalized n-gram feature hashing."""

    def __init__(self, dimensions=256):
        self.dimensions = dimensions

    def tokenize(self, text):
        raw_tokens = TOKEN_RE.findall(text.lower())
        return [SYNONYMS.get(token, token) for token in raw_tokens]

    def embed(self, text):
        tokens = self.tokenize(text)
        features = Counter(tokens)
        features.update(f"{a}_{b}" for a, b in zip(tokens, tokens[1:]))

        vector = [0.0] * self.dimensions
        for feature, count in features.items():
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            slot = int.from_bytes(digest, "big") % self.dimensions
            vector[slot] += 1.0 + math.log(count)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @property
    def name(self):
        return "local-hashed-ngram"


class FunctionEmbedder:
    def __init__(self, embed_function, name):
        self.embed_function = embed_function
        self.name = name

    def embed(self, text):
        return self.embed_function(text)


def cosine_similarity(left, right):
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def load_embedder():
    spec = os.getenv("CONTEXT_FIRST_EMBEDDER", "").strip()
    if not spec:
        if importlib.util.find_spec("sentence_transformers"):
            from app.sentence_embedder import create_embedder

            try:
                return create_embedder()
            except Exception:
                return LocalIntentEmbedder()
        return LocalIntentEmbedder()

    if ":" in spec:
        module_name, attr_name = spec.split(":", 1)
    else:
        module_name, attr_name = spec.rsplit(".", 1)

    attr = getattr(importlib.import_module(module_name), attr_name)
    if isinstance(attr, type):
        provider = attr()
    elif hasattr(attr, "embed"):
        provider = attr
    elif callable(attr):
        try:
            provider = attr()
        except TypeError:
            provider = attr
    else:
        provider = attr

    if hasattr(provider, "embed"):
        if not hasattr(provider, "name"):
            try:
                provider.name = spec
            except AttributeError:
                pass
        return provider
    if callable(provider):
        return FunctionEmbedder(provider, spec)
    raise TypeError("CONTEXT_FIRST_EMBEDDER must resolve to an object with embed(text) or a callable.")


def marker_ratio(text, markers):
    normalized = text.lower()
    tokens = set(TOKEN_RE.findall(normalized))
    hits = 0
    for marker in markers:
        if " " in marker:
            hits += int(marker in normalized)
        else:
            hits += int(marker in tokens)
    return hits / max(1, len(markers))
