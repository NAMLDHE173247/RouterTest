import os

class SettingsStore:
    _qwen_url: str = None
    
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
        if url:
            cls._qwen_url = url.rstrip('/')
        else:
            cls._qwen_url = None
