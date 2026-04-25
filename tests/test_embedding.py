import os
import unittest
from unittest.mock import patch

from app.embedding import LocalIntentEmbedder, cosine_similarity, load_embedder


class EmbeddingTest(unittest.TestCase):
    def test_local_embedder_returns_normalized_vector(self):
        embedder = LocalIntentEmbedder(dimensions=32)
        vector = embedder.embed("I booked a room under Kim Ji-hoon.")

        self.assertEqual(len(vector), 32)
        self.assertGreater(cosine_similarity(vector, vector), 0.99)

    def test_cosine_similarity_handles_empty_vectors(self):
        self.assertEqual(cosine_similarity([], []), 0.0)
        self.assertEqual(cosine_similarity([0.0], [1.0]), 0.0)

    def test_custom_embedder_import_path(self):
        with patch.dict(os.environ, {"CONTEXT_FIRST_EMBEDDER": "examples.simple_embedder:create_embedder"}):
            embedder = load_embedder()

        self.assertEqual(embedder.name, "examples.simple_embedder:create_embedder")
        self.assertTrue(embedder.embed("hello"))


if __name__ == "__main__":
    unittest.main()
