import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "scenarios"


def load_scenarios():
    scenarios = []
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            scenarios.append(json.load(file))
    return scenarios


def get_scenario(scenario_id):
    for scenario in load_scenarios():
        if scenario["id"] == scenario_id:
            return scenario
    return None
