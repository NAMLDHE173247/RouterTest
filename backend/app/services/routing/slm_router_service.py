"""Registry and orchestration for SLM router versions."""

from typing import Dict, Iterable

from app.schemas.routing import RouteResponse
from app.services.routing.base import RouterVersionService
from app.services.routing.version_services import QwenV0Service


class SLMRouterService:
    """Owns registration and dispatch of external SLM-backed routers."""

    def __init__(self, services: Iterable[RouterVersionService] | None = None):
        self.services: Dict[str, RouterVersionService] = {}
        for service in services or (QwenV0Service(),):
            self.register(service)

    def register(self, service: RouterVersionService) -> None:
        if service.family != "slm":
            raise ValueError(f"Invalid SLM service family: {service.family}")
        if service.router_id in self.services:
            raise ValueError(f"Duplicate router ID: {service.router_id}")
        self.services[service.router_id] = service

    def get(self, router_id: str) -> RouterVersionService:
        try:
            return self.services[router_id]
        except KeyError as exc:
            raise ValueError(f"SLM router not found: {router_id}") from exc

    def route(self, router_id: str, question: str, history: list[str] | None = None) -> RouteResponse:
        return self.get(router_id).route(question, history)

    def get_available_routers(self) -> list[dict]:
        return [service.get_metadata() for service in self.services.values()]
