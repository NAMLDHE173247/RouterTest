from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EvaluationRequest(BaseModel):
    router_ids: List[str] = Field(default_factory=lambda: ["rule_v0", "rule_v1", "rule_v2"])
    dataset_id: Optional[str] = None
    limit: Optional[int] = None

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
