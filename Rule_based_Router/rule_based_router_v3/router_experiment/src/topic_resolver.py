"""Structured topic matcher and primary-subject resolver for Phase 1."""

import re
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
}


def _find_term_matches(text: str, term: str):
    pattern = re.compile(r"(?<![\wÀ-ỹ])" + re.escape(term) + r"(?![\wÀ-ỹ])")
    return pattern.finditer(text)


def _find_pattern_matches(text: str, pattern: str):
    try:
        return re.finditer(pattern, text, flags=re.IGNORECASE)
    except re.error:
        return ()


def _match_topic(text: str, topic: TopicDefinition) -> list[RuleMatch]:
    matches = []

    def add_terms(terms, source, score, is_entity=False):
        for term in terms:
            for match in _find_term_matches(text, normalize_text(term)):
                rule_id = f"subject.{topic.primary_subject}.{topic.branch}.{topic.topic_id.rsplit('.', 1)[-1]}.{source}"
                matches.append(RuleMatch(
                    rule_id=rule_id,
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
    for pattern in topic.formula_patterns:
        for match in _find_pattern_matches(text, pattern):
            rule_id = f"subject.{topic.primary_subject}.{topic.branch}.{topic.topic_id.rsplit('.', 1)[-1]}.formula"
            matches.append(RuleMatch(rule_id, topic.primary_subject, topic.topic_id, "formula", match.group(0), match.start(), match.end(), SOURCE_WEIGHTS["formula"]))
    for pattern in topic.unit_patterns:
        for match in _find_pattern_matches(text, pattern):
            rule_id = f"subject.{topic.primary_subject}.{topic.branch}.{topic.topic_id.rsplit('.', 1)[-1]}.unit"
            matches.append(RuleMatch(rule_id, topic.primary_subject, topic.topic_id, "unit", match.group(0), match.start(), match.end(), SOURCE_WEIGHTS["unit"]))
    return matches


def extract_topic_matches(question: str) -> list[RuleMatch]:
    text = normalize_text(question)
    matches = []
    for topic in TOPIC_DEFINITIONS:
        matches.extend(_match_topic(text, topic))
    # A repeated term should not multiply evidence.
    unique = {}
    for match in matches:
        key = (match.rule_id, match.start, match.end)
        unique[key] = match
    return list(unique.values())


def _topic_score(matches: list[RuleMatch], topic: TopicDefinition) -> int:
    topic_matches = [match for match in matches if match.topic == topic.topic_id]
    score = sum(match.score for match in topic_matches)
    return score if score >= topic.minimum_evidence else 0


def resolve_subject(question: str, history_subject: str | None = None) -> TopicResolution:
    matches = extract_topic_matches(question)
    subject_scores = defaultdict(int)
    topic_scores = {}
    for topic in TOPIC_DEFINITIONS:
        score = _topic_score(matches, topic)
        topic_scores[topic.topic_id] = score
        subject_scores[topic.primary_subject] += score

    # Entity-only evidence is intentionally zero-weight. A chemistry entity
    # inside an ideal-gas/physics question cannot own the primary subject.
    ranked_topics = sorted(
        ((topic_id, score) for topic_id, score in topic_scores.items() if score > 0),
        key=lambda item: item[1],
        reverse=True,
    )
    ranked_subjects = sorted(
        ((subject, subject_scores[subject]) for subject in VALID_SUBJECTS),
        key=lambda item: item[1],
        reverse=True,
    )
    top_subject, top_score = ranked_subjects[0]
    second_score = ranked_subjects[1][1]
    owner_topic = ranked_topics[0][0] if ranked_topics else None

    # Use topic ownership rather than raw entity/keyword totals for close
    # interdisciplinary cases. The strongest non-entity topic owns the case.
    owner_matches = [match for match in matches if not match.is_entity]
    owner_topic_scores = defaultdict(int)
    for match in owner_matches:
        owner_topic_scores[match.topic] += match.score
    if owner_topic_scores:
        owner_topic = max(owner_topic_scores, key=owner_topic_scores.get)
        owner_subject = next(topic.primary_subject for topic in TOPIC_DEFINITIONS if topic.topic_id == owner_topic)
        if owner_topic_scores[owner_topic] >= 2:
            top_subject = owner_subject
            top_score = subject_scores[owner_subject]

    if top_score < 2:
        primary_subject = history_subject if history_subject else "unknown"
        top_score = max(top_score, 0)
    else:
        primary_subject = top_subject

    primary_score = subject_scores[primary_subject] if primary_subject in subject_scores else 0
    secondary_subjects = []
    for subject, score in ranked_subjects:
        if subject == primary_subject or score < 2:
            continue
        if primary_score and score / primary_score >= 0.35:
            secondary_subjects.append(subject)

    primary_topic = owner_topic if primary_subject != "unknown" else None
    primary_matches = [match for match in matches if match.topic == primary_topic]
    return TopicResolution(
        primary_subject=primary_subject,
        secondary_subjects=secondary_subjects,
        subject_scores=dict(subject_scores),
        top_score=primary_score if primary_subject != "unknown" else top_score,
        second_score=second_score,
        topic=primary_topic,
        matched_terms=[match.matched_text for match in primary_matches],
        matches=matches,
    )
