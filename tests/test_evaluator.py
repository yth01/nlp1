import unittest

from app.evaluator import ResponseEvaluator, grammar_feedback, local_feedback, score_rubric
from app.scenarios import get_scenario


class EvaluatorTest(unittest.TestCase):
    def setUp(self):
        self.scenario = get_scenario("hotel_lobby_crisis")
        self.evaluator = ResponseEvaluator()

    def test_good_response_scores_higher_than_poor_response(self):
        good = self.evaluator.evaluate(
            self.scenario,
            "I understand. I have a reservation under Kim Ji-hoon and can show the confirmation email. Could you please check again?",
        )
        poor = self.evaluator.evaluate(self.scenario, "I booked room. You check it now")

        self.assertGreater(good["final_score"], poor["final_score"])
        self.assertGreater(good["signals"]["rubric_coverage"], poor["signals"]["rubric_coverage"])

    def test_evaluation_contains_required_contract_fields(self):
        scores = self.evaluator.evaluate(
            self.scenario,
            "I have a reservation under Kim Ji-hoon. Could you please check again?",
        )

        self.assertIn("semantic_score", scores)
        self.assertIn("nuance_score", scores)
        self.assertIn("final_score", scores)
        self.assertIn("rubric_breakdown", scores)
        self.assertEqual(len(scores["rubric_breakdown"]), len(self.scenario["evaluation_rubric"]))

    def test_score_rubric_returns_breakdown_and_normalized_score(self):
        breakdown, rubric_score = score_rubric(
            self.scenario,
            "Could you please check my reservation under Kim with the confirmation email?",
        )

        self.assertEqual(len(breakdown), len(self.scenario["evaluation_rubric"]))
        self.assertGreaterEqual(rubric_score, 0.0)
        self.assertLessEqual(rubric_score, 1.0)

    def test_local_feedback_contains_coach_sections(self):
        response = "i booked room. You check it now"
        scores = self.evaluator.evaluate(self.scenario, response)
        feedback = local_feedback(self.scenario, response, scores)

        for key in [
            "rating",
            "rating_line",
            "context_explanation",
            "intent_match",
            "social_nuance",
            "business_appropriateness",
            "improvements",
            "grammar_feedback",
            "better_response",
        ]:
            self.assertIn(key, feedback)
        self.assertLessEqual(len(feedback["improvements"]), 3)

    def test_grammar_feedback_detects_basic_errors(self):
        feedback = grammar_feedback("i booked room")

        self.assertTrue(any("booked a room" in item for item in feedback))
        self.assertTrue(any("대문자" in item for item in feedback))
        self.assertTrue(any("마침표" in item for item in feedback))


if __name__ == "__main__":
    unittest.main()
