import re

from keyword_matcher import (
    SingleLabelFlashTextMatcher,
    WeightedFlashTextMatcher,
    normalize_text,
)

from rules import (
    INTENT_RULES,
    INTENT_PRIORITY,
    FOLLOW_UP_RULES,
    AMBIGUOUS_RULES,
    OUT_OF_SCOPE_RULES,
    THRESHOLDS
)
from topic_resolver import VALID_SUBJECTS, resolve_subject
from intent_resolver import resolve_intent
from router_context import build_router_context, history_is_usable

INTENT_MATCHER = WeightedFlashTextMatcher(
    INTENT_RULES
)

FOLLOW_UP_MATCHER = SingleLabelFlashTextMatcher(
    FOLLOW_UP_RULES,
    "follow_up"
)

AMBIGUOUS_MATCHER = SingleLabelFlashTextMatcher(
    AMBIGUOUS_RULES,
    "ambiguous"
)

OUT_OF_SCOPE_MATCHER = SingleLabelFlashTextMatcher(
    OUT_OF_SCOPE_RULES,
    "out_of_scope"
)


SCOPE_CONTEXT_RULES = (
    ("scope.oos.weather", r"(?:thời tiết|trời sẽ mưa|có mưa không)"),
    ("scope.oos.food", r"(?:món ăn|nấu mì|ăn gì|cách nấu)"),
    ("scope.oos.shopping", r"(?:mua điện thoại|chọn tai nghe|giá rẻ|chọn balo)"),
    ("scope.oos.entertainment", r"(?:chơi game|xem phim|bài nhạc|truyện ngắn)"),
    ("scope.oos.lifestyle", r"(?:ngủ sớm|tập thể dục|giảm căng thẳng|mặc áo|chăm sóc cây)"),
    ("scope.oos.writing", r"(?:caption|lời chúc sinh nhật|đặt tên nhóm|mở đầu thuyết trình)"),
    ("scope.oos.study_lifestyle", r"(?:sắp xếp bàn học|mật khẩu mạnh|app ghi chú|gấp áo đồng phục|lịch ôn thi)"),
)


def get_history_text(item) -> str:
    if isinstance(item, str):
        return item

    if not isinstance(item, dict):
        return ""

    for key in [
        "question",
        "content",
        "message",
        "text",
        "answer"
    ]:
        value = item.get(key)

        if isinstance(value, str) and value.strip():
            return value

    return ""


def get_history_subject(history):
    if not history:
        return None

    for item in reversed(history):
        if isinstance(item, dict):
            subject = (
                item.get("primary_subject")
                or item.get("subject")
            )

            if subject in VALID_SUBJECTS:
                return subject

        history_text = get_history_text(item)

        if not history_text:
            continue

        resolved = resolve_subject(history_text)
        if resolved.primary_subject in VALID_SUBJECTS and resolved.top_score >= 2:
            return resolved.primary_subject

    return None


def detect_intent(
    question: str,
    history=None,
    context=None,
):
    return resolve_intent(
        question=question,
        history=history or [],
        intent_matcher=INTENT_MATCHER,
        follow_up_matcher=FOLLOW_UP_MATCHER,
        context=context,
    )

    # Legacy score path retained below for reference; Phase 2 returns above.
    history = history or []

    signals = INTENT_MATCHER.extract_all(question)

    scores = {
        intent: result["score"]
        for intent, result in signals.items()
    }

    best_score = max(
        scores.values(),
        default=0
    )

    if best_score == 0:
        follow_up_score = FOLLOW_UP_MATCHER.extract(
            question
        )["score"]

        if follow_up_score > 0 and history:
            return {
                "intent": "ask_follow_up",
                "score": 3,
                "scores": scores,
                "matched_terms": []
            }

        return {
            "intent": "unknown",
            "score": 0,
            "scores": scores,
            "matched_terms": []
        }

    # Các intent có score gần bằng score cao nhất.
    candidates = {
        intent
        for intent, score in scores.items()
        if score > 0 and score >= best_score - 1
    }

    # Nếu gần bằng nhau thì dùng priority.
    selected_intent = None

    for intent in INTENT_PRIORITY:
        if intent in candidates:
            selected_intent = intent
            break

    if selected_intent is None:
        selected_intent = max(
            scores,
            key=scores.get
        )

    return {
        "intent": selected_intent,
        "score": scores[selected_intent],
        "scores": scores,
        "matched_terms": signals[
            selected_intent
        ]["matched_terms"]
    }


