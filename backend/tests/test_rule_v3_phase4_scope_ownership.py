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


def route(question, history=None):
    return route_question(question, history or [])


def test_ideal_gas_co2_has_physics_primary_and_chemistry_secondary():
    result = route("khí CO2 theo phương trình khí lí tưởng PV=nRT")
    assert result["primary_subject"] == "physics"
    assert result["secondary_subjects"] == ["chemistry"]
    assert result["trace"]["secondary_reasons"]["chemistry"] == "subject.chemistry.supporting.ideal_gas_entity_context"


def test_chemical_reaction_thermal_context_owns_primary():
    result = route("phản ứng cháy tỏa nhiệt, áp suất tăng")
    assert result["primary_subject"] == "chemistry"
    assert result["trace"]["ownership_override"]["rule_id"] == "subject.chemistry.override.reaction_thermal_focus"


def test_physics_kinematics_equation_owns_primary_and_math_is_tool_subject():
    result = route("giải phương trình chuyển động rơi tự do v = gt")
    assert result["primary_subject"] == "physics"
    assert result["secondary_subjects"] == ["math"]
    assert result["trace"]["ownership_override"]["rule_id"] == "subject.physics.override.kinematics_equation_focus"


@pytest.mark.parametrize("question", ["CO2", "HCl", "O2"])
def test_entity_alone_does_not_create_secondary(question):
    result = route(question)
    assert result["secondary_subjects"] == []
    assert result["primary_subject"] == "unknown"


def test_confirmed_oos_beats_ambiguous_keyword_and_does_not_clarify():
    result = route("Tối nay ở Hà Nội có nên đi chơi không hay trời sẽ mưa?")
    assert result["trace"]["scope"]["scope_state"] == "CONFIRMED_OUT_OF_SCOPE"
    assert result["target_slm"] == "general_tutor"
    assert result["need_clarification"] is False


def test_confirmed_stem_beats_oos_ambiguous_word():
    result = route("tan trong nước và áp suất khí theo PV=nRT")
    assert result["trace"]["scope"]["scope_state"] == "CONFIRMED_STEM"
    assert result["primary_subject"] == "physics"


def test_unknown_scope_requires_clarification_with_reason_code():
    result = route("CO2")
    assert result["trace"]["scope"]["scope_state"] == "UNKNOWN_SCOPE"
    assert result["need_clarification"] is True
    assert result["clarification_reason_code"] == "NO_SUBJECT_EVIDENCE"


def test_follow_up_without_history_reason_code_is_preserved():
    result = route("vậy bước tiếp theo là gì?")
    assert result["need_clarification"] is True
    assert result["clarification_reason_code"] == "MISSING_HISTORY_FOR_FOLLOW_UP"


def test_subject_conflict_reason_code_is_traceable():
    result = route("áp suất và nhiệt độ của khí trong bình kín thay đổi thế nào?")
    if result["need_clarification"]:
        assert result["clarification_reason_code"] in {
            "CROSS_DOMAIN_CONFLICT",
            "LOW_CONFIDENCE",
            "NO_SUBJECT_EVIDENCE",
        }


def test_every_clarifying_route_has_reason_code():
    for question in ["CO2", "vậy bước tiếp theo là gì?", "phần này là gì?"]:
        result = route(question)
        if result["need_clarification"]:
            assert result["clarification_reason_code"]
