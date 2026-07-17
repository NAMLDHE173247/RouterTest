import json
import sys
from pathlib import Path

import pytest


V3_SRC = (
    Path(__file__).resolve().parents[2]
    / "Rule_based_Router"
    / "rule_based_router_v3"
    / "router_experiment"
    / "src"
)
if str(V3_SRC) not in sys.path:
    sys.path.insert(0, str(V3_SRC))

from rule_router import route_question  # noqa: E402


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "Rule_based_Router"
    / "rule_based_router_v2"
    / "router_experiment"
    / "data"
    / "test_router.jsonl"
)


def route(question, history=None):
    return route_question(question, history or [])


def test_follow_up_inherits_subject_and_topic_with_trace():
    result = route(
        "vậy bước tiếp theo là gì?",
        [{"primary_subject": "math", "topic": "math.algebra.quadratic"}],
    )
    context = result["trace"]["router_context"]
    assert result["primary_subject"] == "math"
    assert result["topic"] == "math.algebra.quadratic"
    assert context["inherited_fields"] == ["primary_subject", "topic"]
    assert context["source_turn"] == 0
    assert context["history_weight"] == 1.0


def test_subject_switch_resets_context_and_current_evidence_wins():
    result = route(
        "lực ma sát tác dụng như thế nào?",
        [{"primary_subject": "math", "topic": "math.algebra.quadratic"}],
    )
    context = result["trace"]["router_context"]
    assert result["primary_subject"] == "physics"
    assert context["inherited_fields"] == []
    assert context["reset_reason"] == "current_subject_switch"


def test_topic_switch_within_subject_resets_only_topic_context():
    result = route(
        "đạo hàm âm thì hàm số tăng hay giảm?",
        [{"primary_subject": "math", "topic": "math.algebra.quadratic"}],
    )
    context = result["trace"]["router_context"]
    assert result["primary_subject"] == "math"
    assert result["topic"] == "math.calculus.derivative"
    assert context["reset_reason"] == "current_topic_switch"


def test_history_decay_prevents_strong_inheritance():
    history = [{"primary_subject": "math", "topic": "math.algebra.quadratic"}]
    history.extend({"question": "đây là một lượt trung gian"} for _ in range(5))
    result = route("vậy tiếp theo?", history)
    context = result["trace"]["router_context"]
    assert result["primary_subject"] == "unknown"
    assert context["history_weight"] < 0.25
    assert context["reset_reason"] == "history_decay_expired"


def test_follow_up_without_history_is_missing_context_not_inferred():
    result = route("vậy bước tiếp theo là gì?")
    context = result["trace"]["router_context"]
    assert result["primary_subject"] == "unknown"
    assert result["need_clarification"] is True
    assert context["missing_history"] is True
    assert context["reset_reason"] == "missing_history"


def test_history_follow_up_beats_current_weak_calculation_token():
    rows = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    row = next(row for row in rows if row["id"] == "q247")
    result = route(row["question"], row["history"])
    assert result["intent"] == "ask_follow_up"
    assert result["trace"]["intent"]["history_context"]


@pytest.mark.parametrize(
    "question",
    [
        "không cần gợi ý, giải luôn bài này",
        "đừng chỉ gợi ý, hãy giải đầy đủ",
    ],
)
def test_phase2_negative_hint_adversarial_guard(question):
    result = route(question)
    assert result["intent"] == "solve_problem"
    assert any(
        item["rule_id"] == "intent.phase3.veto.hint.negative_request"
        for item in result["trace"]["intent"]["vetoes"]
    )


def test_trace_contains_context_provenance_fields():
    result = route(
        "vậy tiếp theo?",
        [{"primary_subject": "physics", "topic": "physics.mechanics.force", "intent": "ask_follow_up"}],
    )
    context = result["trace"]["router_context"]
    for field in (
        "source_turn",
        "history_weight",
        "inherited_fields",
        "reset_reason",
        "context_confidence",
    ):
        assert field in context
