# rule_router.py  —  v1

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
from rules import (
    SUBJECT_RULES,
    INTENT_RULES,
    INTENT_PRIORITY,
    FOLLOW_UP_MARKERS,
    AMBIGUOUS_MARKERS,
    OUT_OF_SCOPE_RULES,
)


VALID_SUBJECTS = ["math", "physics", "chemistry"]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def match_weighted_rules(text: str, rules: list[dict]):
    score = 0
    matched_terms = []
    domain_specific_count = 0

    for rule in rules:
        term = normalize_text(rule["term"])
        weight = rule.get("weight", 1)
        rule_type = rule.get("type", "general")

        if term and term in text:
            score += weight
            matched_terms.append(term)

            if rule_type == "domain_specific":
                domain_specific_count += 1

    return {
        "score": score,
        "matched_terms": matched_terms,
        "domain_specific_count": domain_specific_count,
    }


def get_subject_signals(question: str):
    text = normalize_text(question)

    signals = {}

    for subject, rules in SUBJECT_RULES.items():
        result = match_weighted_rules(text, rules)
        signals[subject] = result

    signals = apply_regex_subject_boosts(question, signals)
    return signals


def apply_regex_subject_boosts(question: str, signals: dict):
    text = normalize_text(question)
    raw_text = question

    # Math signals: x^2, f(x), equations, common math symbols
    if re.search(r"\bx\s*\^?\s*2\b", text) or "f(x)" in text:
        signals["math"]["score"] += 3
        signals["math"]["matched_terms"].append("math_formula")
        signals["math"]["domain_specific_count"] += 1

    if any(symbol in raw_text for symbol in ["√", "∫", "≤", "≥", "Δ"]):
        signals["math"]["score"] += 3
        signals["math"]["matched_terms"].append("math_symbol")
        signals["math"]["domain_specific_count"] += 1

    # Physics signals: units and formulas
    physics_units = [
        "m/s", "km/h", "n", "j", "w", "v", "a", "hz", "kg", "m/s2", "m/s^2"
    ]

    if any(unit in text for unit in physics_units):
        if any(word in text for word in ["vận tốc", "gia tốc", "lực", "công", "điện", "sóng", "vật"]):
            signals["physics"]["score"] += 3
            signals["physics"]["matched_terms"].append("physics_unit")
            signals["physics"]["domain_specific_count"] += 1

    # Chemistry signals: chemical formulas and reaction arrows
    chemical_patterns = [
        r"\bnaoh\b", r"\bhcl\b", r"\bco2\b", r"\bh2o\b",
        r"\bh2\b", r"\bo2\b", r"\bcaco3\b", r"\bnacl\b"
    ]

    if any(re.search(pattern, text) for pattern in chemical_patterns):
        signals["chemistry"]["score"] += 4
        signals["chemistry"]["matched_terms"].append("chemical_formula")
        signals["chemistry"]["domain_specific_count"] += 1

    if "->" in text or "→" in text:
        signals["chemistry"]["score"] += 3
        signals["chemistry"]["matched_terms"].append("reaction_arrow")
        signals["chemistry"]["domain_specific_count"] += 1

    # pH must be handled carefully, not as simple "ph"
    if re.search(r"\bpH\b", raw_text):
        signals["chemistry"]["score"] += 5
        signals["chemistry"]["matched_terms"].append("pH")
        signals["chemistry"]["domain_specific_count"] += 1

    return signals


def get_history_subject(history):
    if not history:
        return None

    for item in reversed(history):
        if isinstance(item, dict):
            subject = item.get("primary_subject") or item.get("subject")
            if subject in VALID_SUBJECTS:
                return subject

            text = item.get("question") or item.get("content") or item.get("message") or ""
            if text:
                signals = get_subject_signals(text)
                best_subject, best_score = get_best_subject_from_signals(signals)
                if best_subject != "unknown" and best_score >= 3:
                    return best_subject

        elif isinstance(item, str):
            signals = get_subject_signals(item)
            best_subject, best_score = get_best_subject_from_signals(signals)
            if best_subject != "unknown" and best_score >= 3:
                return best_subject

    return None


def get_best_subject_from_signals(signals: dict):
    sorted_items = sorted(
        signals.items(),
        key=lambda item: item[1]["score"],
        reverse=True
    )

    best_subject = sorted_items[0][0]
    best_score = sorted_items[0][1]["score"]

    if best_score <= 0:
        return "unknown", 0

    return best_subject, best_score


