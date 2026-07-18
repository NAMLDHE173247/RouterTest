"""Rule-first/LLM-fallback decision policy for Hybrid Router V0."""

import time
from typing import Any, List

from app.schemas.routing import HybridConfig, HybridRuntime, RouteResponse, RouterRuntime


class HybridRouterError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class HybridV0Adapter:
    ID = "hybrid"
    NAME = "Hybrid Router V0"
    FAMILY = "hybrid"
    VERSION = "v0"

    def __init__(self, rule_service: Any, llm_service: Any):
        self.rule_service = rule_service
        self.llm_service = llm_service

    def route(
        self,
        question: str,
        history: List[str] | None = None,
        config: HybridConfig | None = None,
    ) -> RouteResponse:
        config = config or HybridConfig()
        self._validate_config(config)
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

        if rule_response is not None:
            triggers = self._fallback_triggers(rule_response, config)
        else:
            triggers = ["rule_error"]

        if not triggers:
            return self._build_response(
                config=config,
                selected=rule_response,
                rule_response=rule_response,
                llm_response=None,
                selected_source="rule",
                fallback_triggers=[],
                rule_error_code=None,
                started=started,
            )

        try:
            llm_response = self.llm_service.get(config.llm_router_id).route(question, history)
            return self._build_response(
                config=config,
                selected=llm_response,
                rule_response=rule_response,
                llm_response=llm_response,
                selected_source="llm",
                fallback_triggers=triggers,
                rule_error_code=rule_error_code,
                started=started,
            )
        except Exception as exc:
            error_code = getattr(exc, "code", "hybrid_llm_failed")
            if rule_response is not None and config.llm_failure_policy == "use_rule":
                return self._build_response(
                    config=config,
                    selected=rule_response,
                    rule_response=rule_response,
                    llm_response=None,
                    selected_source="rule_after_llm_failure",
                    fallback_triggers=triggers,
                    rule_error_code=error_code,
                    started=started,
                )
            raise HybridRouterError("hybrid_both_failed", "Both selected Rule and LLM Routers failed") from exc

    def _validate_config(self, config: HybridConfig) -> None:
        if config.rule_router_id == self.ID or config.llm_router_id == self.ID:
            raise HybridRouterError("hybrid_invalid_config", "Hybrid cannot use itself as a child Router")
        try:
            rule = self.rule_service.get(config.rule_router_id)
        except Exception as exc:
            raise HybridRouterError("hybrid_rule_not_found", "Selected Rule Router was not found") from exc
        try:
            llm = self.llm_service.get(config.llm_router_id)
        except Exception as exc:
            raise HybridRouterError("hybrid_llm_not_found", "Selected LLM Router was not found") from exc
        if rule.family != "rule_based":
            raise HybridRouterError("hybrid_unsupported_rule_router", "Hybrid requires a rule_based child Router")
        if llm.family != "openrouter_llm":
            raise HybridRouterError("hybrid_unsupported_llm_router", "Hybrid requires an openrouter_llm child Router")

    @staticmethod
    def _fallback_triggers(response: RouteResponse, config: HybridConfig) -> list[str]:
        decision = response.decision
        triggers: list[str] = []
        if config.fallback_on_low_confidence and decision.confidence < config.rule_confidence_threshold:
            triggers.append("low_confidence")
        if config.fallback_on_unknown_subject and decision.primary_subject == "unknown":
            triggers.append("unknown_subject")
        if config.fallback_on_need_clarification and (
            decision.need_clarification or decision.target_slm == "ask_clarification"
        ):
            triggers.append("need_clarification")
        return triggers

    def _build_response(
        self,
        config: HybridConfig,
        selected: RouteResponse,
        rule_response: RouteResponse | None,
        llm_response: RouteResponse | None,
        selected_source: str,
        fallback_triggers: list[str],
        rule_error_code: str | None,
        started: float,
    ) -> RouteResponse:
        total_latency = round((time.perf_counter() - started) * 1000, 2)
        rule_runtime = rule_response.runtime if rule_response else None
        llm_runtime = llm_response.runtime if llm_response else None
        llm_error_code = rule_error_code if selected_source == "rule_after_llm_failure" else None
        hybrid_runtime = HybridRuntime(
            rule_router_id=config.rule_router_id,
            llm_router_id=config.llm_router_id,
            rule_called=rule_response is not None,
            llm_called=llm_response is not None or selected_source == "rule_after_llm_failure",
            selected_source=selected_source,
            fallback_triggers=fallback_triggers,
            primary_fallback_trigger=fallback_triggers[0] if fallback_triggers else None,
            rule_confidence=rule_response.decision.confidence if rule_response else None,
            rule_latency_ms=rule_runtime.latency_ms if rule_runtime else 0.0,
            llm_latency_ms=llm_runtime.latency_ms if llm_runtime else 0.0,
            total_latency_ms=total_latency,
            degraded_mode=selected_source == "rule_after_llm_failure",
            llm_error_code=llm_error_code,
            config_snapshot=config,
            rule_decision=rule_response.decision if rule_response else None,
            llm_decision=llm_response.decision if llm_response else None,
        )
        runtime = RouterRuntime(
            router_type=self.ID,
            source=selected_source,
            latency_ms=total_latency,
            input_tokens=llm_runtime.input_tokens if llm_runtime else 0,
            output_tokens=llm_runtime.output_tokens if llm_runtime else 0,
            total_tokens=llm_runtime.total_tokens if llm_runtime else 0,
            cost=llm_runtime.cost if llm_runtime else None,
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
        return RouteResponse(
            router_id=self.ID,
            router_name=self.NAME,
            decision=selected.decision,
            runtime=runtime,
        )
