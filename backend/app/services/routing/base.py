"""Common interface for versioned router services."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.schemas.routing import RouteResponse


class RouterVersionService(ABC):
    """Application service for one concrete router version."""

    router_id: str
    router_name: str
    family: str
    version: str

    @abstractmethod
    def route(self, question: str, history: list[str] | None = None) -> RouteResponse:
        """Route one request through the version-specific adapter."""

    def get_version(self) -> str:
        return self.version

    def get_family(self) -> str:
        return self.family

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "id": self.router_id,
            "name": self.router_name,
            "family": self.family,
            "version": self.version,
            "status": "ready" if self.is_available() else "unavailable",
            "capabilities": {
                "supports_history": True,
                "supports_debug_trace": False,
                "requires_external_service": False,
            },
        }

    def is_available(self) -> bool:
        return True
