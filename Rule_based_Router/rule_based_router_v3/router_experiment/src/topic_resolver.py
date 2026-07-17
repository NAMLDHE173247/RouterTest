"""Context-aware Subject -> Topic resolver for Rule V3 Phase 1.1."""

import re
import unicodedata
from collections import defaultdict

from keyword_matcher import normalize_text
from models import RuleMatch, TopicDefinition, TopicResolution
from topic_ontology import TOPIC_DEFINITIONS


VALID_SUBJECTS = ("math", "physics", "chemistry")
SOURCE_WEIGHTS = {
    "strong_term": 3,
    "support_term": 1,
    "formula": 3,
    "unit": 2,
    "entity": 0,
    "entity_context": 4,
}
NEAR_TIE_MARGIN = 1


OWNERSHIP_OVERRIDES = (
    {
        "rule_id": "subject.physics.override.buoyancy_gas_context",
        "pattern": r"(?:bóng bay|khí hidro|khí heli).{0,100}(?:lực đẩy|lực nổi|ác[- ]si[- ]mét)|(?:lực đẩy|lực nổi|ác[- ]si[- ]mét).{0,100}(?:bóng bay|khí hidro|khí heli)",
        "final_winner": "physics",
        "reason": "The gas is used in a buoyancy/Archimedes context, so Physics owns the decision.",
    },
    {
        "rule_id": "subject.chemistry.override.fuel_combustion_energy",
        "pattern": r"xăng.{0,80}(?:năng lượng hóa học|động năng)|(?:năng lượng hóa học|động năng).{0,80}xăng",
        "final_winner": "chemistry",
        "reason": "The requested relationship is the chemical energy of fuel combustion; vehicle motion is its consequence.",
    },
    {
        "rule_id": "subject.physics.override.gas_work_piston",
        "pattern": r"(?:số mol.{0,80}công khí|công khí.{0,80}số mol|đẩy piston).{0,60}(?:h2|khí|mol)?",
        "final_winner": "physics",
        "reason": "The question asks for gas work and piston mechanics, so Physics owns the decision.",
    },
    {
        "rule_id": "subject.chemistry.override.chemical_thermal_reaction",
        "pattern": r"(?:hòa tan muối|năng lượng phản ứng hóa học).{0,100}(?:nước lạnh|nhiệt học|nhiệt độ)",
        "final_winner": "chemistry",
        "reason": "The question asks about chemical reaction energy during dissolution; temperature is the observed effect.",
    },
    {
        "rule_id": "subject.chemistry.override.combustion_stoichiometry",
        "pattern": r"(?:đốt cháy|phản ứng cháy).{0,60}(?:\bmol\b|ch4|h2|nước)",
        "final_winner": "chemistry",
        "reason": "Combustion stoichiometry owns the question; heat is a consequence, not the primary subject.",
    },
    {
        "rule_id": "subject.physics.override.thermal_calculation",
        "pattern": r"lượng nhiệt.{0,80}(?:bay hơi|đun).{0,80}(?:phản ứng cháy|bếp gas|gas)",
        "final_winner": "physics",
        "reason": "The requested heat/phase-change calculation owns the question; combustion is contextual input.",
    },
    {
        "rule_id": "subject.physics.override.electrical_potential_comparison",
        "pattern": r"(?:suất điện động.{0,80}hiệu điện thế|hiệu điện thế.{0,80}suất điện động)",
        "final_winner": "physics",
        "reason": "The comparison is between electrical potential quantities, so Physics owns the decision.",
    },
)


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_value).strip("_")
    return slug[:48] or "pattern"


def _rule_id(topic: TopicDefinition, source: str, value: str, index: int) -> str:
    return (
        f"subject.{topic.primary_subject}.{topic.branch}."
        f"{topic.topic_id.rsplit('.', 1)[-1]}.{source}.{index:02d}_{_slug(value)}"
    )


def _find_term_matches(text: str, term: str):
    pattern = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", flags=re.IGNORECASE)
    return pattern.finditer(text)


def _find_pattern_matches(text: str, pattern: str):
    try:
        return re.finditer(pattern, text, flags=re.IGNORECASE)
    except re.error:
        return ()


def _is_negative_context(text: str, start: int, end: int, negative_terms: tuple[str, ...]) -> bool:
    if not negative_terms:
        return False
    window = text[max(0, start - 32): min(len(text), end + 32)]
    return any(normalize_text(term) in window for term in negative_terms)


