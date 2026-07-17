"""Phase 2 contextual intent resolution for Rule V3."""

import re
import unicodedata

from keyword_matcher import normalize_text


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")[:48] or "pattern"


# These are contextual additions. The existing INTENT_RULES remain unchanged.
CONTEXT_RULES = (
    ("intent.phase3.solve.negative_hint", "solve_problem", r"(?:không cần gợi ý|đừng chỉ gợi ý).{0,30}(?:giải|lời giải|đầy đủ)", 16, "strong"),
    ("intent.phase2.diagnose.strong.formula_error", "diagnose_error", r"sai.{0,30}th.{0,5}c", 12, "strong"),
    ("intent.phase2.explain.strong.difference", "explain_concept", r"(?:không hiểu|chưa hiểu|khác nhau như thế nào|làm sao để nhận biết|là gì|giải thích|vì sao|tại sao|ý nghĩa|xảy ra khi nào)", 8, "strong"),
    ("intent.phase2.explain.strong.concept", "explain_concept", r"(?:bản chất|nguyên lý|hiểu như thế nào|liên quan đến.{0,40}như thế nào|thuộc phần kiến thức|tạo ra những chất gì)", 8, "strong"),
    ("intent.phase2.explain.strong.need_context", "explain_concept", r"(?:có cần biết|dùng để.{0,30}(?:kiểu nào|làm bài))", 10, "strong"),
    ("intent.phase2.solve.strong.calculation", "solve_problem", r"(?:giải hệ|giải bất phương trình|giải phương trình|tính|tìm|xác định|bao nhiêu|thay đổi thế nào)", 8, "strong"),
    ("intent.phase2.solve.strong.arithmetic_progression", "solve_problem", r"công sai", 8, "strong"),
    ("intent.phase2.diagnose.strong.location", "diagnose_error", r"(?:sai ở đâu|sai chỗ nào|sai bước nào|vì sao sai|chỉ ra lỗi|em sai bước nào)", 9, "strong"),
    ("intent.phase2.diagnose.strong.formula", "diagnose_error", r"(?:công thức|kết quả|cách tính).{0,30}sai", 12, "strong"),
    ("intent.phase2.diagnose.strong.correction", "diagnose_error", r"(?:công thức đúng là gì|có cần đổi).{0,40}", 10, "strong"),
    ("intent.phase2.check.strong.answer", "check_answer", r"(?:đáp án|kết quả).{0,30}(?:đúng không|hợp lý không)|(?:đúng không|hợp lý không)", 8, "strong"),
    ("intent.phase2.check.strong.user_claim", "check_answer", r"(?:như vậy có sai không|em làm vậy đúng không|em tính ra số âm, có sai không)", 8, "strong"),
    ("intent.phase2.hint.strong.guidance", "give_hint", r"(?:gợi ý|chỉ gợi ý|đừng giải hết|đừng cho đáp án|không cần lời giải|cho em hướng làm|hướng làm|nên bắt đầu từ đâu)", 9, "strong"),
    ("intent.phase2.hint.strong.stuck", "give_hint", r"(?:bị kẹt|chỉ em tiếp|không biết phải thế số vào đâu)", 9, "strong"),
    ("intent.phase2.follow_up.strong.reference", "ask_follow_up", r"(?:câu trên|phần trên|phần này|bước tiếp theo|làm tiếp|tiếp tục|ý đó|vì sao vậy|vậy sau|^vậy)", 9, "strong"),
)


VETO_RULES = (
    ("intent.phase2.veto.diagnose.cong_sai", "diagnose_error", r"công sai", "The phrase means arithmetic progression difference, not an error report."),
    ("intent.phase3.veto.hint.negative_request", "give_hint", r"(?:không cần gợi ý|đừng chỉ gợi ý)", "A negative hint request asks for a full solution or rejects hint-only output."),
    ("intent.phase2.veto.solve.hint_request", "solve_problem", r"(?:gợi ý|chỉ gợi ý|đừng giải hết|đừng cho đáp án|không cần lời giải|cho em hướng làm|hướng làm|nên bắt đầu từ đâu|bị kẹt|chỉ em tiếp|không biết phải thế số vào đâu)", "A hint request must not be routed as a full solution."),
)


def _matches(text: str, pattern: str):
    try:
        return re.finditer(pattern, text, flags=re.IGNORECASE)
    except re.error:
        return ()


def _base_trace(signals: dict) -> list[dict]:
    matches = []
    for intent, signal in signals.items():
        for item in signal.get("matched_rules", []):
            term = item["term"]
            matches.append({
                "rule_id": f"intent.base.{intent}.{_slug(term)}",
                "intent": intent,
                "source": "base_rule",
                "matched_text": term,
                "start": item.get("start"),
                "end": item.get("end"),
                "score": item.get("weight", 0),
                "strength": item.get("type", "general"),
            })
    return matches