def is_follow_up_question(question: str):
    text = normalize_text(question)
    return any(marker in text for marker in FOLLOW_UP_MARKERS)


def is_ambiguous_without_context(question: str, history):
    text = normalize_text(question)

    if history:
        return False

    return any(marker in text for marker in AMBIGUOUS_MARKERS)


def detect_intent(question: str, history=None):
    text = normalize_text(question)

    intent_scores = {}

    for intent, rules in INTENT_RULES.items():
        result = match_weighted_rules(text, rules)
        intent_scores[intent] = result["score"]

    # Priority-based decision
    for intent in INTENT_PRIORITY:
        if intent_scores.get(intent, 0) >= 5:
            return intent, intent_scores[intent]

    # If no strong intent, choose best score
    best_intent = max(intent_scores, key=intent_scores.get)
    best_score = intent_scores[best_intent]

    if best_score > 0:
        return best_intent, best_score

    if history and is_follow_up_question(question):
        return "ask_follow_up", 4

    return "unknown", 0


def detect_out_of_scope(question: str, total_stem_score: int):
    text = normalize_text(question)
    result = match_weighted_rules(text, OUT_OF_SCOPE_RULES)

    out_score = result["score"]

    # Out-of-scope only if OOS signal is strong and STEM signal is weak.
    if out_score >= 5 and total_stem_score < 3:
        return True, out_score

    return False, out_score


def detect_subject(question: str, history=None):
    if history is None:
        history = []

    signals = get_subject_signals(question)

    sorted_subjects = sorted(
        signals.items(),
        key=lambda item: item[1]["score"],
        reverse=True
    )

    top_subject = sorted_subjects[0][0]
    top_score = sorted_subjects[0][1]["score"]

    second_subject = sorted_subjects[1][0]
    second_score = sorted_subjects[1][1]["score"]

    history_subject = get_history_subject(history)
    follow_up = is_follow_up_question(question)

    # Multi-turn: inherit subject from history if current question is follow-up and weakly specified.
    if follow_up and history_subject and top_score < 4:
        return {
            "primary_subject": history_subject,
            "secondary_subjects": [],
            "subject_scores": {s: signals[s]["score"] for s in VALID_SUBJECTS},
            "top_score": 4,
            "second_score": 0,
            "is_interdisciplinary": False,
            "inherited_from_history": True,
        }

    # Unknown if no meaningful STEM subject signal.
    if top_score < 2:
        return {
            "primary_subject": "unknown",
            "secondary_subjects": [],
            "subject_scores": {s: signals[s]["score"] for s in VALID_SUBJECTS},
            "top_score": top_score,
            "second_score": second_score,
            "is_interdisciplinary": False,
            "inherited_from_history": False,
        }

    # Domain-owner logic:
    # Physics/Chemistry should dominate Math when Math is only a calculation tool.
    physics_specific = signals["physics"]["domain_specific_count"] > 0
    chemistry_specific = signals["chemistry"]["domain_specific_count"] > 0
    math_score = signals["math"]["score"]
    physics_score = signals["physics"]["score"]
    chemistry_score = signals["chemistry"]["score"]

    if physics_specific and math_score > 0 and physics_score >= 3:
        top_subject = "physics"
        top_score = physics_score

    if chemistry_specific and math_score > 0 and chemistry_score >= 3:
        top_subject = "chemistry"
        top_score = chemistry_score

    # Re-sort after domain-owner adjustment
    sorted_subjects = sorted(
        signals.items(),
        key=lambda item: item[1]["score"],
        reverse=True
    )

    secondary_subjects = []
    is_interdisciplinary = False

    for subject, result in sorted_subjects:
        if subject == top_subject:
            continue

        score = result["score"]

        if score >= 2 and top_score > 0 and (score / top_score) >= 0.35:
            secondary_subjects.append(subject)
            is_interdisciplinary = True

    return {
        "primary_subject": top_subject,
        "secondary_subjects": secondary_subjects,
        "subject_scores": {s: signals[s]["score"] for s in VALID_SUBJECTS},
        "top_score": top_score,
        "second_score": second_score,
        "is_interdisciplinary": is_interdisciplinary,
        "inherited_from_history": False,
    }


