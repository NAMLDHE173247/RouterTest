"""Phase 3 dialogue context extraction and decay policy."""

from dataclasses import dataclass, field

from keyword_matcher import normalize_text
from models import TopicResolution
from topic_resolver import VALID_SUBJECTS, resolve_subject


DEFAULT_HISTORY_DECAY = 0.75
MIN_HISTORY_WEIGHT = 0.25


@dataclass
class RouterContext:
    last_explicit_subject: str | None = None
    last_topic: str | None = None
    last_intent: str | None = None
    active_entities: list[str] = field(default_factory=list)
    turns_since_explicit_subject: int | None = None
    pending_clarification: bool = False
    context_confidence: float = 0.0
    history_weight: float = 0.0
    source_turn: int | None = None
    inherited_fields: list[str] = field(default_factory=list)
    reset_reason: str | None = None
    missing_history: bool = False

    def as_dict(self) -> dict:
        return {
            "last_explicit_subject": self.last_explicit_subject,
            "last_topic": self.last_topic,
            "last_intent": self.last_intent,
            "active_entities": self.active_entities,
            "turns_since_explicit_subject": self.turns_since_explicit_subject,
            "pending_clarification": self.pending_clarification,
            "context_confidence": round(self.context_confidence, 4),
            "history_weight": round(self.history_weight, 4),
            "source_turn": self.source_turn,
            "inherited_fields": self.inherited_fields,
            "reset_reason": self.reset_reason,
            "missing_history": self.missing_history,
        }


def _history_text(item) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return ""
    for key in ("question", "content", "message", "text", "answer"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _turn_state(item) -> dict:
    text = _history_text(item)
    resolved = resolve_subject(text) if text else None
    explicit_subject = None
    topic = None
    intent = None
    entities = []
    pending = False

    if isinstance(item, dict):
        candidate = item.get("primary_subject") or item.get("subject")
        if candidate in VALID_SUBJECTS:
            explicit_subject = candidate
        topic = item.get("topic")
        intent = item.get("intent")
        pending = bool(item.get("need_clarification", False))
        raw_entities = item.get("active_entities") or item.get("entities") or []
        if isinstance(raw_entities, (list, tuple)):
            entities.extend(str(entity) for entity in raw_entities)

    if resolved and resolved.primary_subject in VALID_SUBJECTS and resolved.top_score >= 2:
        explicit_subject = explicit_subject or resolved.primary_subject
        topic = topic or resolved.topic
        entities.extend(
            match.matched_text
            for match in resolved.matches
            if match.is_entity
        )

    deduped_entities = list(dict.fromkeys(entities))
    return {
        "explicit_subject": explicit_subject,
        "topic": topic,
        "intent": intent,
        "entities": deduped_entities,
        "pending_clarification": pending,
    }


def build_router_context(
    history: list,
    current_subject: TopicResolution,
    current_intent: str | None,
    current_topic: str | None,
    decay: float = DEFAULT_HISTORY_DECAY,
) -> RouterContext:
    context = RouterContext(missing_history=not history)
    if not history:
        context.reset_reason = "missing_history"
        return context

    states = [_turn_state(item) for item in history]
    subject_index = next(
        (index for index in range(len(states) - 1, -1, -1) if states[index]["explicit_subject"]),
        None,
    )
    latest_index = len(states) - 1
    if subject_index is None:
        context.reset_reason = "no_explicit_subject_in_history"
        return context

    state = states[subject_index]
    turns_since = latest_index - subject_index
    weight = decay ** turns_since
    context.last_explicit_subject = state["explicit_subject"]
    context.last_topic = state["topic"]
    context.last_intent = state["intent"]
    context.active_entities = state["entities"]
    context.turns_since_explicit_subject = turns_since
    context.pending_clarification = states[latest_index]["pending_clarification"]
    context.history_weight = weight
    context.source_turn = subject_index
    context.context_confidence = min(1.0, 0.55 + 0.45 * weight)

    if weight < MIN_HISTORY_WEIGHT:
        context.reset_reason = "history_decay_expired"

    if current_subject.primary_subject not in {"unknown", context.last_explicit_subject}:
        context.reset_reason = "current_subject_switch"
    elif (
        current_topic
        and context.last_topic
        and current_topic != context.last_topic
        and current_subject.primary_subject in {"unknown", context.last_explicit_subject}
    ):
        context.reset_reason = "current_topic_switch"
    elif current_subject.primary_subject == context.last_explicit_subject:
        context.reset_reason = None

    if current_subject.primary_subject not in {"unknown", context.last_explicit_subject}:
        context.context_confidence *= 0.5
    if current_intent and context.last_intent and current_intent != context.last_intent:
        context.reset_reason = context.reset_reason or "current_intent_switch"
    if (
        current_topic
        and context.last_topic
        and current_topic != context.last_topic
        and current_subject.primary_subject in {"unknown", context.last_explicit_subject}
    ):
        context.reset_reason = "current_topic_switch"
    return context


def history_is_usable(context: RouterContext) -> bool:
    return bool(
        context.last_explicit_subject
        and context.history_weight >= MIN_HISTORY_WEIGHT
        and not context.reset_reason
    )
