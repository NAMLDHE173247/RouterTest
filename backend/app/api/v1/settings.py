from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.settings_store import SettingsStore
from app.qwen_service_client import QwenServiceClient, QwenServiceClientError
from app.openrouter_service_client import OpenRouterServiceClient, OpenRouterServiceError

router = APIRouter()
qwen_client = QwenServiceClient()
openrouter_client = OpenRouterServiceClient()

class QwenUrlRequest(BaseModel):
    url: str


class OpenRouterApiKeyRequest(BaseModel):
    api_key: str = Field(min_length=1)

@router.get("/qwen-service")
def get_qwen_url():
    return {"url": SettingsStore.get_qwen_url()}


@router.get("/qwen-service/status")
def get_qwen_status():
    url = SettingsStore.get_qwen_url()
    details = SettingsStore.get_qwen_health_details()
    health = SettingsStore.get_qwen_health()
    if not url:
        connection_status = "not_configured"
    elif health is True:
        connection_status = "connected"
    elif details.get("model_loaded") is True:
        connection_status = "stale"
    elif details.get("model_loaded") is False:
        connection_status = "model_not_loaded"
    elif details:
        connection_status = "unreachable"
    else:
        connection_status = "not_tested"
    return {
        "configured": bool(url),
        "connection_status": connection_status,
        "model_loaded": details.get("model_loaded"),
        "model_name": details.get("model_name"),
        "device": details.get("device"),
        "startup_error": details.get("startup_error"),
        "checked_at": details.get("checked_at"),
        "service_version": details.get("service_version"),
    }

@router.post("/qwen-service")
def set_qwen_url(req: QwenUrlRequest):
    SettingsStore.set_qwen_url(req.url)
    return {"status": "success", "url": SettingsStore.get_qwen_url()}

@router.post("/qwen-service/test")
def test_qwen_connection():
    try:
        res = qwen_client.health_check()
        SettingsStore.set_qwen_health_details(res)
        return res
    except QwenServiceClientError as e:
        SettingsStore.set_qwen_health(False)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        SettingsStore.set_qwen_health(False)
        raise HTTPException(status_code=500, detail=str(e))


def _openrouter_status(connection_status: str | None = None):
    api_key = SettingsStore.get_openrouter_api_key()
    stored_status = SettingsStore.get_openrouter_status()
    return {
        "configured": bool(api_key),
        "source": SettingsStore.get_openrouter_source(),
        "connection_status": connection_status or stored_status or ("configured" if api_key else "not_configured"),
        "error_code": stored_status if stored_status and stored_status.startswith("openrouter_") else None,
        "error_message": SettingsStore.get_openrouter_error_message(),
        "last_checked_at": SettingsStore.get_openrouter_checked_at(),
    }


@router.get("/openrouter/status")
def get_openrouter_status():
    return _openrouter_status()


@router.post("/openrouter/verify")
def verify_openrouter_key(req: OpenRouterApiKeyRequest):
    try:
        openrouter_client.verify_key(req.api_key)
        SettingsStore.set_openrouter_connection_result("verified")
        return {"configured": False, "source": None, "connection_status": "verified"}
    except OpenRouterServiceError as exc:
        SettingsStore.set_openrouter_connection_result(exc.code, str(exc))
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)})


@router.post("/openrouter")
def set_openrouter_key(req: OpenRouterApiKeyRequest):
    try:
        openrouter_client.verify_key(req.api_key)
        SettingsStore.set_openrouter_api_key(req.api_key)
        SettingsStore.set_openrouter_connection_result("verified")
        return _openrouter_status("verified")
    except OpenRouterServiceError as exc:
        SettingsStore.set_openrouter_connection_result(exc.code, str(exc))
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)})


@router.delete("/openrouter")
def delete_openrouter_runtime_key():
    SettingsStore.clear_openrouter_runtime_key()
    return _openrouter_status("environment_fallback" if SettingsStore.get_openrouter_api_key() else "runtime_key_deleted")
