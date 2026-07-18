import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.adapters.llm_router_v0_adapter import LLMRouterV0Adapter
from app.llm_router_prompt import MODEL_CONFIGS
from app.openrouter_service_client import OpenRouterServiceError
from app.settings_store import SettingsStore


class FakeOpenRouterClient:
    timeout = 60

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.payloads = []

    def chat_completion(self, api_key, payload):
        self.payloads.append(payload)
        if self.error:
            raise self.error
        return self.response


@pytest.fixture(autouse=True)
def clear_runtime_key(monkeypatch):
    SettingsStore.clear_openrouter_runtime_key()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    yield
    SettingsStore.clear_openrouter_runtime_key()


def test_three_router_ids_have_expected_models():
    assert MODEL_CONFIGS["llm_deepseek_v0"]["model"] == "deepseek/deepseek-chat"
    assert MODEL_CONFIGS["llm_gemini_v0"]["model"] == "google/gemini-2.0-flash-001"
    assert MODEL_CONFIGS["llm_openai_v0"]["model"] == "openai/gpt-4o-mini"


def test_runtime_key_precedes_environment_and_delete_falls_back(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "environment-key")
    SettingsStore.set_openrouter_api_key("runtime-key")
    assert SettingsStore.get_openrouter_api_key() == "runtime-key"
    assert SettingsStore.get_openrouter_source() == "runtime"

    SettingsStore.clear_openrouter_runtime_key()
    assert SettingsStore.get_openrouter_api_key() == "environment-key"
    assert SettingsStore.get_openrouter_source() == "environment"


def test_route_validates_decision_and_records_runtime_metadata():
    SettingsStore.set_openrouter_api_key("runtime-key")
    client = FakeOpenRouterClient({
        "model": "deepseek/deepseek-chat",
        "choices": [{
            "message": {"content": '{"primary_subject":"physics","secondary_subjects":["math"],"intent":"solve_problem","target_slm":"physics_slm","confidence":0.9,"need_clarification":false,"reason":"The question is about motion."}'},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    })

    response = LLMRouterV0Adapter("llm_deepseek_v0", client).route("A falling object", [])

    assert response.router_id == "llm_deepseek_v0"
    assert response.decision.primary_subject == "physics"
    assert response.runtime.structured_output_mode == "json_schema"
    assert response.runtime.total_tokens == 30
    assert client.payloads[0]["temperature"] == 0


def test_invalid_schema_does_not_get_silently_repaired():
    SettingsStore.set_openrouter_api_key("runtime-key")
    client = FakeOpenRouterClient({
        "choices": [{"message": {"content": '{"primary_subject":"geometry"}'}}]
    })

    with pytest.raises(OpenRouterServiceError) as error:
        LLMRouterV0Adapter("llm_deepseek_v0", client).route("question", [])

    assert error.value.code == "openrouter_schema_validation_failed"
    assert len(client.payloads) == 2
