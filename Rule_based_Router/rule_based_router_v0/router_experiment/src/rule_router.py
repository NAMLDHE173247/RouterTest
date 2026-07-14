# rule_router.py

from rules import SUBJECT_KEYWORDS, INTENT_KEYWORDS, OUT_OF_SCOPE_KEYWORDS


def normalize_text(text: str) -> str:
    return text.lower().strip()


def count_keyword_score(text: str, keywords: list[str]) -> int:
    score = 0
    for keyword in keywords:
        if keyword.lower() in text:
            if " " in keyword:
                score += 2
            else:
                score += 1
    return score


def is_out_of_scope(question: str) -> bool:
    text = normalize_text(question)
    return any(keyword.lower() in text for keyword in OUT_OF_SCOPE_KEYWORDS)


def detect_subject(question: str):
    text = normalize_text(question)

    scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        scores[subject] = count_keyword_score(text, keywords)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    primary_subject, primary_score = sorted_scores[0]

    if primary_score == 0:
        return "unknown", [], 0.30

    secondary_subjects = []
    for subject, score in sorted_scores[1:]:
        if score > 0:
            secondary_subjects.append(subject)

    confidence = min(1.0, 0.50 + primary_score * 0.10)

    return primary_subject, secondary_subjects, confidence


def detect_intent(question: str, history=None):
    text = normalize_text(question)

    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        scores[intent] = count_keyword_score(text, keywords)

    best_intent, best_score = max(scores.items(), key=lambda x: x[1])

    if best_score == 0:
        if history and len(history) > 0:
            return "ask_follow_up", 0.50
        return "unknown", 0.30

    confidence = min(1.0, 0.50 + best_score * 0.10)
    return best_intent, confidence


def decide_target_slm(primary_subject: str, need_clarification: bool, out_of_scope: bool):
    if out_of_scope:
        return "general_tutor"

    if need_clarification:
        return "ask_clarification"

    mapping = {
        "math": "math_slm",
        "physics": "physics_slm",
        "chemistry": "chemistry_slm"
    }

    return mapping.get(primary_subject, "ask_clarification")


def route_question(question: str, history=None):
    if history is None:
        history = []

    out_of_scope = is_out_of_scope(question)

    if out_of_scope:
        return {
            "primary_subject": "unknown",
            "secondary_subjects": [],
            "intent": "unknown",
            "target_slm": "general_tutor",
            "confidence": 0.80,
            "need_clarification": False,
            "reason": "Detected out-of-scope keywords, routed to general tutor."
        }

    primary_subject, secondary_subjects, subject_confidence = detect_subject(question)
    intent, intent_confidence = detect_intent(question, history)

    need_clarification = False

    if primary_subject == "unknown":
        need_clarification = True

    if intent == "unknown":
        need_clarification = True

    target_slm = decide_target_slm(
        primary_subject=primary_subject,
        need_clarification=need_clarification,
        out_of_scope=out_of_scope
    )

    final_confidence = round((subject_confidence + intent_confidence) / 2, 2)

    return {
        "primary_subject": primary_subject,
        "secondary_subjects": secondary_subjects,
        "intent": intent,
        "target_slm": target_slm,
        "confidence": final_confidence,
        "need_clarification": need_clarification,
        "reason": f"Detected subject={primary_subject}, intent={intent} using keyword-based rules."
    }


if __name__ == "__main__":
    sample_question = "Một vật rơi tự do trong 5 giây, tính vận tốc cuối cùng."
    result = route_question(sample_question)
    print(result)
