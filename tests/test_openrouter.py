import unittest

from app.openrouter import normalize_feedback
from app.scenarios import get_scenario


class OpenRouterFeedbackTest(unittest.TestCase):
    def test_normalize_feedback_fills_missing_fields(self):
        scenario = get_scenario("hotel_lobby_crisis")
        feedback = normalize_feedback({"rating": "7", "improvements": "Add details."}, scenario)

        self.assertEqual(feedback["rating"], 5)
        self.assertIsInstance(feedback["improvements"], list)
        self.assertIsInstance(feedback["grammar_feedback"], list)
        self.assertEqual(feedback["better_response"], scenario["model_response"])
        self.assertIn("rating_line", feedback)
        self.assertIn("social_nuance", feedback)


if __name__ == "__main__":
    unittest.main()