def resolve_intent(question: str, history, intent_matcher, follow_up_matcher, context=None) -> dict:
    text = normalize_text(question)
    signals = intent_matcher.extract_all(question)
    scores = {intent: signal["score"] for intent, signal in signals.items()}
    matches = _base_trace(signals)
    contextual_scores = {intent: 0 for intent in scores}
    contextual_strength = {intent: 0 for intent in scores}

    for rule_id, intent, pattern, weight, strength in CONTEXT_RULES:
        for match in _matches(text, pattern):
            contextual_scores[intent] = contextual_scores.get(intent, 0) + weight
            contextual_strength[intent] = contextual_strength.get(intent, 0) + 1
            matches.append({
                "rule_id": rule_id,
                "intent": intent,
                "source": "context_rule",
                "matched_text": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "score": weight,
                "strength": strength,
            })

    vetoes = []
    vetoed_intents = set()
    follow_up_signal = follow_up_matcher.extract(question)
    if history and (re.search(r"\bvậy\b", text) or follow_up_signal["score"] > 0):
        history_weight = getattr(context, "history_weight", 1.0) or 1.0
        contextual_scores["ask_follow_up"] = contextual_scores.get("ask_follow_up", 0) + round(22 * history_weight)
        contextual_strength["ask_follow_up"] = contextual_strength.get("ask_follow_up", 0) + 1
        matches.append({
            "rule_id": "intent.phase2.follow_up.context.history",
            "intent": "ask_follow_up",
            "source": "history_context",
            "matched_text": text[: min(len(text), 48)],
            "start": 0,
            "end": min(len(text), 48),
            "score": round(22 * history_weight),
            "strength": "strong",
        })

    if not history:
        follow_up_terms = {"ask_follow_up"}
        if any(item["intent"] in follow_up_terms for item in matches):
            vetoed_without_history = {
                "rule_id": "intent.phase2.veto.follow_up.no_history",
                "intent": "ask_follow_up",
                "reason": "A follow-up reference without conversation history is not actionable context.",
                "matched_text": text[: min(len(text), 48)],
                "start": 0,
                "end": min(len(text), 48),
            }
            vetoes.append(vetoed_without_history)
            vetoed_intents.add("ask_follow_up")

    for rule_id, intent, pattern, reason in VETO_RULES:
        for match in _matches(text, pattern):
            vetoed_intents.add(intent)
            vetoes.append({
                "rule_id": rule_id,
                "intent": intent,
                "reason": reason,
                "matched_text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })

    if any(veto["rule_id"] == "intent.phase3.veto.hint.negative_request" for veto in vetoes):
        vetoed_intents.discard("solve_problem")
        vetoes = [
            veto for veto in vetoes
            if veto["rule_id"] != "intent.phase2.veto.solve.hint_request"
        ]

    final_scores = {
        intent: score + contextual_scores.get(intent, 0)
        for intent, score in scores.items()
        if intent not in vetoed_intents
    }
    for intent, score in contextual_scores.items():
        if intent not in final_scores and intent not in vetoed_intents:
            final_scores[intent] = score

    ranked = sorted(final_scores.items(), key=lambda item: (item[1], contextual_strength.get(item[0], 0), item[0]), reverse=True)
    if not ranked or ranked[0][1] <= 0:
        selected = "unknown"
        selected_score = 0
    else:
        selected, selected_score = ranked[0]
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            top_strength = contextual_strength.get(ranked[0][0], 0)
            second_strength = contextual_strength.get(ranked[1][0], 0)
            if top_strength == second_strength:
                selected = "unknown"
                selected_score = 0
            elif second_strength > top_strength:
                selected, selected_score = ranked[1]

    selected_matches = [item["matched_text"] for item in matches if item["intent"] == selected]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    return {
        "intent": selected,
        "score": selected_score,
        "scores": final_scores,
        "matched_terms": selected_matches,
        "trace": {
            "rule_matches": matches,
            "vetoes": vetoes,
            "scores": final_scores,
            "selected_intent": selected,
            "top_score": selected_score,
            "second_score": second_score,
            "decision_margin": max(selected_score - second_score, 0),
            "history_context": {
                "source_turn": getattr(context, "source_turn", None),
                "history_weight": round(getattr(context, "history_weight", 0.0), 4),
                "inherited_fields": list(getattr(context, "inherited_fields", [])),
                "missing_history": bool(getattr(context, "missing_history", not history)),
            },
        },
    }
