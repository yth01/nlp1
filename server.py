import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.evaluator import ResponseEvaluator, local_feedback
from app.openrouter import OpenRouterClient
from app.scenarios import get_scenario, load_scenarios


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"


class ContextFirstHandler(SimpleHTTPRequestHandler):
    evaluator = ResponseEvaluator()
    openrouter = OpenRouterClient()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/scenarios":
            return self.send_json(load_scenarios())
        if path.startswith("/api/scenarios/"):
            scenario_id = path.rsplit("/", 1)[-1]
            scenario = get_scenario(scenario_id)
            if not scenario:
                return self.send_json({"error": "scenario not found"}, status=404)
            return self.send_json(scenario)
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/evaluate":
            return self.send_json({"error": "not found"}, status=404)

        try:
            payload = self.read_json()
        except json.JSONDecodeError:
            return self.send_json({"error": "invalid json"}, status=400)

        scenario_id = payload.get("scenario_id", "hotel_lobby_crisis")
        user_response = str(payload.get("response", "")).strip()
        if not user_response:
            return self.send_json({"error": "response is required"}, status=400)

        scenario = get_scenario(scenario_id)
        if not scenario:
            return self.send_json({"error": "scenario not found"}, status=404)

        scores = self.evaluator.evaluate(scenario, user_response)
        feedback = self.openrouter.generate_feedback(scenario, user_response, scores)
        if feedback is None or feedback.get("rating_line", "").startswith("OpenRouter 피드백 생성에 실패"):
            fallback = local_feedback(scenario, user_response, scores)
            if feedback:
                fallback["openrouter_error"] = feedback["improvements"][0]
            feedback = fallback

        return self.send_json(
            {
                "scenario_id": scenario_id,
                "response": user_response,
                "scores": scores,
                "feedback": feedback,
            }
        )

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ContextFirstHandler)
    print("Context-First running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
