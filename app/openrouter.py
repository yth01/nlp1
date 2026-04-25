import json
import os
import urllib.error
import urllib.request


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FEEDBACK_KEYS = {
    "rating",
    "rating_line",
    "context_explanation",
    "intent_match",
    "social_nuance",
    "business_appropriateness",
    "improvements",
    "grammar_feedback",
    "better_response",
}


class OpenRouterClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = os.getenv("OPENROUTER_MODEL", "").strip()

    @property
    def enabled(self):
        return bool(self.api_key)

    def generate_feedback(self, scenario, user_response, scores):
        if not self.enabled:
            return None

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Context-First business English coach and situation simulator. "
                        "Use the persona, emotional context, crisis pause, response goal, and "
                        "evaluation rubric to judge whether the user solved the situation. "
                        "Prioritize intent match, social nuance, business appropriateness, and "
                        "specific next steps over literal wording. Detect phrases that are "
                        "grammatically possible but socially rude or too vague. Return only compact "
                        "JSON with these exact keys: rating, rating_line, context_explanation, "
                        "intent_match, social_nuance, business_appropriateness, improvements, "
                        "grammar_feedback, better_response. rating must be an integer from 1 to 5. "
                        "rating_line must be one Korean sentence beginning with star symbols such "
                        "as ★★★★☆. context_explanation, intent_match, social_nuance, and "
                        "business_appropriateness must be Korean strings. improvements must be an "
                        "array of 1-3 Korean sentences. grammar_feedback must be an array; if "
                        "there is no grammar issue, include one short Korean sentence saying the "
                        "grammar is acceptable. better_response must be a natural English sentence."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "scenario": {
                                "title": scenario["title"],
                                "context": scenario["context"],
                                "persona": scenario["persona"],
                                "persona_emotion": scenario.get("persona_emotion", ""),
                                "transcript": scenario.get("transcript", []),
                                "staff_line": scenario["staff_line"],
                                "pause_line": scenario.get("pause_line", scenario["staff_line"]),
                                "response_goal": scenario.get("response_goal", ""),
                                "ideal_intent": scenario["ideal_intent"],
                                "evaluation_rubric": scenario.get("evaluation_rubric", []),
                                "poor_response": scenario.get("poor_response", ""),
                                "excellent_response": scenario.get("excellent_response", scenario["model_response"]),
                            },
                            "user_response": user_response,
                            "scores": scores,
                        },
                        ensure_ascii=True,
                    ),
                },
            ],
            "temperature": 0.3,
            "max_tokens": 500,
            "response_format": {"type": "json_object"},
        }
        if self.model:
            payload["model"] = self.model

        request = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Context-First MVP",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return {
                "rating": 0,
                "rating_line": "OpenRouter 피드백 생성에 실패해 로컬 피드백으로 대체해야 합니다.",
                "context_explanation": "",
                "intent_match": "",
                "social_nuance": "",
                "business_appropriateness": "",
                "improvements": [f"오류: {exc}"],
                "grammar_feedback": [],
                "better_response": scenario["model_response"],
            }

        content = body["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {
                "rating": 0,
                "rating_line": content.strip(),
                "context_explanation": "응답 형식이 JSON이 아니어서 원문을 표시합니다.",
                "intent_match": "",
                "social_nuance": "",
                "business_appropriateness": "",
                "improvements": [],
                "grammar_feedback": [],
                "better_response": scenario["model_response"],
            }
        parsed = normalize_feedback(parsed, scenario)
        parsed["provider_model"] = body.get("model", self.model or "openrouter account default")
        return parsed


def normalize_feedback(feedback, scenario):
    normalized = {key: feedback.get(key) for key in FEEDBACK_KEYS}
    try:
        normalized["rating"] = max(1, min(5, int(normalized["rating"])))
    except (TypeError, ValueError):
        normalized["rating"] = 0

    if not normalized["rating_line"]:
        normalized["rating_line"] = "평가 문장을 생성하지 못했습니다."
    if not normalized["context_explanation"]:
        normalized["context_explanation"] = "문맥 설명을 생성하지 못했습니다."
    if not normalized["intent_match"]:
        normalized["intent_match"] = "의도 일치 설명을 생성하지 못했습니다."
    if not normalized["social_nuance"]:
        normalized["social_nuance"] = "사회적 뉘앙스 설명을 생성하지 못했습니다."
    if not normalized["business_appropriateness"]:
        normalized["business_appropriateness"] = "비즈니스 적절성 설명을 생성하지 못했습니다."
    if not isinstance(normalized["improvements"], list):
        normalized["improvements"] = [str(normalized["improvements"] or "개선점을 생성하지 못했습니다.")]
    if not isinstance(normalized["grammar_feedback"], list):
        normalized["grammar_feedback"] = [str(normalized["grammar_feedback"] or "문법 피드백을 생성하지 못했습니다.")]
    if not normalized["better_response"]:
        normalized["better_response"] = scenario["model_response"]
    return normalized