def detect_subject(
    question: str,
    history=None
):
    history = history or []
    history_subject = get_history_subject(history)
    resolution = resolve_subject(question)
    scores = resolution.subject_scores
    top_score = resolution.top_score
    second_score = resolution.second_score

    follow_up_score = FOLLOW_UP_MATCHER.extract(
        question
    )["score"]

    context = build_router_context(
        history=history,
        current_subject=resolution,
        current_intent=None,
        current_topic=resolution.topic,
    )

    # Multi-turn: kế thừa môn học từ history.
    is_follow_up_turn = (
        follow_up_score > 0
        or normalize_text(question).startswith("vậy")
        or " vậy " in f" {normalize_text(question)} "
    )

    if (
        is_follow_up_turn
        and history_subject
        and top_score
        <= THRESHOLDS["history_inherit_max_score"]
        and history_is_usable(context)
    ):
        resolution.primary_subject = history_subject
        resolution.secondary_subjects = []
        resolution.inherited_from_history = True
        resolution.top_score = max(top_score, 3)
        context.inherited_fields.append("primary_subject")
        if not resolution.topic:
            resolution.topic = context.last_topic
            if context.last_topic:
                context.inherited_fields.append("topic")

    if is_follow_up_turn and not history:
        context.missing_history = True
        context.reset_reason = "missing_history"

    primary_subject = resolution.primary_subject

    return {
        "primary_subject": primary_subject,
        "secondary_subjects": resolution.secondary_subjects,
        "subject_scores": scores,
        "top_score": resolution.top_score,
        "second_score": resolution.second_score,
        "is_interdisciplinary": resolution.is_interdisciplinary,
        "inherited_from_history": resolution.inherited_from_history,
        "matched_terms": resolution.matched_terms,
        "topic": resolution.topic,
        "trace": {
            **resolution.trace(),
            "router_context": context.as_dict(),
        },
        "router_context": context,
    }


def detect_out_of_scope(
    question: str,
    top_stem_score: int,
    primary_subject: str = "unknown",
):
    result = OUT_OF_SCOPE_MATCHER.extract(
        question
    )

    context_matches = []
    normalized_question = normalize_text(question)
    for rule_id, pattern in SCOPE_CONTEXT_RULES:
        if re.search(pattern, normalized_question, flags=re.IGNORECASE):
            context_matches.append(rule_id)

    if primary_subject in VALID_SUBJECTS and top_stem_score >= THRESHOLDS["minimum_subject_score"]:
        scope_state = "CONFIRMED_STEM"
    elif (
        result["score"] >= THRESHOLDS["out_of_scope_min_score"]
        or context_matches
    ):
        scope_state = "CONFIRMED_OUT_OF_SCOPE"
    else:
        scope_state = "UNKNOWN_SCOPE"

    return {
        "is_out_of_scope": scope_state == "CONFIRMED_OUT_OF_SCOPE",
        "scope_state": scope_state,
        "score": result["score"],
        "matched_terms": result["matched_terms"],
        "context_rule_ids": context_matches,
    }


