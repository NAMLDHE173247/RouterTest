from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class HealthResponse(BaseModel):
    status: str = "ok"
    available_routers: List[str] = []
