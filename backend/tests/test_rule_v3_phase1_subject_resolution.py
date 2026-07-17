import json
import sys
from pathlib import Path

import pytest


V3_SRC = Path(__file__).resolve().parents[2] / "Rule_based_Router" / "rule_based_router_v3" / "router_experiment" / "src"
if str(V3_SRC) not in sys.path:
    sys.path.insert(0, str(V3_SRC))

from models import RuleMatch  # noqa: E402
from topic_resolver import extract_topic_matches, resolve_subject  # noqa: E402


DATASET_PATH = Path(__file__).resolve().parents[2] / "Rule_based_Router" / "rule_based_router_v2" / "router_experiment" / "data" / "test_router.jsonl"


def route(question: str):
    return resolve_subject(question)


@pytest.mark.parametrize("sample_id", ["q046", "q069", "q075", "q093", "q136", "q138", "q143", "q146", "q192"])
def test_phase1_1_required_regressions_resolve_to_gold_subject(sample_id):
    rows = [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    row = next(row for row in rows if row["id"] == sample_id)
    assert route(row["question"]).primary_subject == row["primary_subject"]


@pytest.mark.parametrize(
    ("question", "subject"),
    [
        ("CO2", "unknown"),
        ("khí hidro bay lên", "unknown"),
        ("HCl", "unknown"),
        ("CO2 làm đục nước vôi trong", "chemistry"),
        ("kim loại phản ứng với HCl", "chemistry"),
        ("NaCl tan trong nước", "chemistry"),
        ("khí CO2 theo phương trình khí lí tưởng PV=nRT", "physics"),
        ("vật đứng yên vẫn chịu tác dụng của lực", "physics"),
    ],
)
def test_contextual_entities_and_independent_support_evidence(question, subject):
    assert route(question).primary_subject == subject


def test_ambiguous_terms_do_not_cross_match():
    trig_matches = extract_topic_matches("tan được trong nước và chất tan trong dung dịch")
    assert not any(match.topic == "math.trigonometry" for match in trig_matches)

    experiment_matches = extract_topic_matches("thí nghiệm nhận biết khí CO2")
    assert not any(
        match.topic in {"math.algebra.linear_equation", "math.algebra.quadratic"}
        and match.source == "support_term"
        for match in experiment_matches
    )


def test_true_subject_tie_returns_unknown_instead_of_definition_order(monkeypatch):
    tied_matches = [
        RuleMatch("subject.math.test.one", "math", "math.test", "support_term", "alpha", 0, 5, 1),
        RuleMatch("subject.math.test.two", "math", "math.test", "support_term", "beta", 6, 10, 1),
        RuleMatch("subject.physics.test.one", "physics", "physics.test", "support_term", "alpha", 0, 5, 1),
        RuleMatch("subject.physics.test.two", "physics", "physics.test", "support_term", "beta", 6, 10, 1),
    ]
    monkeypatch.setattr("topic_resolver.extract_topic_matches", lambda _question: tied_matches)
    assert route("synthetic tie").primary_subject == "unknown"


def test_rule_ids_are_unique_per_term_and_context_rule_is_explicit():
    matches = extract_topic_matches("giải phương trình bậc nhất x + 2 = 5")
    rule_ids = [match.rule_id for match in matches]
    assert len(rule_ids) == len(set(rule_ids))
    assert all(rule_id.rsplit(".", 1)[-1].split("_", 1)[0].isdigit() for rule_id in rule_ids)

    contextual = extract_topic_matches("CO2 làm đục nước vôi trong")
    assert any(match.rule_id == "subject.chemistry.context.co2_limewater" for match in contextual)


def test_single_support_term_does_not_own_a_subject():
    assert route("áp suất").primary_subject == "unknown"