def decide_need_clarification(
    question: str,
    history: list,
    subject_result: dict
):
    primary_subject = subject_result[
        "primary_subject"
    ]

    if primary_subject == "unknown":
        return True

    history_subject = get_history_subject(
        history
    )

    ambiguous_score = AMBIGUOUS_MATCHER.extract(
        question
    )["score"]

    if (
        ambiguous_score
        >= THRESHOLDS[
            "ambiguous_min_score"
        ]
        and not history_subject
    ):
        return True

    follow_up_score = FOLLOW_UP_MATCHER.extract(
        question
    )["score"]

    if (
        follow_up_score > 0
        and not history_subject
    ):
        return True

    scores = subject_result[
        "subject_scores"
    ]

    physics_score = scores.get(
        "physics",
        0
    )

    chemistry_score = scores.get(
        "chemistry",
        0
    )

    # Physics và Chemistry cùng mạnh,
    # nhưng không rõ môn chính.
    if (
        physics_score
        >= THRESHOLDS[
            "cross_domain_min_score"
        ]
        and chemistry_score
        >= THRESHOLDS[
            "cross_domain_min_score"
        ]
        and abs(
            physics_score
            - chemistry_score
        )
        <= THRESHOLDS[
            "cross_domain_max_margin"
        ]
    ):
        return True

    return False


def decide_target_slm(
    primary_subject: str,
    need_clarification: bool,
    is_out_of_scope: bool
):
    if is_out_of_scope:
        return "general_tutor"

    if need_clarification:
        return "ask_clarification"

    target_mapping = {
        "math": "math_slm",
        "physics": "physics_slm",
        "chemistry": "chemistry_slm"
    }

    return target_mapping.get(
        primary_subject,
        "ask_clarification"
    )


def calculate_confidence(
    subject_result: dict,
    intent_result: dict,
    need_clarification: bool
):
    if need_clarification:
        return 0.35

    top_score = subject_result[
        "top_score"
    ]

    second_score = subject_result[
        "second_score"
    ]

    margin = max(
        top_score - second_score,
        0
    )

    intent_score = intent_result[
        "score"
    ]

    confidence = 0.42

    confidence += min(
        top_score * 0.045,
        0.30
    )

    confidence += min(
        intent_score * 0.025,
        0.15
    )

    confidence += min(
        margin * 0.025,
        0.10
    )

    if subject_result[
        "is_interdisciplinary"
    ]:
        confidence -= 0.07

    if subject_result[
        "inherited_from_history"
    ]:
        confidence -= 0.04

    if intent_result[
        "intent"
    ] == "unknown":
        confidence -= 0.08

    confidence = max(
        0.20,
        min(confidence, 0.95)
    )

    return round(
        confidence,
        2
    )


def build_reason(
    subject_result: dict,
    intent_result: dict,
    is_out_of_scope: bool,
    need_clarification: bool
):
    if is_out_of_scope:
        return (
            "Strong out-of-scope signal "
            "with no reliable STEM signal."
        )

    if need_clarification:
        return (
            "The subject or conversational "
            "reference is not sufficiently clear."
        )

    if subject_result[
        "inherited_from_history"
    ]:
        return (
            f"Inherited subject="
            f"{subject_result['primary_subject']} "
            f"from history; "
            f"intent={intent_result['intent']}."
        )

    if subject_result[
        "is_interdisciplinary"
    ]:
        secondary = ",".join(
            subject_result[
                "secondary_subjects"
            ]
        )

        return (
            f"Interdisciplinary question: "
            f"primary="
            f"{subject_result['primary_subject']}, "
            f"secondary={secondary}, "
            f"intent={intent_result['intent']}."
        )

    return (
        f"Weighted FlashText signals indicate "
        f"subject="
        f"{subject_result['primary_subject']}, "
        f"intent={intent_result['intent']}."
    )


