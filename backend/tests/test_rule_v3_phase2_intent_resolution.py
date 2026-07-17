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

from rule_router import detect_intent  # noqa: E402


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "Rule_based_Router"
    / "rule_based_router_v2"
    / "router_experiment"
    / "data"
    / "test_router.jsonl"
)


def intent(question, history=None):
    return detect_intent(question, history or [])


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("sai ở bước nào trong lời giải?", "diagnose_error"),
        ("đáp án có đúng không?", "check_answer"),
        ("chỉ gợi ý thôi", "give_hint"),
        ("đừng giải hết bài này", "give_hint"),
        ("không cần lời giải, chỉ hướng dẫn", "give_hint"),
        ("có cần biết bản chất phần này không?", "explain_concept"),
    ],
)
def test_contextual_intent_positive(question, expected):
    assert intent(question)["intent"] == expected


def test_arithmetic_progression_phrase_does_not_trigger_diagnosis():
    result = intent("tìm số hạng thứ 10 của cấp số cộng, công sai bằng 3")
    assert result["intent"] == "solve_problem"
    assert any(
        veto["rule_id"] == "intent.phase2.veto.diagnose.cong_sai"
        for veto in result["trace"]["vetoes"]
    )


def test_formula_error_is_diagnosis_even_with_calculation_token():
    result = intent("em tính sai công thức ở đâu vậy?")
    assert result["intent"] == "diagnose_error"


def test_hint_veto_is_traceable_and_beats_solve_token():
    result = intent("đừng giải hết, chỉ gợi ý cách làm")
    veto = next(
        item for item in result["trace"]["vetoes"]
        if item["rule_id"] == "intent.phase2.veto.solve.hint_request"
    )
    assert result["intent"] == "give_hint"
    assert veto["reason"]
    assert result["trace"]["decision_margin"] >= 0


def test_follow_up_requires_history_context():
    assert intent("vậy bước tiếp theo là gì?")["intent"] != "ask_follow_up"
    result = intent(
        "vậy bước tiếp theo là gì?",
        history=[{"question": "Giải phương trình x + 1 = 2"}],
    )
    assert result["intent"] == "ask_follow_up"
    assert any(
        item["rule_id"] == "intent.phase2.follow_up.context.history"
        for item in result["trace"]["rule_matches"]
    )


@pytest.mark.parametrize("sample_id", ["q006", "q189"])
def test_dataset_intent_regressions_are_preserved(sample_id):
    rows = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    row = next(row for row in rows if row["id"] == sample_id)
    assert intent(row["question"])["intent"] == row["intent"]


def test_trace_has_explicit_rule_ids_and_decision_fields():
    trace = intent("đáp án có đúng không?")["trace"]
    assert any(item["source"] == "context_rule" for item in trace["rule_matches"])
    assert trace["selected_intent"] == "check_answer"
    assert "top_score" in trace
    assert "second_score" in trace
    assert "decision_margin" in trace
