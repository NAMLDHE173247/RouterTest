"""Typed models for Rule V3 Phase 1 topic rules."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class TopicDefinition:
    topic_id: str
    primary_subject: str
    branch: str
    strong_terms: tuple[str, ...] = ()
    support_terms: tuple[str, ...] = ()
    formula_patterns: tuple[str, ...] = ()
    unit_patterns: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    negative_terms: tuple[str, ...] = ()
    minimum_evidence: int = 2
    owner_rule: str = "topic_evidence"
    description: str = ""


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    label: str
    topic: str
    source: str
    matched_text: str
    start: int
    end: int
    score: int
    is_entity: bool = False

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "label": self.label,
            "topic": self.topic,
            "source": self.source,
            "matched_text": self.matched_text,
            "start": self.start,
            "end": self.end,
            "score": self.score,
            "is_entity": self.is_entity,
        }


@dataclass
class TopicResolution:
    primary_subject: str
    secondary_subjects: list[str]
    subject_scores: dict[str, int]
    top_score: int
    second_score: int
    topic: Optional[str]
    matched_terms: list[str] = field(default_factory=list)
    matches: list[RuleMatch] = field(default_factory=list)
    inherited_from_history: bool = False
    ownership_override: Optional[dict] = None
    secondary_reasons: dict[str, str] = field(default_factory=dict)

    @property
    def is_interdisciplinary(self) -> bool:
        return bool(self.secondary_subjects)

    def trace(self) -> dict:
        return {
            "topic": self.topic,
            "rule_matches": [match.as_dict() for match in self.matches],
            "subject_scores": self.subject_scores,
            "primary_subject": self.primary_subject,
            "secondary_subjects": self.secondary_subjects,
            "inherited_from_history": self.inherited_from_history,
            "ownership_override": self.ownership_override,
            "secondary_reasons": self.secondary_reasons,
        }
