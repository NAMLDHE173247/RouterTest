from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional

class RouterDecision(BaseModel):
    primary_subject: str
    secondary_subjects: List[str] = Field(default_factory=list)
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


class HybridConfig(BaseModel):
    rule_router_id: str = "rule_v3"
    llm_router_id: str = "llm_gemini_v0"
    rule_confidence_threshold: float = Field(default=0.8, ge=0, le=1)
    fallback_on_low_confidence: bool = True
    fallback_on_unknown_subject: bool = True
    fallback_on_need_clarification: bool = True
    fallback_on_rule_error: bool = True
    llm_failure_policy: Literal["use_rule"] = "use_rule"


class HybridRuntime(BaseModel):
    hybrid_version: str = "v0"
    rule_router_id: str
    llm_router_id: str
    rule_called: bool = True
    llm_called: bool = False
    selected_source: Literal["rule", "llm", "rule_after_llm_failure"]
    fallback_triggers: List[str] = Field(default_factory=list)
    primary_fallback_trigger: Optional[str] = None
    rule_confidence: Optional[float] = None
    rule_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    degraded_mode: bool = False
    llm_error_code: Optional[str] = None
    config_snapshot: HybridConfig
    rule_decision: Optional[RouterDecision] = None
    llm_decision: Optional[RouterDecision] = None

class RouterRuntime(BaseModel):
    router_type: Optional[str] = None
    source: Optional[str] = None
    latency_ms: float
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    total_tokens: Optional[int] = 0
    cost: Optional[float] = None
    parse_success: bool = True
    schema_success: bool = True
    model: Optional[str] = None
    requested_model: Optional[str] = None
    resolved_model: Optional[str] = None
    provider: Optional[str] = None
    prompt_version: Optional[str] = None
    structured_output_mode: Optional[str] = None
    retry_count: int = 0
    attempt_count: int = 1
    retry_reason: Optional[str] = None
    finish_reason: Optional[str] = None
    hybrid: Optional[HybridRuntime] = None

class RouteRequest(BaseModel):
    router_id: str
    question: str
    history: List[str] = Field(default_factory=list)
    hybrid_config: Optional[HybridConfig] = None

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
    model: Optional[str] = None
    available: Optional[bool] = None
    unavailable_reason: Optional[str] = None

class CompareRequest(BaseModel):
    router_ids: List[str] = Field(default_factory=lambda: ["rule_v0", "rule_v1", "rule_v2"])
    question: str
    history: List[str] = Field(default_factory=list)
    hybrid_config: Optional[HybridConfig] = None

class CompareResult(BaseModel):
    router_id: str
    decision: Optional[RouterDecision] = None
    runtime: RouterRuntime

class CompareResponse(BaseModel):
    results: List[CompareResult]
