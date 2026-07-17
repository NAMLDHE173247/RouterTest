"""Version services that keep application logic separate from adapters."""

from app.adapters.qwen_v0_adapter import QwenV0Adapter
from app.adapters.rule_v0_adapter import RuleV0Adapter
from app.adapters.rule_v1_adapter import RuleV1Adapter
from app.adapters.rule_v2_adapter import RuleV2Adapter
from app.adapters.hybrid_v0_adapter import HybridV0Adapter
from app.schemas.routing import RouteResponse
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

    def is_available(self) -> bool:
        """Use cached health state; listing routers must not make network calls."""
        return SettingsStore.get_qwen_health() is True


class HybridV0Service(AdapterBackedRouterService):
    def __init__(self):
        super().__init__(HybridV0Adapter(), "hybrid", "v0")
