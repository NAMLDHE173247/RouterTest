import os
import time
from datetime import datetime, timezone
from typing import Optional

class SettingsStore:
    QWEN_HEALTH_TTL_SECONDS = 20
    _qwen_url: str = None
    _qwen_health: Optional[bool] = None
    _qwen_health_details: dict = {}
    _openrouter_api_key: Optional[str] = None
    _openrouter_status: Optional[str] = None
    _openrouter_error_message: Optional[str] = None
    _openrouter_checked_at: Optional[str] = None
    
    @classmethod
    def get_qwen_url(cls) -> str:
        """
        Lấy URL cho Qwen GPU Service.
        Ưu tiên: 
        1. URL do người dùng thiết lập qua UI (runtime).
        2. Biến môi trường QWEN_ROUTER_SERVICE_URL.
        """
        if cls._qwen_url:
            return cls._qwen_url
            
        env_url = os.environ.get("QWEN_ROUTER_SERVICE_URL", "")
        if env_url:
            return env_url.rstrip('/')
            
        return ""
        
    @classmethod
    def set_qwen_url(cls, url: str):
        """Lưu trữ cấu hình URL runtime."""
        cls._qwen_health = None
        cls._qwen_health_details = {}
        if url:
            cls._qwen_url = url.rstrip('/')
        else:
            cls._qwen_url = None

    @classmethod
    def get_qwen_health(cls) -> Optional[bool]:
        checked_at = cls._qwen_health_details.get("checked_at_epoch")
        if checked_at is None or time.time() - checked_at > cls.QWEN_HEALTH_TTL_SECONDS:
            return None
        return cls._qwen_health

    @classmethod
    def set_qwen_health(cls, is_healthy: bool):
        cls._qwen_health = is_healthy
        cls._qwen_health_details = {
            "model_loaded": True if is_healthy else None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checked_at_epoch": time.time(),
        }

    @classmethod
    def set_qwen_health_details(cls, details: dict) -> None:
        cls._qwen_health_details = {
            **details,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checked_at_epoch": time.time(),
        }
        cls._qwen_health = bool(details.get("model_loaded") is True)

    @classmethod
    def get_qwen_health_details(cls) -> dict:
        return {key: value for key, value in cls._qwen_health_details.items() if key != "checked_at_epoch"}

    @classmethod
    def get_qwen_unavailable_reason(cls) -> str:
        if not cls.get_qwen_url():
            return "qwen_service_not_configured"
        details = cls._qwen_health_details
        if cls.get_qwen_health() is None:
            return "qwen_service_unreachable"
        if details.get("model_loaded") is False:
            return "qwen_model_not_loaded"
        return "qwen_service_unreachable"

    @classmethod
    def get_openrouter_api_key(cls) -> str:
        """Return the runtime key, falling back to the environment key."""
        return cls._openrouter_api_key or os.environ.get("OPENROUTER_API_KEY", "")

    @classmethod
    def get_openrouter_source(cls) -> Optional[str]:
        if cls._openrouter_api_key:
            return "runtime"
        if os.environ.get("OPENROUTER_API_KEY", ""):
            return "environment"
        return None

    @classmethod
    def set_openrouter_api_key(cls, api_key: str) -> None:
        cls._openrouter_api_key = api_key.strip() or None
        cls._openrouter_status = None
        cls._openrouter_error_message = None
        cls._openrouter_checked_at = None

    @classmethod
    def clear_openrouter_runtime_key(cls) -> None:
        cls._openrouter_api_key = None
        cls._openrouter_status = None
        cls._openrouter_error_message = None
        cls._openrouter_checked_at = None

    @classmethod
    def get_openrouter_status(cls) -> Optional[str]:
        return cls._openrouter_status

    @classmethod
    def set_openrouter_status(cls, status: Optional[str]) -> None:
        cls._openrouter_status = status

    @classmethod
    def get_openrouter_error_message(cls) -> Optional[str]:
        return cls._openrouter_error_message

    @classmethod
    def get_openrouter_checked_at(cls) -> Optional[str]:
        return cls._openrouter_checked_at

    @classmethod
    def set_openrouter_connection_result(cls, status: str, message: Optional[str] = None) -> None:
        cls._openrouter_status = status
        cls._openrouter_error_message = None if status == "verified" else message
        cls._openrouter_checked_at = datetime.now(timezone.utc).isoformat()