def decide_need_clarification(primary_subject, intent, question, history, is_interdisciplinary, subject_scores):
    if primary_subject == "unknown":
        return True

    if is_ambiguous_without_context(question, history):
        return True

    # If two non-math STEM subjects compete closely, ask clarification.
    physics_score = subject_scores.get("physics", 0)
    chemistry_score = subject_scores.get("chemistry", 0)

    if physics_score >= 3 and chemistry_score >= 3:
        margin = abs(physics_score - chemistry_score)
        if margin <= 1:
            return True

    # Do not ask clarification only because intent is unknown.
    # Router can still choose correct SLM by subject.
    return False


def decide_target_slm(primary_subject, need_clarification, out_of_scope):
    if out_of_scope:
        return "general_tutor"

    if need_clarification:
        return "ask_clarification"

    mapping = {
        "math": "math_slm",
        "physics": "physics_slm",
        "chemistry": "chemistry_slm",
    }

    return mapping.get(primary_subject, "ask_clarification")


def calculate_confidence(top_score, second_score, intent_score, need_clarification, is_interdisciplinary, inherited_from_history):
    if need_clarification:
        return 0.35

    margin = max(top_score - second_score, 0)

    confidence = 0.45
    confidence += min(top_score * 0.05, 0.30)
    confidence += min(intent_score * 0.03, 0.15)
    confidence += min(margin * 0.03, 0.10)

    if is_interdisciplinary:
        confidence -= 0.08

    if inherited_from_history:
        confidence -= 0.05

    return round(max(0.20, min(confidence, 0.95)), 2)


def build_reason(subject_result, intent, out_of_scope, need_clarification):
    if out_of_scope:
        return "Detected strong out-of-scope signal with weak STEM signal."

    if subject_result.get("inherited_from_history"):
        return f"Inherited subject={subject_result['primary_subject']} from conversation history and detected intent={intent}."

    if need_clarification:
        return f"Need clarification because subject or context is ambiguous. Detected subject={subject_result['primary_subject']}, intent={intent}."

    if subject_result.get("is_interdisciplinary"):
        return f"Detected interdisciplinary question. Primary subject={subject_result['primary_subject']}, secondary={subject_result['secondary_subjects']}, intent={intent}."

    return f"Detected subject={subject_result['primary_subject']}, intent={intent} using weighted keyword rules."


def route_question(question: str, history=None):
    if history is None:
        history = []

    subject_result = detect_subject(question, history)
    subject_scores = subject_result["subject_scores"]
    total_stem_score = sum(subject_scores.values())

    out_of_scope, out_score = detect_out_of_scope(question, total_stem_score)

    if out_of_scope:
        return {
            "primary_subject": "unknown",
            "secondary_subjects": [],
            "intent": "unknown",
            "target_slm": "general_tutor",
            "confidence": 0.80,
            "need_clarification": False,
            "reason": "Detected strong out-of-scope signal with weak STEM signal."
        }

    intent, intent_score = detect_intent(question, history)

    need_clarification = decide_need_clarification(
        primary_subject=subject_result["primary_subject"],
        intent=intent,
        question=question,
        history=history,
        is_interdisciplinary=subject_result["is_interdisciplinary"],
        subject_scores=subject_scores,
    )

    target_slm = decide_target_slm(
        primary_subject=subject_result["primary_subject"],
        need_clarification=need_clarification,
        out_of_scope=out_of_scope,
    )

    confidence = calculate_confidence(
        top_score=subject_result["top_score"],
        second_score=subject_result["second_score"],
        intent_score=intent_score,
        need_clarification=need_clarification,
        is_interdisciplinary=subject_result["is_interdisciplinary"],
        inherited_from_history=subject_result["inherited_from_history"],
    )

    reason = build_reason(
        subject_result=subject_result,
        intent=intent,
        out_of_scope=out_of_scope,
        need_clarification=need_clarification,
    )

    return {
        "primary_subject": subject_result["primary_subject"],
        "secondary_subjects": subject_result["secondary_subjects"],
        "intent": intent,
        "target_slm": target_slm,
        "confidence": confidence,
        "need_clarification": need_clarification,
        "reason": reason,
    }


if __name__ == "__main__":
    samples = [
        "Một vật rơi tự do trong 5 giây, tính vận tốc cuối cùng.",
        "Dùng phương trình bậc hai để tính thời gian vật chạm đất.",
        "Giải thích vì sao em sai ở bước này.",
        "Cân bằng phương trình H2 + O2 -> H2O.",
        "Phần này làm tiếp thế nào?",
    ]

    for question in samples:
        print(question)
        print(route_question(question))
        print()
