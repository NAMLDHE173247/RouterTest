export interface RouterDecision {
  primary_subject: string;
  secondary_subjects: string[];
  intent: string;
  target_slm: string;
  confidence: number;
  need_clarification: boolean;
  reason: string;
}

export interface RouterRuntime {
  router_type?: string;
  source?: string;
  latency_ms: number;
  input_tokens?: number;
  output_tokens?: number;
  parse_success: boolean;
  model?: string;
}

export interface RouterError {
  message: string;
}

export interface RouterResult {
  decision: RouterDecision | null;
  runtime: RouterRuntime | null;
  error: RouterError | null;
}

export type RouterType = "rule_v0" | "rule_v1" | "rule_v2" | "rule_v3" | "qwen_v0" | "hybrid";

export interface RouteRequest {
  router_id: string;
  question: string;
  history: string[];
}

export interface RouteResponse {
  router_id: string;
  router_name: string;
  decision: RouterDecision;
  runtime: RouterRuntime;
}

export interface RouterInfo {
  id: string;
  name: string;
  status: string;
  family?: string;
  version?: string;
  capabilities?: Record<string, boolean>;
  description?: string;
}

export interface HealthResponse {
  status: string;
  available_routers: string[];
}

export interface CompareResult {
  router_id: string;
  response?: RouteResponse;
  error?: string;
}

export interface CompareResponse {
  comparisons: CompareResult[];
}

export interface RouterMetrics {
  total_samples: number;
  primary_subject_accuracy: number;
  intent_accuracy: number;
  target_slm_accuracy: number;
  need_clarification_accuracy: number;
  exact_match_accuracy: number;
  total_errors: number;
  average_latency_ms: number;
  full_total_errors?: number;
  secondary_subject_exact_set_accuracy?: number;
  secondary_subject_micro_precision?: number;
  secondary_subject_micro_recall?: number;
  secondary_subject_micro_f1?: number;
  full_exact_match_accuracy?: number;
  metrics_by_case_type?: Record<string, Record<string, number>>;
}

export interface ErrorItem {
  id: string;
  question: string;
  history: string[];
  case_type: string;
  router_id: string;
  gold: any;
  prediction: any;
  wrong_fields: string[];
}

export interface EvaluationResponse {
  run_id: string;
  status: string;
  metrics: Record<string, RouterMetrics>;
  errors_count: number;
}

export interface EvaluationMetricsResponse {
  run_id: string;
  routers: Record<string, RouterMetrics>;
}

export interface EvaluationErrorsResponse {
  run_id: string;
  errors: ErrorItem[];
}

export interface ConfusionItem {
  gold: string;
  predicted: string;
  count: number;
  router_id: string;
}

export interface ErrorAnalysisResponse {
  run_id: string;
  total_errors_by_router: Record<string, number>;
  errors_by_field: Record<string, number>;
  errors_by_case_type: Record<string, number>;
  errors_by_router_and_case_type: Record<string, Record<string, number>>;
  errors_by_router_and_field: Record<string, Record<string, number>>;
  clarification_errors: Record<string, Record<string, number>>;
  subject_confusion: ConfusionItem[];
  intent_confusion: ConfusionItem[];
}

export interface DatasetListItem {
  dataset_id: string;
  name: string;
  format: string;
  total_samples: number;
  source: string;
}

export interface DatasetErrorDetail {
  line: number;
  id?: string;
  field?: string;
  message: string;
}

export interface DatasetUploadResponse {
  dataset_id?: string;
  filename: string;
  format: string;
  total_samples: number;
  valid_samples: number;
  invalid_samples: number;
  status: string;
  message?: string;
  errors?: DatasetErrorDetail[];
}
