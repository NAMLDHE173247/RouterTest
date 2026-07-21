"""Version services that keep application logic separate from adapters."""

from app.adapters.qwen_v0_adapter import QwenV0Adapter
from app.adapters.rule_v0_adapter import RuleV0Adapter
from app.adapters.rule_v1_adapter import RuleV1Adapter
from app.adapters.rule_v2_adapter import RuleV2Adapter
from app.adapters.hybrid_v0_adapter import HybridV0Adapter
from app.schemas.routing import HybridConfig, RouteResponse
from app.settings_store import SettingsStore
from app.services.routing.base import RouterVersionService


class AdapterBackedRouterService(RouterVersionService):
    """Thin version service around an existing adapter."""

    def __init__(self, adapter: object, family: str, version: str):
        self.adapter = adapter
        self.router_id = adapter.ID
        self.router_name = adapter.NAME
        self.family = family
        self.version = version
        self.capabilities = dict(self.capabilities)

    def route(self, question: str, history: list[str] | None = None) -> RouteResponse:
        return self.adapter.route(question=question, history=history or [])


class RuleV0Service(AdapterBackedRouterService):
    def __init__(self):
        super().__init__(RuleV0Adapter(), "rule_based", "v0")


class RuleV1Service(AdapterBackedRouterService):
    def __init__(self):
        super().__init__(RuleV1Adapter(), "rule_based", "v1")


class RuleV2Service(AdapterBackedRouterService):
    def __init__(self):
        super().__init__(RuleV2Adapter(), "rule_based", "v2")


class RuleV3Service(AdapterBackedRouterService):
    """V3 Phase 0: compatibility baseline with V2 behavior."""

    def __init__(self):
        from app.adapters.rule_v3_adapter import RuleV3Adapter

        super().__init__(RuleV3Adapter(), "rule_based", "v3")


class QwenV0Service(AdapterBackedRouterService):
    def __init__(self):
        super().__init__(QwenV0Adapter(), "slm", "v0")
        self.capabilities["requires_external_service"] = True
        self.capabilities["can_be_hybrid_fallback"] = True

    def is_available(self) -> bool:
        """Use cached health state; listing routers must not make network calls."""
        return SettingsStore.get_qwen_health() is True

    def get_metadata(self):
        metadata = super().get_metadata()
        health = SettingsStore.get_qwen_health_details()
        metadata.update({
            "model": health.get("model_name") or "Qwen/Qwen2.5-7B-Instruct",
            "available": self.is_available(),
            "unavailable_reason": None if self.is_available() else SettingsStore.get_qwen_unavailable_reason(),
            "qwen_model_loaded": health.get("model_loaded"),
            "qwen_status_checked_at": health.get("checked_at"),
            "qwen_gpu_service_version": health.get("service_version"),
        })
        return metadata


class HybridV0Service(RouterVersionService):
    def __init__(self, rule_service, fallback_executor):
        self.adapter = HybridV0Adapter(rule_service, fallback_executor)
        self.router_id = self.adapter.ID
        self.router_name = self.adapter.NAME
        self.family = "hybrid"
        self.version = "v0"
        self.capabilities = {
            **self.capabilities,
            "requires_configuration": True,
            "supports_rule_first": True,
            "supports_fallback_router": True,
        }

    def route(
        self,
        question: str,
        history: list[str] | None = None,
        config: HybridConfig | None = None,
    ) -> RouteResponse:
        return self.adapter.route(question=question, history=history or [], config=config)

    def get_metadata(self):
        metadata = super().get_metadata()
        metadata.update({
            "available": True,
            "unavailable_reason": None,
            "description": "Rule-first Hybrid Router with configurable LLM fallback",
        })
        return metadata
