"""Registry and orchestration for Rule-based Router versions."""

from typing import Dict, Iterable

from app.schemas.routing import RouteResponse
from app.services.routing.base import RouterVersionService
from app.services.routing.version_services import (
    RuleV0Service,
    RuleV1Service,
    RuleV2Service,
    RuleV3Service,
)


class RuleBasedRouterService:
    """Owns registration and dispatch of all Rule-based versions."""

    def __init__(self, services: Iterable[RouterVersionService] | None = None):
        self.services: Dict[str, RouterVersionService] = {}
        for service in services or (
            RuleV0Service(),
            RuleV1Service(),
            RuleV2Service(),
            RuleV3Service(),
        ):
            self.register(service)

    def register(self, service: RouterVersionService) -> None:
        if service.family != "rule_based":
            raise ValueError(f"Invalid Rule-based service family: {service.family}")
        if service.router_id in self.services:
            raise ValueError(f"Duplicate router ID: {service.router_id}")
        self.services[service.router_id] = service

    def get(self, router_id: str) -> RouterVersionService:
        try:
            return self.services[router_id]
        except KeyError as exc:
            raise ValueError(f"Rule-based router not found: {router_id}") from exc

    def route(self, router_id: str, question: str, history: list[str] | None = None) -> RouteResponse:
        return self.get(router_id).route(question, history)

    def compare(self, router_ids: list[str], question: str, history: list[str] | None = None):
        return [(router_id, self.get(router_id).route(question, history)) for router_id in router_ids]

    def get_available_routers(self) -> list[dict]:
        return [service.get_metadata() for service in self.services.values()]
