import json
import time
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.llm_router_prompt import (
    MAX_OUTPUT_TOKENS,
    MODEL_CONFIGS,
    PROMPT_VERSION,
    TEMPERATURE,
    build_messages,
    json_schema_format,
)
from app.openrouter_service_client import OpenRouterServiceClient, OpenRouterServiceError
from app.schemas.routing import RouteResponse, RouterDecision, RouterRuntime
from app.settings_store import SettingsStore


class LLMDecisionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_subject: Literal["math", "physics", "chemistry", "unknown"]
    secondary_subjects: List[Literal["math", "physics", "chemistry"]] = Field(default_factory=list)
    intent: Literal[
        "solve_problem", "explain_concept", "give_hint", "check_answer",
        "diagnose_error", "ask_follow_up", "unknown",
    ]
    target_slm: Literal["math_slm", "physics_slm", "chemistry_slm", "general_tutor", "ask_clarification"]
    confidence: float = Field(ge=0, le=1)
    need_clarification: bool
    reason: str = Field(min_length=1)

    @field_validator("secondary_subjects")
    @classmethod
    def validate_secondary_subjects(cls, values, info):
        if len(values) != len(set(values)):
            raise ValueError("secondary_subjects must not contain duplicates")
        primary = info.data.get("primary_subject")
        if primary and primary != "unknown" and primary in values:
            raise ValueError("secondary_subjects must not contain primary_subject")
        return values


class LLMRouterV0Adapter:
    FAMILY = "openrouter_llm"
    VERSION = "v0"

    def __init__(self, router_id: str, client: OpenRouterServiceClient | None = None):
        if router_id not in MODEL_CONFIGS:
            raise ValueError(f"Unknown LLM Router ID: {router_id}")
        self.id = router_id
        self.ID = router_id
        self.NAME = MODEL_CONFIGS[router_id]["name"]
        self.model = MODEL_CONFIGS[router_id]["model"]
        self.client = client or OpenRouterServiceClient()

    def route(self, question: str, history: List[str] | None = None) -> RouteResponse:
        api_key = SettingsStore.get_openrouter_api_key()
        if not api_key:
            raise OpenRouterServiceError("openrouter_not_configured", "OpenRouter API key is not configured")

        started = time.perf_counter()
        retry_count = 0
        output_mode = "json_schema"
        last_error: Exception | None = None
        retry_reason = None

        for attempt in range(2):
            retry_count = attempt
            try:
                response = self._request(api_key, question, history or [], output_mode)
                raw_content = self._extract_content(response)
                decision_data = self._parse_json(raw_content)
                decision_model = LLMDecisionModel.model_validate(decision_data)
                return self._build_response(
                    decision_model,
                    response,
                    started,
                    output_mode,
                    retry_count,
                    retry_reason,
                )
            except ValidationError as exc:
                last_error = OpenRouterServiceError(
                    "openrouter_schema_validation_failed",
                    "OpenRouter response failed RouterDecision validation",
                )
                retry_reason = "schema_validation_failed"
                output_mode = "json_object"
            except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                last_error = OpenRouterServiceError(
                    "openrouter_invalid_response",
                    "OpenRouter response did not contain a valid RouterDecision JSON object",
                )
                retry_reason = "invalid_json"
                output_mode = "json_object"
            except OpenRouterServiceError as exc:
                last_error = exc
                if not self._can_retry(exc, output_mode):
                    raise
                retry_reason = exc.code
                output_mode = "json_object" if exc.status_code == 400 else output_mode

        if last_error:
            raise last_error
        raise OpenRouterServiceError("openrouter_invalid_response", "OpenRouter returned no usable response")

    def _request(self, api_key: str, question: str, history: List[str], output_mode: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": build_messages(question, history),
            "temperature": TEMPERATURE,
            "stream": False,
            "max_tokens": MAX_OUTPUT_TOKENS,
        }
        if output_mode == "json_schema":
            payload["response_format"] = json_schema_format()
        else:
            payload["response_format"] = {"type": "json_object"}
        return self.client.chat_completion(api_key, payload)

    @staticmethod
    def _extract_content(response: Dict[str, Any]) -> str:
        choices = response.get("choices") or []
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Missing assistant content")
        return content.strip()

    @staticmethod
    def _parse_json(content: str) -> Dict[str, Any]:
        if content.startswith("```"):
            lines = content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise TypeError("Router output must be a JSON object")
        return parsed

    def _build_response(
        self,
        decision_model: LLMDecisionModel,
        response: Dict[str, Any],
        started: float,
        output_mode: str,
        retry_count: int,
        retry_reason: str | None,
    ) -> RouteResponse:
        usage = response.get("usage") or {}
        runtime = RouterRuntime(
            router_type=self.id,
            source="OpenRouter",
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cost=usage.get("cost"),
            parse_success=True,
            schema_success=True,
            model=response.get("model", self.model),
            requested_model=self.model,
            resolved_model=response.get("model", self.model),
            provider="OpenRouter",
            prompt_version=PROMPT_VERSION,
            structured_output_mode=output_mode,
            retry_count=retry_count,
            attempt_count=retry_count + 1,
            retry_reason=retry_reason,
            finish_reason=(response.get("choices") or [{}])[0].get("finish_reason"),
        )
        return RouteResponse(
            router_id=self.id,
            router_name=self.NAME,
            decision=RouterDecision(**decision_model.model_dump()),
            runtime=runtime,
        )

    @staticmethod
    def _can_retry(error: OpenRouterServiceError, output_mode: str) -> bool:
        if error.code in {
            "openrouter_not_configured", "openrouter_invalid_key", "openrouter_forbidden",
            "openrouter_insufficient_credit", "openrouter_model_unavailable",
            "openrouter_context_length_exceeded",
        }:
            return False
        return output_mode == "json_schema" or error.code in {"openrouter_timeout", "openrouter_upstream_error"}
