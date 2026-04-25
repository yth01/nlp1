from app.embedding import (
    AGGRESSIVE_MARKERS,
    POLITE_MARKERS,
    TOKEN_RE,
    cosine_similarity,
    load_embedder,
    marker_ratio,
)


class ResponseEvaluator:
    def __init__(self):
        self.embedder = load_embedder()

    def evaluate(self, scenario, user_response):
        ideal_texts = [scenario["ideal_intent"], *scenario.get("acceptable_responses", [])]
        response_vector = self.embedder.embed(user_response)
        similarities = [
            cosine_similarity(response_vector, self.embedder.embed(text))
            for text in ideal_texts
        ]
        semantic_similarity = max(similarities) if similarities else 0.0

        polite = marker_ratio(user_response, POLITE_MARKERS)
        aggressive = marker_ratio(user_response, AGGRESSIVE_MARKERS)
        length_factor = min(1.0, len(TOKEN_RE.findall(user_response.lower())) / 10)
        rubric_breakdown, rubric_score = score_rubric(scenario, user_response)

        semantic_score = round(max(0.0, min(1.0, semantic_similarity)) * 100)
        nuance_score = round(
            max(0.0, min(1.0, rubric_score * 0.62 + polite * 1.3 + length_factor * 0.12 - aggressive * 1.8))
            * 100
        )
        final_score = round(semantic_score * 0.65 + nuance_score * 0.35)

        return {
            "semantic_score": semantic_score,
            "nuance_score": nuance_score,
            "final_score": final_score,
            "matched_intent": ideal_texts[similarities.index(max(similarities))]
            if similarities
            else scenario["ideal_intent"],
            "signals": {
                "politeness": round(polite, 2),
                "aggressive_language": round(aggressive, 2),
                "rubric_coverage": round(rubric_score, 2),
            },
            "rubric_breakdown": rubric_breakdown,
            "embedding_provider": getattr(self.embedder, "name", self.embedder.__class__.__name__),
        }


def star_rating(final_score):
    if final_score >= 90:
        return 5
    if final_score >= 75:
        return 4
    if final_score >= 55:
        return 3
    if final_score >= 35:
        return 2
    return 1


def stars(rating):
    return "★" * rating + "☆" * (5 - rating)


def score_rubric(scenario, user_response):
    rubric = scenario.get("evaluation_rubric", [])
    if not rubric:
        return [], 0.0

    normalized = user_response.lower()
    tokens = set(TOKEN_RE.findall(normalized))
    breakdown = []
    weighted_total = 0.0
    total_weight = 0.0

    for item in rubric:
        markers = item.get("markers", [])
        hits = []
        for marker in markers:
            marker_lower = marker.lower()
            if " " in marker_lower or "." in marker_lower:
                matched = marker_lower in normalized
            else:
                matched = marker_lower in tokens
            if matched:
                hits.append(marker)

        coverage = min(1.0, len(hits) / max(1, min(3, len(markers))))
        weight = float(item.get("weight", 1.0))
        weighted_total += coverage * weight
        total_weight += weight
        breakdown.append(
            {
                "key": item.get("key", ""),
                "label": item.get("label", item.get("key", "Rubric")),
                "score": round(coverage * 100),
                "matched_markers": hits,
                "description": item.get("description", ""),
            }
        )

    return breakdown, weighted_total / total_weight if total_weight else 0.0


def grammar_feedback(user_response):
    feedback = []
    lowered = user_response.lower()
    if "booked room" in lowered:
        feedback.append("'booked room'보다는 'booked a room'처럼 관사를 넣는 것이 자연스럽습니다.")
    if "i has" in lowered:
        feedback.append("'I has'는 주어-동사 일치 오류입니다. 'I have'를 사용하세요.")
    if "i am agree" in lowered:
        feedback.append("'I am agree'는 부자연스럽습니다. 'I agree'라고 말하세요.")
    if user_response and user_response[0].islower():
        feedback.append("문장 첫 글자는 대문자로 시작하는 것이 좋습니다.")
    if user_response and user_response[-1] not in ".?!":
        feedback.append("완성된 문장처럼 보이도록 마침표나 물음표를 붙이는 것이 좋습니다.")
    if not feedback:
        feedback.append("눈에 띄는 기본 문법 오류는 없습니다.")
    return feedback


def local_feedback(scenario, user_response, scores):
    improvements = []
    if scores["semantic_score"] < 45:
        improvements.append("상대가 바로 이해할 수 있도록 문제 상황과 원하는 조치를 더 직접적으로 말하세요.")
    if scores["nuance_score"] < 55:
        improvements.append("상대에게 책임을 묻기보다 정중하게 근거와 다음 행동을 제시하는 편이 좋습니다.")
    weak_rubrics = [item for item in scores.get("rubric_breakdown", []) if item["score"] < 50]
    for item in weak_rubrics[:2]:
        improvements.append(f"{item['label']} 요소가 약합니다. 이 상황에서 필요한 단서를 더 분명히 넣어보세요.")
    if not improvements:
        improvements.append("구체적인 시간, 자료, 확인 방법을 덧붙이면 실제 상황에서 더 빨리 해결될 수 있습니다.")
    improvements = improvements[:3]

    rating = star_rating(scores["final_score"])

    return {
        "rating": rating,
        "rating_line": f"{stars(rating)} 상황 해결 의도가 {'잘 전달됩니다' if rating >= 4 else '아직 약하게 전달됩니다'}.",
        "context_explanation": (
            f"{scenario['title']} 상황에서는 감정적으로 반응하기보다 문제를 인정하고, "
            f"상대가 바로 처리할 수 있는 정보와 다음 행동을 정중하게 제시하는 것이 중요합니다. "
            f"핵심 의도는 다음과 같습니다: {scenario['ideal_intent']}"
        ),
        "intent_match": f"가장 가까운 의도: {scores['matched_intent']}",
        "social_nuance": (
            "정중함과 구체성이 함께 있어야 상황을 악화시키지 않고 해결 가능성이 높아집니다."
            if scores["nuance_score"] >= 60
            else "현재 답변은 상대가 방어적으로 느낄 수 있거나 해결 단서가 부족할 수 있습니다."
        ),
        "business_appropriateness": (
            "비즈니스 상황에서 사용할 수 있는 수준입니다."
            if scores["final_score"] >= 75
            else "비즈니스 상황에서는 더 구체적인 근거와 다음 행동 제안이 필요합니다."
        ),
        "improvements": improvements,
        "grammar_feedback": grammar_feedback(user_response),
        "better_response": scenario["model_response"],
    }