def clarification_reason(
    question: str,
    history: list,
    subject_result: dict,
    intent_result: dict,
    scope_state: str,
) -> str:
    if scope_state == "CONFIRMED_OUT_OF_SCOPE":
        return "OUT_OF_SCOPE_CONFIRMED"
    if subject_result["primary_subject"] == "unknown":
        normalized = normalize_text(question)
        if (normalized.startswith("vậy") or " vậy " in f" {normalized} ") and not history:
            return "MISSING_HISTORY_FOR_FOLLOW_UP"
        scores = subject_result.get("subject_scores", {})
        top = max(scores.values(), default=0)
        if top > 0 and list(scores.values()).count(top) > 1:
            return "SUBJECT_SCORE_TIE"
        if AMBIGUOUS_MATCHER.extract(question)["score"] >= THRESHOLDS["ambiguous_min_score"]:
            return "INCOMPLETE_REFERENCE"
        return "NO_SUBJECT_EVIDENCE"
    if intent_result.get("intent") == "unknown":
        return "UNKNOWN_INTENT"
    scores = subject_result.get("subject_scores", {})
    if abs(scores.get("physics", 0) - scores.get("chemistry", 0)) <= THRESHOLDS["cross_domain_max_margin"]:
        if scores.get("physics", 0) >= THRESHOLDS["cross_domain_min_score"] and scores.get("chemistry", 0) >= THRESHOLDS["cross_domain_min_score"]:
            return "CROSS_DOMAIN_CONFLICT"
    return "LOW_CONFIDENCE"


def route_question(
    question: str,
    history=None
):
    history = history or []

    subject_result = detect_subject(
        question,
        history
    )

    out_of_scope_result = detect_out_of_scope(
        question,
        subject_result["top_score"],
        subject_result["primary_subject"],
    )

    if out_of_scope_result[
        "is_out_of_scope"
    ]:
        return {
            "primary_subject": "unknown",
            "secondary_subjects": [],
            "intent": "unknown",
            "target_slm": "general_tutor",
            "confidence": 0.80,
            "need_clarification": False,
            "topic": None,
            "trace": {
                **subject_result.get("trace", {}),
                "scope": out_of_scope_result,
            },
            "reason": (
                "Strong out-of-scope signal "
                "with no reliable STEM signal."
            )
        }

    router_context = subject_result.get("router_context")
    intent_result = detect_intent(
        question,
        history,
        router_context,
    )

    need_clarification = (
        decide_need_clarification(
            question=question,
            history=history,
            subject_result=subject_result
        )
    )

    clarification_reason_code = clarification_reason(
        question=question,
        history=history,
        subject_result=subject_result,
        intent_result=intent_result,
        scope_state=out_of_scope_result["scope_state"],
    ) if need_clarification else None

    target_slm = decide_target_slm(
        primary_subject=subject_result[
            "primary_subject"
        ],
        need_clarification=need_clarification,
        is_out_of_scope=False
    )

    confidence = calculate_confidence(
        subject_result=subject_result,
        intent_result=intent_result,
        need_clarification=need_clarification
    )

    reason = build_reason(
        subject_result=subject_result,
        intent_result=intent_result,
        is_out_of_scope=False,
        need_clarification=need_clarification
    )

    return {
        "primary_subject": subject_result[
            "primary_subject"
        ],
        "secondary_subjects": subject_result[
            "secondary_subjects"
        ],
        "intent": intent_result[
            "intent"
        ],
        "target_slm": target_slm,
        "confidence": confidence,
        "need_clarification": need_clarification,
        "reason": reason,
        "topic": subject_result.get("topic"),
        "trace": {
            **subject_result.get("trace", {}),
            "intent": intent_result.get("trace", {}),
            "scope": out_of_scope_result,
            "clarification_reason_code": clarification_reason_code,
        },
        "clarification_reason_code": clarification_reason_code,
    }


if __name__ == "__main__":
    samples = [
        {
            "question": (
                "Một vật rơi tự do trong 5 giây, "
                "tính vận tốc cuối cùng."
            ),
            "history": []
        },
        {
            "question": (
                "Dùng phương trình bậc hai để tính "
                "thời gian vật chạm đất."
            ),
            "history": []
        },
        {
            "question": "Vì sao bước này sai?",
            "history": [
                {
                    "primary_subject": "physics"
                }
            ]
        },
        {
            "question": (
                "Cân bằng phương trình "
                "H2 + O2 -> H2O."
            ),
            "history": []
        },
        {
            "question": (
                "Phần này làm tiếp thế nào?"
            ),
            "history": []
        }
    ]

    for sample in samples:
        print(sample["question"])

        print(
            route_question(
                sample["question"],
                sample["history"]
            )
        )

        print()
