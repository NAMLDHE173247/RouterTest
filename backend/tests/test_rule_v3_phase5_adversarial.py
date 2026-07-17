import sys
from pathlib import Path

V3_SRC = Path(__file__).resolve().parents[2] / "Rule_based_Router" / "rule_based_router_v3" / "router_experiment" / "src"
if str(V3_SRC) not in sys.path:
    sys.path.insert(0, str(V3_SRC))

from rule_router import route_question  # noqa: E402


def route(text, history=None):
    return route_question(text, history or [])


def test_multimeaning_and_negation_adversarial_cases():
    assert route("Tính tan 30 độ trong lượng giác")["primary_subject"] == "math"
    assert route("Không cần gợi ý, hãy giải bài rơi tự do")["intent"] == "solve_problem"
    assert route("Đừng chỉ gợi ý; hãy kiểm tra đáp án 12 m/s")["intent"] == "check_answer"


def test_entity_only_and_stem_oos_are_not_false_positives():
    assert route("CO2")["secondary_subjects"] == []
    assert route("Thời tiết hôm nay có mưa không?")["trace"]["scope"]["scope_state"] == "CONFIRMED_OUT_OF_SCOPE"
    assert route("Tính pH của dung dịch HCl")["trace"]["scope"]["scope_state"] == "CONFIRMED_STEM"


def test_interdisciplinary_and_history_adversarial_cases():
    ideal_gas = route("Tính áp suất khí CO2 theo PV=nRT trong bình kín")
    assert ideal_gas["primary_subject"] == "physics"
    assert "chemistry" in ideal_gas["secondary_subjects"]
    follow_up = route("Còn cách khác không?")
    assert follow_up["need_clarification"] is True
    switched = route("Tính đạo hàm của x^2", [{"question": "Giải phương trình HCl tác dụng với kim loại", "primary_subject": "chemistry"}])
    assert switched["primary_subject"] == "math"
