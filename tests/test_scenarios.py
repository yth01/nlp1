import unittest

from app.scenarios import get_scenario, load_scenarios


REQUIRED_FIELDS = {
    "id",
    "title",
    "level",
    "context",
    "persona",
    "persona_emotion",
    "transcript",
    "staff_line",
    "pause_line",
    "response_goal",
    "ideal_intent",
    "acceptable_responses",
    "evaluation_rubric",
    "poor_response",
    "excellent_response",
    "model_response",
}


class ScenarioTest(unittest.TestCase):
    def test_all_scenarios_have_required_fields(self):
        scenarios = load_scenarios()

        self.assertGreaterEqual(len(scenarios), 3)
        for scenario in scenarios:
            missing = REQUIRED_FIELDS - set(scenario)
            self.assertEqual(missing, set(), scenario["id"])
            self.assertGreaterEqual(len(scenario["transcript"]), 1)
            self.assertGreaterEqual(len(scenario["acceptable_responses"]), 1)
            self.assertGreaterEqual(len(scenario["evaluation_rubric"]), 1)

    def test_get_scenario_returns_expected_scenario(self):
        scenario = get_scenario("hotel_lobby_crisis")

        self.assertIsNotNone(scenario)
        self.assertEqual(scenario["title"], "Hotel Lobby Crisis")

    def test_rubric_items_have_scoring_metadata(self):
        for scenario in load_scenarios():
            for item in scenario["evaluation_rubric"]:
                self.assertIn("key", item)
                self.assertIn("label", item)
                self.assertIn("description", item)
                self.assertIn("markers", item)
                self.assertIn("weight", item)
                self.assertGreater(len(item["markers"]), 0)
                self.assertGreater(float(item["weight"]), 0)


if __name__ == "__main__":
    unittest.main()
