from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.settings_store import SettingsStore
from app.qwen_service_client import QwenServiceClient, QwenServiceClientError

router = APIRouter()
qwen_client = QwenServiceClient()

class QwenUrlRequest(BaseModel):
    url: str

@router.get("/qwen-service")
def get_qwen_url():
    return {"url": SettingsStore.get_qwen_url()}

@router.post("/qwen-service")
def set_qwen_url(req: QwenUrlRequest):
    SettingsStore.set_qwen_url(req.url)
    return {"status": "success", "url": SettingsStore.get_qwen_url()}

@router.post("/qwen-service/test")
def test_qwen_connection():
    try:
        res = qwen_client.health_check()
        SettingsStore.set_qwen_health(True)
        return res
    except QwenServiceClientError as e:
        SettingsStore.set_qwen_health(False)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        SettingsStore.set_qwen_health(False)
        raise HTTPException(status_code=500, detail=str(e))
