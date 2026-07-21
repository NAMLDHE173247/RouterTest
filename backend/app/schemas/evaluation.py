from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.schemas.routing import HybridConfig

class EvaluationRequest(BaseModel):
    router_ids: List[str] = Field(default_factory=lambda: ["rule_v0", "rule_v1", "rule_v2"])
    dataset_id: Optional[str] = None
    limit: Optional[int] = None
    hybrid_config: Optional[HybridConfig] = None

class RouterMetrics(BaseModel):
    total_samples: int
    primary_subject_accuracy: float
    intent_accuracy: float
    target_slm_accuracy: float
    need_clarification_accuracy: float
    exact_match_accuracy: float
    total_errors: int
    average_latency_ms: float
    full_total_errors: int = 0
    secondary_subject_exact_set_accuracy: float = 0.0
    secondary_subject_micro_precision: float = 0.0
    secondary_subject_micro_recall: float = 0.0
    secondary_subject_micro_f1: float = 0.0
    full_exact_match_accuracy: float = 0.0
    metrics_by_case_type: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    median_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    average_tokens_per_sample: float = 0.0
    total_cost: Optional[float] = None
    average_cost_per_sample: Optional[float] = None
    cost_coverage_rate: float = 0.0
    valid_json_rate: float = 0.0
    schema_success_rate: float = 0.0
    failed_prediction_rate: float = 0.0
    retry_count: int = 0
    rule_only_usage_rate: float = 0.0
    fallback_invocation_count: int = 0
    fallback_invocation_rate: float = 0.0
    fallback_success_count: int = 0
    fallback_failure_count: int = 0
    fallback_selected_accuracy: Optional[float] = None
    rule_after_fallback_failure_count: int = 0
    fallback_usage_by_router: Dict[str, int] = Field(default_factory=dict)
    # Deprecated aliases retained for existing dashboards/artifacts.
    llm_fallback_rate: float = 0.0
    llm_success_rate: float = 0.0
    llm_failure_rate: float = 0.0
    degraded_mode_rate: float = 0.0
    rule_selected_accuracy: Optional[float] = None
    llm_selected_accuracy: Optional[float] = None
    accuracy_by_selected_source: Dict[str, float] = Field(default_factory=dict)
    rule_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    degraded_mode_count: int = 0
    fallback_trigger_distribution: Dict[str, int] = Field(default_factory=dict)

class EvaluationMetrics(BaseModel):
    run_id: str
    routers: Dict[str, RouterMetrics]

class ErrorItem(BaseModel):
    id: str
    question: str
    history: List[str]
    case_type: str
    router_id: str
    gold: Dict[str, Any]
    prediction: Dict[str, Any]
    wrong_fields: List[str]

class EvaluationErrors(BaseModel):
    run_id: str
    errors: List[ErrorItem]

class EvaluationResponse(BaseModel):
    run_id: str
    status: str
    metrics: Dict[str, RouterMetrics]
    errors_count: int

class ConfusionItem(BaseModel):
    gold: str
    predicted: str
    count: int
    router_id: str

class ErrorAnalysisResponse(BaseModel):
    run_id: str
    total_errors_by_router: Dict[str, int]
    errors_by_field: Dict[str, int]
    errors_by_case_type: Dict[str, int]
    errors_by_router_and_case_type: Dict[str, Dict[str, int]]
    errors_by_router_and_field: Dict[str, Dict[str, int]]
    clarification_errors: Dict[str, Dict[str, int]]
    subject_confusion: List[ConfusionItem]
    intent_confusion: List[ConfusionItem]
