import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.adapters.hybrid_v0_adapter import HybridRouterError, HybridV0Adapter
from app.schemas.routing import HybridConfig, RouteResponse, RouterDecision, RouterRuntime
from app.fallback_router_executor import FallbackRouterExecutor


def response(router_id: str, subject: str, confidence: float) -> RouteResponse:
    return RouteResponse(
        router_id=router_id,
        router_name=router_id,
        decision=RouterDecision(
            primary_subject=subject,
            secondary_subjects=[],
            intent="solve_problem",
            target_slm="physics_slm" if subject == "physics" else "ask_clarification",
            confidence=confidence,
            need_clarification=subject == "unknown",
            reason="test",
        ),
        runtime=RouterRuntime(router_type=router_id, source="test", latency_ms=1),
    )


class ChildService:
    def __init__(self, family, result=None, error=None):
        self.family = family
        self.result = result
        self.error = error
        self.calls = 0
        self.router_id = "qwen_v0" if family == "slm" else "llm_gemini_v0"
        self.capabilities = {"can_be_hybrid_fallback": family in {"slm", "openrouter_llm"}}

    def is_available(self):
        return True

    def get_metadata(self):
        return {"family": self.family, "available": True, "unavailable_reason": None}

    def route(self, question, history):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class Registry:
    def __init__(self, services):
        self.services = services

    def get(self, router_id):
        return self.services[router_id]


def make_adapter(rule_result, llm_result=None, llm_error=None):
    rule = ChildService("rule_based", rule_result)
    llm = ChildService("openrouter_llm", llm_result, llm_error)
    return HybridV0Adapter(
        Registry({"rule_v3": rule}),
        FallbackRouterExecutor({"llm_gemini_v0": llm}),
    ), rule, llm


def test_reliable_rule_does_not_call_llm():
    adapter, rule, llm = make_adapter(response("rule_v3", "physics", 0.95), response("llm_gemini_v0", "math", 0.9))

    result = adapter.route("question", [], HybridConfig(fallback_router_id="llm_gemini_v0"))

    assert result.runtime.hybrid.selected_source == "rule"
    assert result.runtime.hybrid.llm_called is False
    assert result.runtime.hybrid.fallback_triggers == []
    assert rule.calls == 1
    assert llm.calls == 0


def test_policy_flags_control_unknown_and_clarification_triggers():
    adapter, _, llm = make_adapter(response("rule_v3", "unknown", 0.95), response("llm_gemini_v0", "physics", 0.9))
    config = HybridConfig(fallback_router_id="llm_gemini_v0", fallback_on_unknown_subject=False, fallback_on_need_clarification=False)

    result = adapter.route("question", [], config)

    assert result.runtime.hybrid.selected_source == "rule"
    assert llm.calls == 0


def test_low_confidence_calls_llm_and_uses_llm_decision():
    adapter, _, llm = make_adapter(response("rule_v3", "physics", 0.2), response("llm_gemini_v0", "physics", 0.9))

    result = adapter.route("question", [], HybridConfig(fallback_router_id="llm_gemini_v0"))

    assert result.runtime.hybrid.selected_source == "fallback"
    assert result.runtime.hybrid.fallback_triggers == ["low_confidence"]
    assert llm.calls == 1


def test_llm_failure_falls_back_to_rule_and_marks_degraded():
    adapter, _, llm = make_adapter(
        response("rule_v3", "physics", 0.2),
        llm_error=RuntimeError("upstream failure"),
    )

    result = adapter.route("question", [], HybridConfig(fallback_router_id="llm_gemini_v0"))

    assert result.runtime.hybrid.selected_source == "rule_after_fallback_failure"
    assert result.runtime.hybrid.degraded_mode is True
    assert result.runtime.hybrid.fallback_called is True
    assert llm.calls == 1


def test_hybrid_rejects_wrong_child_family_and_self_reference():
    rule = ChildService("rule_based", response("rule_v3", "physics", 0.9))
    llm = ChildService("openrouter_llm", response("llm_gemini_v0", "physics", 0.9))
    adapter = HybridV0Adapter(Registry({"rule_v3": rule}), FallbackRouterExecutor({"llm_gemini_v0": llm}))

    with pytest.raises(HybridRouterError, match="Hybrid cannot use itself"):
        adapter.route("question", [], HybridConfig(rule_router_id="hybrid", fallback_router_id="llm_gemini_v0"))


def test_qwen_is_supported_by_generic_fallback_executor():
    rule = ChildService("rule_based", response("rule_v3", "physics", 0.2))
    qwen = ChildService("slm", response("qwen_v0", "physics", 0.9))
    adapter = HybridV0Adapter(
        Registry({"rule_v3": rule}),
        FallbackRouterExecutor({"qwen_v0": qwen}),
    )

    result = adapter.route("question", [], HybridConfig(fallback_router_id="qwen_v0"))

    assert result.runtime.hybrid.selected_source == "fallback"
    assert result.runtime.hybrid.fallback_router_id == "qwen_v0"
    assert result.runtime.hybrid.fallback_family == "slm"


def test_hybrid_requires_explicit_fallback_router():
    adapter, _, _ = make_adapter(response("rule_v3", "physics", 0.9))

    with pytest.raises(HybridRouterError, match="explicit fallback_router_id"):
        adapter.route("question", [], HybridConfig())
