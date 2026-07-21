"""Dispatches Hybrid fallback requests without coupling Hybrid to a family."""

from app.schemas.routing import RouteResponse


class FallbackRouterError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class FallbackRouterExecutor:
    def __init__(self, services: dict[str, object]):
        self.services = services

    def get(self, router_id: str, require_available: bool = True):
        service = self.services.get(router_id)
        if service is None:
            raise FallbackRouterError("hybrid_fallback_not_found", "Selected fallback Router was not found")
        if service.router_id == "hybrid":
            raise FallbackRouterError("hybrid_invalid_config", "Hybrid cannot use itself as a fallback Router")
        if not service.capabilities.get("can_be_hybrid_fallback", False):
            raise FallbackRouterError("hybrid_unsupported_fallback_router", "Selected Router cannot be used as a Hybrid fallback")
        if require_available and not service.is_available():
            reason = service.get_metadata().get("unavailable_reason") or "hybrid_fallback_unavailable"
            raise FallbackRouterError(reason, "Selected fallback Router is unavailable")
        return service

    def execute(self, router_id: str, question: str, history: list[str]) -> RouteResponse:
        service = self.get(router_id)
        try:
            return service.route(question, history)
        except FallbackRouterError:
            raise
        except Exception as exc:
            code = "hybrid_qwen_service_unavailable" if getattr(service, "family", "") == "slm" else getattr(exc, "code", "hybrid_fallback_failed")
            raise FallbackRouterError(code, "Selected fallback Router failed") from exc
