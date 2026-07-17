"""High-level routing facade."""

from app.schemas.routing import RouteRequest, RouteResponse
from app.services.routing.rule_based_router_service import RuleBasedRouterService
from app.services.routing.slm_router_service import SLMRouterService
from app.services.routing.version_services import HybridV0Service


class RoutingService:
    """Dispatches requests by router family without owning version logic."""

    def __init__(self):
        self.rule_based = RuleBasedRouterService()
        self.slm = SLMRouterService()
        self.hybrid = HybridV0Service()
        self.services = {
            **self.rule_based.services,
            **self.slm.services,
            self.hybrid.router_id: self.hybrid,
        }

    @property
    def adapters(self):
        """Compatibility-only view for legacy integrations."""
        return {router_id: service.adapter for router_id, service in self.services.items()}

    def get_available_routers(self):
        return (
            self.rule_based.get_available_routers()
            + self.slm.get_available_routers()
            + [self.hybrid.get_metadata()]
        )

    def get_available_router_ids(self):
        return list(self.services)

    def has_router(self, router_id: str) -> bool:
        return router_id in self.services

    def get_service(self, router_id: str):
        try:
            return self.services[router_id]
        except KeyError as exc:
            raise ValueError(f"Router {router_id} not found") from exc

    def _get_service(self, router_id: str):
        """Backward-compatible alias; new code should use ``get_service``."""
        return self.get_service(router_id)

    def route(self, req: RouteRequest) -> RouteResponse:
        return self.get_service(req.router_id).route(req.question, req.history)

    def compare_routers(self, router_ids: list[str], question: str, history: list[str] | None = None):
        results = []
        for router_id in router_ids:
            try:
                results.append({
                    "router_id": router_id,
                    "response": self.get_service(router_id).route(question, history),
                })
            except NotImplementedError as exc:
                results.append({"router_id": router_id, "error": str(exc)})
            except Exception as exc:
                results.append({"router_id": router_id, "error": str(exc)})
        return results


routing_service = RoutingService()
