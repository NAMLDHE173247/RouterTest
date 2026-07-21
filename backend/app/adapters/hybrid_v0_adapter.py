"""Rule-first policy with a configurable Router fallback."""

import time
from typing import Any, List

from app.schemas.routing import HybridConfig, HybridRuntime, RouteResponse, RouterRuntime
from app.fallback_router_executor import FallbackRouterError


class HybridRouterError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class HybridV0Adapter:
    ID = "hybrid"
    NAME = "Hybrid Router V0"
    FAMILY = "hybrid"
    VERSION = "v0"

    def __init__(self, rule_service: Any, fallback_executor: Any):
        self.rule_service = rule_service
        self.fallback_executor = fallback_executor

    def route(self, question: str, history: List[str] | None = None, config: HybridConfig | None = None) -> RouteResponse:
        if config is None:
            raise HybridRouterError("hybrid_invalid_config", "Hybrid requires an explicit fallback_router_id")
        fallback_router_id = config.resolved_fallback_router_id()
        if not fallback_router_id:
            raise HybridRouterError("hybrid_invalid_config", "Hybrid requires an explicit fallback_router_id")
        self._validate_config(config, fallback_router_id)
        history = history or []
        started = time.perf_counter()

        rule_response = None
        rule_error_code = None
        try:
            rule_response = self.rule_service.get(config.rule_router_id).route(question, history)
        except Exception as exc:
            rule_error_code = "hybrid_rule_failed"
            if not config.fallback_on_rule_error:
                raise HybridRouterError(rule_error_code, "Selected Rule Router failed") from exc

        triggers = self._fallback_triggers(rule_response, config) if rule_response else ["rule_error"]
        if not triggers:
            return self._build_response(config, fallback_router_id, rule_response, None, "rule", [], None, started)

        try:
            fallback_response = self.fallback_executor.execute(fallback_router_id, question, history)
            return self._build_response(config, fallback_router_id, rule_response, fallback_response, "fallback", triggers, rule_error_code, started)
        except FallbackRouterError as exc:
            if rule_response is not None and config.fallback_failure_policy == "use_rule":
                return self._build_response(config, fallback_router_id, rule_response, None, "rule_after_fallback_failure", triggers, exc.code, started)
            raise HybridRouterError("hybrid_both_failed", "Both selected Rule and fallback Routers failed") from exc
        except Exception as exc:
            if rule_response is not None and config.fallback_failure_policy == "use_rule":
                return self._build_response(config, fallback_router_id, rule_response, None, "rule_after_fallback_failure", triggers, "hybrid_fallback_failed", started)
            raise HybridRouterError("hybrid_both_failed", "Both selected Rule and fallback Routers failed") from exc

    def _validate_config(self, config: HybridConfig, fallback_router_id: str) -> None:
        if config.rule_router_id == self.ID or fallback_router_id == self.ID:
            raise HybridRouterError("hybrid_invalid_config", "Hybrid cannot use itself as a child Router")
        try:
            rule = self.rule_service.get(config.rule_router_id)
        except Exception as exc:
            raise HybridRouterError("hybrid_rule_not_found", "Selected Rule Router was not found") from exc
        if rule.family != "rule_based":
            raise HybridRouterError("hybrid_unsupported_rule_router", "Hybrid requires a rule_based child Router")
        try:
            self.fallback_executor.get(fallback_router_id, require_available=False)
        except FallbackRouterError as exc:
            raise HybridRouterError(exc.code, str(exc)) from exc

    @staticmethod
    def _fallback_triggers(response: RouteResponse | None, config: HybridConfig) -> list[str]:
        if response is None:
            return ["rule_error"]
        decision = response.decision
        triggers: list[str] = []
        if config.fallback_on_low_confidence and decision.confidence < config.rule_confidence_threshold:
            triggers.append("low_confidence")
        if config.fallback_on_unknown_subject and decision.primary_subject == "unknown":
            triggers.append("unknown_subject")
        if config.fallback_on_need_clarification and (decision.need_clarification or decision.target_slm == "ask_clarification"):
            triggers.append("need_clarification")
        return triggers

    def _build_response(self, config, fallback_router_id, rule_response, fallback_response, selected_source, fallback_triggers, fallback_error_code, started):
        total_latency = round((time.perf_counter() - started) * 1000, 2)
        rule_runtime = rule_response.runtime if rule_response else None
        fallback_runtime = fallback_response.runtime if fallback_response else None
        fallback_service = self.fallback_executor.services.get(fallback_router_id)
        fallback_family = getattr(fallback_service, "family", None)
        hybrid_runtime = HybridRuntime(
            rule_router_id=config.rule_router_id,
            fallback_router_id=fallback_router_id,
            fallback_family=fallback_family,
            rule_called=rule_response is not None,
            fallback_called=fallback_response is not None or selected_source == "rule_after_fallback_failure",
            selected_source=selected_source,
            fallback_triggers=fallback_triggers,
            primary_fallback_trigger=fallback_triggers[0] if fallback_triggers else None,
            rule_confidence=rule_response.decision.confidence if rule_response else None,
            rule_latency_ms=rule_runtime.latency_ms if rule_runtime else 0.0,
            fallback_latency_ms=fallback_runtime.latency_ms if fallback_runtime else 0.0,
            total_latency_ms=total_latency,
            degraded_mode=selected_source == "rule_after_fallback_failure",
            fallback_error_code=fallback_error_code if selected_source == "rule_after_fallback_failure" else None,
            config_snapshot=config,
            rule_decision=rule_response.decision if rule_response else None,
            fallback_decision=fallback_response.decision if fallback_response else None,
            llm_router_id=fallback_router_id if fallback_family == "openrouter_llm" else None,
            llm_called=fallback_response is not None or selected_source == "rule_after_fallback_failure",
            llm_latency_ms=fallback_runtime.latency_ms if fallback_runtime and fallback_family == "openrouter_llm" else 0.0,
            llm_error_code=fallback_error_code if fallback_family == "openrouter_llm" and selected_source == "rule_after_fallback_failure" else None,
            llm_decision=fallback_response.decision if fallback_response and fallback_family == "openrouter_llm" else None,
        )
        selected = fallback_response or rule_response
        if selected is None:
            raise HybridRouterError("hybrid_both_failed", "Both selected Rule and fallback Routers failed")
        runtime = RouterRuntime(
            router_type=self.ID,
            source=selected_source,
            latency_ms=total_latency,
            input_tokens=fallback_runtime.input_tokens if fallback_runtime else 0,
            output_tokens=fallback_runtime.output_tokens if fallback_runtime else 0,
            total_tokens=fallback_runtime.total_tokens if fallback_runtime else 0,
            cost=fallback_runtime.cost if fallback_runtime else None,
            parse_success=selected.runtime.parse_success,
            schema_success=selected.runtime.schema_success,
            model=selected.runtime.model,
            requested_model=selected.runtime.requested_model,
            resolved_model=selected.runtime.resolved_model,
            provider=selected.runtime.provider,
            prompt_version=selected.runtime.prompt_version,
            structured_output_mode=selected.runtime.structured_output_mode,
            retry_count=selected.runtime.retry_count,
            attempt_count=selected.runtime.attempt_count,
            retry_reason=selected.runtime.retry_reason,
            finish_reason=selected.runtime.finish_reason,
            hybrid=hybrid_runtime,
        )
        return RouteResponse(router_id=self.ID, router_name=self.NAME, decision=selected.decision, runtime=runtime)