def _match_topic(text: str, topic: TopicDefinition) -> list[RuleMatch]:
    matches: list[RuleMatch] = []

    def add_terms(terms, source, score, is_entity=False):
        for index, term in enumerate(terms, start=1):
            normalized_term = normalize_text(term)
            for match in _find_term_matches(text, normalized_term):
                if not is_entity and _is_negative_context(
                    text, match.start(), match.end(), topic.negative_terms
                ):
                    continue
                matches.append(RuleMatch(
                    rule_id=_rule_id(topic, source, term, index),
                    label=topic.primary_subject,
                    topic=topic.topic_id,
                    source=source,
                    matched_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    score=score,
                    is_entity=is_entity,
                ))

    add_terms(topic.strong_terms, "strong_term", SOURCE_WEIGHTS["strong_term"])
    add_terms(topic.support_terms, "support_term", SOURCE_WEIGHTS["support_term"])
    add_terms(topic.entities, "entity", SOURCE_WEIGHTS["entity"], is_entity=True)
    for index, pattern in enumerate(topic.formula_patterns, start=1):
        for match in _find_pattern_matches(text, pattern):
            matches.append(RuleMatch(
                _rule_id(topic, "formula", pattern, index), topic.primary_subject,
                topic.topic_id, "formula", match.group(0), match.start(), match.end(),
                SOURCE_WEIGHTS["formula"],
            ))
    for index, pattern in enumerate(topic.unit_patterns, start=1):
        for match in _find_pattern_matches(text, pattern):
            matches.append(RuleMatch(
                _rule_id(topic, "unit", pattern, index), topic.primary_subject,
                topic.topic_id, "unit", match.group(0), match.start(), match.end(),
                SOURCE_WEIGHTS["unit"],
            ))
    return matches


# Entities remain non-owning by themselves. These explicit context rules turn
# an entity into Chemistry evidence only when the surrounding chemistry phrase
# is present.
CONTEXTUAL_ENTITY_RULES = (
    (
        "subject.chemistry.context.co2_limewater",
        r"(?:\bco2\b|khí\s+co2).{0,50}(?:nước\s+vôi|vôi\s+trong|ca\s*\(\s*oh\s*\)\s*2)|(?:nước\s+vôi|vôi\s+trong).{0,50}(?:\bco2\b|khí\s+co2)",
    ),
    (
        "subject.chemistry.context.gas_identification",
        r"nhận\s+biết.{0,35}(?:khí|co2|o2|h2|hcl)|(?:khí|co2|o2|h2|hcl).{0,35}nhận\s+biết",
    ),
    (
        "subject.chemistry.context.hcl_metal",
        r"(?:hcl|axit\s+clohidric).{0,40}kim\s+loại|kim\s+loại.{0,40}(?:hcl|axit\s+clohidric)",
    ),
    (
        "subject.chemistry.context.nacl_water",
        r"(?:nacl|muối\s+ăn).{0,40}(?:tan\s+trong\s+nước|hòa\s+tan)|(?:tan\s+trong\s+nước|hòa\s+tan).{0,40}(?:nacl|muối\s+ăn)",
    ),
)


def _contextual_entity_matches(text: str) -> list[RuleMatch]:
    matches = []
    for rule_id, pattern in CONTEXTUAL_ENTITY_RULES:
        for match in _find_pattern_matches(text, pattern):
            matches.append(RuleMatch(
                rule_id=rule_id,
                label="chemistry",
                topic="chemistry.contextual_entity",
                source="entity_context",
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                score=SOURCE_WEIGHTS["entity_context"],
                is_entity=True,
            ))
    return matches


def extract_topic_matches(question: str) -> list[RuleMatch]:
    text = normalize_text(question)
    matches = _contextual_entity_matches(text)
    for topic in TOPIC_DEFINITIONS:
        matches.extend(_match_topic(text, topic))
    unique = {}
    for match in matches:
        key = (match.rule_id, match.start, match.end)
        unique[key] = match
    return list(unique.values())


def _topic_score(matches: list[RuleMatch], topic: TopicDefinition) -> int:
    topic_matches = [match for match in matches if match.topic == topic.topic_id]
    score = sum(match.score for match in topic_matches)
    return score if score >= topic.minimum_evidence else 0


def _subject_signature(subject: str, matches: list[RuleMatch]) -> tuple[int, int, int, int, int]:
    relevant = [
        match for match in matches
        if match.label == subject and (not match.is_entity or match.source == "entity_context")
    ]
    independent = {(match.rule_id, match.start, match.end) for match in relevant}
    contextual = sum(match.source == "entity_context" for match in relevant)
    formulas = sum(match.source == "formula" for match in relevant)
    max_phrase_length = max((len(match.matched_text) for match in relevant), default=0)
    score = sum(match.score for match in relevant)
    return (contextual, max_phrase_length, formulas, len(independent), score)


def _rank_subjects(matches: list[RuleMatch]):
    ranked = []
    for subject in VALID_SUBJECTS:
        relevant = [
            match for match in matches
            if match.label == subject and (not match.is_entity or match.source == "entity_context")
        ]
        score = sum(match.score for match in relevant)
        signature = _subject_signature(subject, matches)
        # A lone support term remains below the subject threshold.
        if score >= 2:
            ranked.append((subject, score, signature))
    return sorted(ranked, key=lambda item: (item[2], item[0]), reverse=True)


