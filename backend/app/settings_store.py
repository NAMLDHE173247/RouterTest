import os
from typing import Optional

class SettingsStore:
    _qwen_url: str = None
    _qwen_health: Optional[bool] = None
    _openrouter_api_key: Optional[str] = None
    _openrouter_status: Optional[str] = None
    
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
        if url:
            cls._qwen_url = url.rstrip('/')
        else:
            cls._qwen_url = None

    @classmethod
    def get_qwen_health(cls) -> Optional[bool]:
        return cls._qwen_health

    @classmethod
    def set_qwen_health(cls, is_healthy: bool):
        cls._qwen_health = is_healthy

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

    @classmethod
    def clear_openrouter_runtime_key(cls) -> None:
        cls._openrouter_api_key = None
        cls._openrouter_status = None

    @classmethod
    def get_openrouter_status(cls) -> Optional[str]:
        return cls._openrouter_status

    @classmethod
    def set_openrouter_status(cls, status: Optional[str]) -> None:
        cls._openrouter_status = status
