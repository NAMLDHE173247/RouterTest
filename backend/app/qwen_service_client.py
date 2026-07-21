import os
import requests
import time
from typing import Dict, Any, List

from .settings_store import SettingsStore

class QwenServiceClientError(Exception):
    """Exception throw when Qwen GPU Service is offline or fails."""
    pass

class QwenServiceClient:
    def __init__(self):
        # Đọc cấu hình timeout từ ENV, mặc định 120 giây
        self.timeout = int(os.environ.get("QWEN_ROUTER_TIMEOUT_SECONDS", 120))
        
    def _get_url(self) -> str:
        url = SettingsStore.get_qwen_url()
        if not url:
            raise QwenServiceClientError("QWEN_ROUTER_SERVICE_URL chưa được cấu hình. Vui lòng thiết lập trên giao diện.")
        return url
        
    def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra sức khoẻ của GPU Service.
        Ưu tiên gọi /model/status để kiểm tra model state.
        """
        base_url = self._get_url().rstrip('/')
        last_err = None
        
        for attempt in range(2):
            try:
                # 1. Ưu tiên gọi /model/status
                url_model_status = f"{base_url}/model/status"
                try:
                    resp_status = requests.get(url_model_status, timeout=10)
                    # Chấp nhận cả 200 và 503 (nếu backend trả 503 kèm json model_loaded)
                    if resp_status.status_code in (200, 503):
                        data = resp_status.json()
                        if "model_loaded" in data:
                            # Normalize model_loaded to explicit boolean
                            is_loaded = data.get("model_loaded") in (True, "true", "True", 1)
                            return {
                                "model_loaded": is_loaded,
                                "model_name": data.get("model_name"),
                                "startup_error": data.get("startup_error"),
                                "device": data.get("device"),
                                "status": data.get("status", "healthy"),
                                "service_version": data.get("version") or data.get("service_version"),
                            }
                except Exception:
                    pass # Chuyển sang fallback nếu request gặp sự cố (ví dụ connection error)
                
                # 2. Fallback gọi /health
                url_health = f"{base_url}/health"
                resp_health = requests.get(url_health, timeout=10)
                resp_health.raise_for_status()
                data = resp_health.json()
                
                # Cố thử lấy /model/status lần nữa nếu data không chứa model_loaded
                if "model_loaded" not in data and data.get("status") == "healthy":
                    try:
                        ms_resp = requests.get(url_model_status, timeout=10)
                        if ms_resp.status_code in (200, 503):
                            ms_data = ms_resp.json()
                            if "model_loaded" in ms_data:
                                data["model_loaded"] = ms_data.get("model_loaded") in (True, "true", "True", 1)
                                data["model_name"] = ms_data.get("model_name")
                                data["startup_error"] = ms_data.get("startup_error")
                        data["device"] = ms_data.get("device")
                        data["service_version"] = ms_data.get("version") or ms_data.get("service_version")
                    except Exception:
                        pass
                
                return data
            except requests.RequestException as e:
                last_err = e
                time.sleep(1) # Chờ 1s trước khi retry
                
        raise QwenServiceClientError(f"Không thể kết nối đến Qwen Service tại {base_url}. Lỗi: {str(last_err)}")
            
    def route_question(self, question: str, history: List[str] = None) -> Dict[str, Any]:
        """
        Gọi endpoint /route để lấy kết quả phân luồng.
        """
        url = f"{self._get_url()}/route"
        payload = {
            "question": question,
            "history": history or [],
            "max_retries": 2
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            
            # Xử lý riêng HTTP 503 (Model Not Loaded)
            if resp.status_code == 503:
                err_detail = resp.json().get("detail", "Service is running but model is not loaded.")
                raise QwenServiceClientError(f"Qwen Service báo lỗi 503: {err_detail}")
                
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise QwenServiceClientError(f"Yêu cầu tới Qwen Service đã bị Timeout sau {self.timeout} giây.")
        except requests.RequestException as e:
            if resp is not None and hasattr(resp, "text"):
                raise QwenServiceClientError(f"Lỗi khi gọi Qwen Service: HTTP {resp.status_code} - {resp.text}")
            raise QwenServiceClientError(f"Lỗi không xác định khi gọi Qwen Service: {str(e)}")
            
    def batch_route(self, questions: List[str]) -> Dict[str, Any]:
        """
        Gửi batch câu hỏi lên endpoint /batch-route.
        """
        url = f"{self._get_url()}/batch-route"
        payload = {
            "questions": questions,
            "history": [],
            "max_retries": 2
        }
        try:
            # Nhân timeout lên theo số lượng câu hỏi
            batch_timeout = self.timeout + (len(questions) * 10) 
            resp = requests.post(url, json=payload, timeout=batch_timeout)
            
            if resp.status_code == 503:
                raise QwenServiceClientError(f"Qwen Service báo lỗi 503: {resp.text}")
                
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise QwenServiceClientError("Yêu cầu Batch tới Qwen Service đã bị Timeout.")
        except Exception as e:
            raise QwenServiceClientError(f"Batch routing thất bại. Lỗi: {str(e)}")
