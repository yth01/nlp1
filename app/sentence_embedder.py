import os


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEmbedder:
    def __init__(self, model_name=None):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name or os.getenv("CONTEXT_FIRST_ST_MODEL", DEFAULT_MODEL)
        self.model = SentenceTransformer(self.model_name)
        self.name = f"sentence-transformers:{self.model_name}"

    def embed(self, text):
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)


def create_embedder():
    return SentenceTransformerEmbedder()
