"""Registry for the independent OpenRouter-backed LLM Router V0 variants."""

from typing import Dict, Iterable

from app.adapters.llm_router_v0_adapter import LLMRouterV0Adapter
from app.services.routing.base import RouterVersionService
from app.settings_store import SettingsStore


LLM_ROUTER_IDS = (
    "llm_deepseek_v0",
    "llm_gemini_v0",
    "llm_openai_v0",
)


class LLMRouterV0Service(RouterVersionService):
    def __init__(self, router_id: str):
        self.adapter = LLMRouterV0Adapter(router_id)
        self.router_id = self.adapter.ID
        self.router_name = self.adapter.NAME
        self.family = "openrouter_llm"
        self.version = "v0"
        self.model = self.adapter.model
        self.capabilities = {
            **self.capabilities,
            "requires_external_service": True,
            "supports_structured_output": True,
            "can_be_hybrid_fallback": True,
        }

    def route(self, question: str, history: list[str] | None = None):
        return self.adapter.route(question=question, history=history or [])

    def is_available(self) -> bool:
        return bool(SettingsStore.get_openrouter_api_key())

    def get_metadata(self):
        metadata = super().get_metadata()
        metadata.update({
            "model": self.model,
            "available": self.is_available(),
            "unavailable_reason": None if self.is_available() else "openrouter_not_configured",
        })
        return metadata


class OpenRouterLLMRouterService:
    def __init__(self, services: Iterable[RouterVersionService] | None = None):
        self.services: Dict[str, RouterVersionService] = {}
        for service in services or (LLMRouterV0Service(router_id) for router_id in LLM_ROUTER_IDS):
            self.register(service)

    def register(self, service: RouterVersionService) -> None:
        if service.family != "openrouter_llm":
            raise ValueError(f"Invalid OpenRouter LLM service family: {service.family}")
        if service.router_id in self.services:
            raise ValueError(f"Duplicate router ID: {service.router_id}")
        self.services[service.router_id] = service

    def get(self, router_id: str) -> RouterVersionService:
        try:
            return self.services[router_id]
        except KeyError as exc:
            raise ValueError(f"OpenRouter LLM router not found: {router_id}") from exc

    def get_available_routers(self) -> list[dict]:
        return [service.get_metadata() for service in self.services.values()]
