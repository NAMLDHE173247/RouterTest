export interface RouterDecision {
  primary_subject: string;
  secondary_subjects: string[];
  intent: string;
  target_slm: string;
  confidence: number;
  need_clarification: boolean;
  reason: string;
}

export interface HybridConfig {
  rule_router_id: string;
  fallback_router_id?: string;
  llm_router_id?: string;
  rule_confidence_threshold: number;
  fallback_on_low_confidence: boolean;
  fallback_on_unknown_subject: boolean;
  fallback_on_need_clarification: boolean;
  fallback_on_rule_error: boolean;
  fallback_failure_policy: 'use_rule';
}

export interface HybridRuntime {
  hybrid_version: string;
  rule_router_id: string;
  fallback_router_id: string;
  fallback_family?: string | null;
  rule_called: boolean;
  fallback_called: boolean;
  selected_source: 'rule' | 'fallback' | 'rule_after_fallback_failure';
  fallback_triggers: string[];
  primary_fallback_trigger?: string | null;
  rule_confidence?: number | null;
  rule_latency_ms: number;
  fallback_latency_ms: number;
  total_latency_ms: number;
  degraded_mode: boolean;
  fallback_error_code?: string | null;
  config_snapshot: HybridConfig;
  rule_decision?: RouterDecision | null;
  fallback_decision?: RouterDecision | null;
  llm_router_id?: string | null;
  llm_called?: boolean;
  llm_latency_ms?: number;
  llm_error_code?: string | null;
  llm_decision?: RouterDecision | null;
}

export interface RouterRuntime {
  router_type?: string;
  source?: string;
  latency_ms: number;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  cost?: number | null;
  parse_success: boolean;
  schema_success?: boolean;
  model?: string;
  requested_model?: string;
  resolved_model?: string;
  provider?: string;
  prompt_version?: string;
  structured_output_mode?: string;
  retry_count?: number;
  attempt_count?: number;
  retry_reason?: string;
  finish_reason?: string;
  hybrid?: HybridRuntime;
}

export interface RouterError {
  message: string;
  code?: string;
}

export interface RouterResult {
  decision: RouterDecision | null;
  runtime: RouterRuntime | null;
  error: RouterError | null;
}

export type RouterType = "rule_v0" | "rule_v1" | "rule_v2" | "rule_v3" | "qwen_v0" | "hybrid" | "llm_deepseek_v0" | "llm_gemini_v0" | "llm_openai_v0";

export interface RouteRequest {
  router_id: string;
  question: string;
  history: string[];
  hybrid_config?: HybridConfig;
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
  enabled?: boolean;
  family?: string;
  version?: string;
  capabilities?: Record<string, boolean>;
  description?: string;
  model?: string;
  available?: boolean;
  unavailable_reason?: string;
}

export interface HealthResponse {
  status: string;
  available_routers: string[];
}

export interface CompareResult {
  router_id: string;
  response?: RouteResponse;
  error?: RouterError | string;
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
  median_latency_ms?: number;
  p95_latency_ms?: number;
  total_input_tokens?: number;
  total_output_tokens?: number;
  total_tokens?: number;
  average_tokens_per_sample?: number;
  total_cost?: number | null;
  average_cost_per_sample?: number | null;
  cost_coverage_rate?: number;
  valid_json_rate?: number;
  schema_success_rate?: number;
  failed_prediction_rate?: number;
  retry_count?: number;
  rule_only_usage_rate?: number;
  fallback_invocation_count?: number;
  fallback_invocation_rate?: number;
  fallback_success_count?: number;
  fallback_failure_count?: number;
  fallback_selected_accuracy?: number | null;
  rule_after_fallback_failure_count?: number;
  fallback_usage_by_router?: Record<string, number>;
  llm_fallback_rate?: number;
  llm_success_rate?: number;
  llm_failure_rate?: number;
  degraded_mode_rate?: number;
  rule_selected_accuracy?: number | null;
  llm_selected_accuracy?: number | null;
  accuracy_by_selected_source?: Record<string, number>;
  rule_latency_ms?: number;
  llm_latency_ms?: number;
  degraded_mode_count?: number;
  fallback_trigger_distribution?: Record<string, number>;
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
