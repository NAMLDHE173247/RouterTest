"""Small OpenRouter HTTP client with no routing/business-prompt logic."""

import os
from typing import Any, Dict, Optional

import requests


class OpenRouterServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class OpenRouterServiceClient:
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or os.environ.get("OPENROUTER_BASE_URL", self.BASE_URL)).rstrip("/")
        self.timeout = timeout or int(os.environ.get("OPENROUTER_TIMEOUT_SECONDS", "60"))

    def _headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def verify_key(self, api_key: str) -> Dict[str, Any]:
        """Verify a key without creating a completion or storing the key."""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self._headers(api_key),
                timeout=min(self.timeout, 15),
            )
        except requests.Timeout as exc:
            raise OpenRouterServiceError("openrouter_timeout", "OpenRouter verification timed out") from exc
        except requests.RequestException as exc:
            raise OpenRouterServiceError("openrouter_unreachable", "Unable to connect to OpenRouter") from exc

        self._raise_for_status(response)
        try:
            return response.json() if response.content else {}
        except ValueError as exc:
            raise OpenRouterServiceError("openrouter_invalid_response", "OpenRouter returned invalid JSON") from exc

    def chat_completion(self, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(api_key),
                json=payload,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise OpenRouterServiceError("openrouter_timeout", "OpenRouter request timed out") from exc
        except requests.RequestException as exc:
            raise OpenRouterServiceError("openrouter_upstream_error", "Unable to connect to OpenRouter") from exc

        self._raise_for_status(response)
        try:
            return response.json()
        except ValueError as exc:
            raise OpenRouterServiceError("openrouter_invalid_response", "OpenRouter returned invalid JSON") from exc

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.ok:
            return

        code = {
            401: "openrouter_invalid_key",
            403: "openrouter_forbidden",
            402: "openrouter_insufficient_credit",
            429: "openrouter_rate_limited",
            404: "openrouter_model_unavailable",
        }.get(response.status_code, "openrouter_upstream_error")
        detail = "OpenRouter request failed"
        try:
            error = response.json().get("error", {})
            if isinstance(error, dict) and error.get("message"):
                detail = str(error["message"])
        except ValueError:
            pass
        if "context length" in detail.lower():
            code = "openrouter_context_length_exceeded"
        raise OpenRouterServiceError(code, detail, response.status_code)
