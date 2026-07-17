from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class RouterDecision(BaseModel):
    primary_subject: str
    secondary_subjects: List[str] = []
    intent: str
    target_slm: str
    confidence: float
    need_clarification: bool
    reason: str
    router_id: Optional[str] = None
    router_family: Optional[str] = None
    router_version: Optional[str] = None
    topic: Optional[str] = None
    reason_code: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None

class RouterRuntime(BaseModel):
    router_type: Optional[str] = None
    source: Optional[str] = None
    latency_ms: float
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    parse_success: bool = True
    model: Optional[str] = None

class RouteRequest(BaseModel):
    router_id: str
    question: str
    history: List[str] = []

class RouteResponse(BaseModel):
    router_id: str
    router_name: str
    decision: RouterDecision
    runtime: RouterRuntime

class RouterInfo(BaseModel):
    id: str
    name: str
    status: str
    family: Optional[str] = None
    version: Optional[str] = None
    capabilities: Optional[Dict[str, bool]] = None
    description: Optional[str] = None

class CompareRequest(BaseModel):
    router_ids: List[str] = ["rule_v0", "rule_v1", "rule_v2"]
    question: str
    history: List[str] = []

class CompareResult(BaseModel):
    router_id: str
    decision: Optional[RouterDecision] = None
    runtime: RouterRuntime

class CompareResponse(BaseModel):
    results: List[CompareResult]