def _match_ownership_override(text: str) -> dict | None:
    candidates = []
    for override in OWNERSHIP_OVERRIDES:
        for match in _find_pattern_matches(text, override["pattern"]):
            candidates.append((len(match.group(0)), override))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]["rule_id"]))[1]


def resolve_subject(question: str, history_subject: str | None = None) -> TopicResolution:
    matches = extract_topic_matches(question)
    normalized_question = normalize_text(question)
    subject_scores = {subject: 0 for subject in VALID_SUBJECTS}
    for subject in VALID_SUBJECTS:
        subject_scores[subject] = sum(
            match.score for match in matches
            if match.label == subject and (not match.is_entity or match.source == "entity_context")
        )

    topic_scores = {
        topic.topic_id: _topic_score(matches, topic)
        for topic in TOPIC_DEFINITIONS
    }
    ranked_subjects = _rank_subjects(matches)
    primary_subject = "unknown"
    top_score = 0
    second_score = 0
    ownership_override = None
    if ranked_subjects:
        score_ranked = sorted(ranked_subjects, key=lambda item: (item[1], item[0]), reverse=True)
        score_winner, score_winner_score = score_ranked[0][0], score_ranked[0][1]
        second_score = score_ranked[1][1] if len(score_ranked) > 1 else 0
        score_margin = score_winner_score - second_score
        # The score winner is the default. Tie-breaks are only consulted for
        # equal scores; a near tie remains score-owned unless an explicit
        # ownership rule below overrides it.
        primary_subject, top_score = score_winner, score_winner_score
        if score_margin == 0:
            tied = [item for item in score_ranked if item[1] == score_winner_score]
            best_signature = max(item[2] for item in tied)
            signature_winners = [item[0] for item in tied if item[2] == best_signature]
            if len(signature_winners) == 1:
                primary_subject = signature_winners[0]
            else:
                primary_subject = "unknown"
                top_score = 0
        elif score_margin <= NEAR_TIE_MARGIN:
            # This branch is intentionally observable and configurable, but
            # does not silently invert the score winner.
            primary_subject = score_winner
        if primary_subject == "unknown" and history_subject in VALID_SUBJECTS:
            primary_subject = history_subject
            top_score = subject_scores[history_subject]
    elif history_subject in VALID_SUBJECTS:
        primary_subject = history_subject

    override_rule = _match_ownership_override(normalized_question)
    if override_rule:
        score_winner = max(
            VALID_SUBJECTS, key=lambda subject: (subject_scores[subject], subject)
        )
        final_winner = override_rule["final_winner"]
        runner_up_score = max(
            (subject_scores[subject] for subject in VALID_SUBJECTS if subject != score_winner),
            default=0,
        )
        ownership_override = {
            "rule_id": override_rule["rule_id"],
            "reason": override_rule["reason"],
            "score_winner": score_winner,
            "score_winner_score": subject_scores[score_winner],
            "final_winner": final_winner,
            "final_winner_score": subject_scores[final_winner],
            "decision_margin": subject_scores[score_winner] - runner_up_score,
            "override_score_delta": abs(subject_scores[score_winner] - subject_scores[final_winner]),
        }
        primary_subject = final_winner
        top_score = subject_scores[final_winner]

    subject_topics = []
    if primary_subject != "unknown":
        for match in matches:
            if match.label == primary_subject and match.source == "entity_context":
                subject_topics.append((match.topic, len(match.matched_text), 1, match.score))
        for topic in TOPIC_DEFINITIONS:
            topic_matches = [
                match for match in matches
                if match.topic == topic.topic_id and match.label == primary_subject
            ]
            if topic_matches and topic_scores[topic.topic_id] > 0:
                independent = len({(m.rule_id, m.start, m.end) for m in topic_matches})
                subject_topics.append((topic.topic_id, max(len(m.matched_text) for m in topic_matches), independent, topic_scores[topic.topic_id]))
    primary_topic = None
    if subject_topics:
        topic_rank = sorted(subject_topics, key=lambda item: (item[3], item[2], item[1], item[0]), reverse=True)
        if len(topic_rank) == 1 or topic_rank[0][1:] != topic_rank[1][1:]:
            primary_topic = topic_rank[0][0]

    primary_matches = [match for match in matches if match.topic == primary_topic]
    secondary_subjects = []
    primary_score = subject_scores.get(primary_subject, 0)
    for subject, score, _ in ranked_subjects:
        if subject == primary_subject or score < 2:
            continue
        if primary_score and score / primary_score >= 0.35:
            secondary_subjects.append(subject)

    return TopicResolution(
        primary_subject=primary_subject,
        secondary_subjects=secondary_subjects,
        subject_scores=subject_scores,
        top_score=primary_score,
        second_score=second_score,
        topic=primary_topic,
        matched_terms=[match.matched_text for match in primary_matches],
        matches=matches,
        ownership_override=ownership_override,
    )
