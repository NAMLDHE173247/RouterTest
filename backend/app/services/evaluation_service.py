import os
import json
import time
import hashlib
import statistics
from uuid import uuid4
from datetime import datetime
from app.schemas.evaluation import EvaluationResponse, RouterMetrics, ErrorItem
from app.services.routing_service import routing_service
from app.schemas.routing import HybridConfig, RouteRequest
from app.llm_router_prompt import MAX_OUTPUT_TOKENS, PROMPT_VERSION, TEMPERATURE
from app.settings_store import SettingsStore

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DATASET_PATH = os.path.join(PROJECT_ROOT, "Rule_based_Router/rule_based_router_v2/router_experiment/data/test_router.jsonl")
RUNS_DIR = os.path.join(PROJECT_ROOT, "data/evaluation_runs")

class EvaluationService:
    RUNS_DIR = RUNS_DIR
    
    def run_evaluation(
        self,
        router_ids: list[str],
        dataset_id: str = None,
        limit: int = None,
        hybrid_config: HybridConfig | None = None,
    ) -> EvaluationResponse:
        unknown_router_ids = [
            router_id for router_id in router_ids
            if not routing_service.has_router(router_id)
        ]
        if unknown_router_ids:
            raise ValueError(
                "Unknown router IDs: " + ", ".join(unknown_router_ids)
            )
        if "hybrid" in router_ids and (hybrid_config is None or not hybrid_config.resolved_fallback_router_id()):
            raise ValueError("Hybrid evaluation requires an explicit fallback_router_id")

        run_id = f"eval_{datetime.now().strftime('%Y%md_%H%M%S')}_{uuid4().hex[:6]}"
        
        # Ensure directories
        run_dir = os.path.join(self.RUNS_DIR, run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        from app.services.dataset_service import dataset_service
        dataset_path = dataset_service.get_dataset_path(dataset_id)
        with open(dataset_path, "rb") as dataset_file:
            dataset_hash = hashlib.sha256(dataset_file.read()).hexdigest()
        
        # Load dataset
        records = []
        ext = dataset_path.split(".")[-1].lower()
        if ext == "jsonl":
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        else:
            with open(dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if "items" in data:
                        data = data["items"]
                    elif "data" in data:
                        data = data["data"]
                records = data
        
        if limit and limit > 0:
            records = records[:limit]
            
        # State
        metrics_dict = {}
        all_errors = []
        run_configs = {}
        prediction_artifacts = []
        
        eval_fields = [
            "primary_subject",
            "secondary_subjects",
            "intent",
            "target_slm",
            "need_clarification",
        ]
        
        for rid in router_ids:
            service = routing_service.get_service(rid)
            adapter = getattr(service, "adapter", None)
            model = getattr(service, "model", None) or getattr(adapter, "model", None)
            is_llm_router = bool(model)
            client = getattr(adapter, "client", None)
            fallback_id = hybrid_config.resolved_fallback_router_id() if rid == "hybrid" and hybrid_config else None
            fallback_service = routing_service.get_service(fallback_id) if fallback_id else None
            fallback_metadata = fallback_service.get_metadata() if fallback_service else None
            fallback_details = SettingsStore.get_qwen_health_details() if fallback_id == "qwen_v0" else {}
            run_configs[rid] = {
                "router_id": rid,
                "display_name": getattr(service, "router_name", rid),
                "model_slug": model,
                "prompt_version": PROMPT_VERSION if model else None,
                "temperature": TEMPERATURE if model else None,
                "max_output_tokens": MAX_OUTPUT_TOKENS if model else None,
                "timeout_seconds": getattr(client, "timeout", None),
                "max_retries": 1 if model else 0,
                "structured_output_requested": bool(model),
                "dataset_id": dataset_id or "default_v2_test_router",
                "dataset_hash": dataset_hash,
                "sample_count": len(records),
                "concurrency": 1,
                "started_at": datetime.now().isoformat(),
                "hybrid_config": hybrid_config.model_dump() if rid == "hybrid" and hybrid_config else None,
                "fallback_router_id": fallback_id,
                "fallback_family": fallback_metadata.get("family") if fallback_metadata else None,
                "fallback_config": {
                    "router_version": fallback_metadata.get("version"),
                    "service_type": "qwen_gpu_service" if fallback_id == "qwen_v0" else "openrouter",
                    "model_name": fallback_metadata.get("model"),
                    "prompt_version": getattr(getattr(fallback_service, "adapter", None), "PROMPT_VERSION", None),
                    "model_loaded": fallback_details.get("model_loaded"),
                    "status_checked_at": fallback_details.get("checked_at"),
                    "gpu_service_version": fallback_details.get("service_version"),
                } if fallback_id else None,
            }
            
            correct_ps = 0
            correct_intent = 0
            correct_slm = 0
            correct_nc = 0
            core_exact_matches = 0
            full_exact_matches = 0
            secondary_exact_matches = 0
            secondary_tp = 0
            secondary_fp = 0
            secondary_fn = 0
            total_time = 0.0
            latencies = []
            total_input_tokens = 0
            total_output_tokens = 0
            total_tokens = 0
            total_cost = 0.0
            cost_count = 0
            valid_json_count = 0
            schema_success_count = 0
            failed_prediction_count = 0
            retry_count_total = 0
            hybrid_rule_only_count = 0
            hybrid_llm_called_count = 0
            hybrid_llm_success_count = 0
            hybrid_llm_failure_count = 0
            hybrid_degraded_count = 0
            hybrid_rule_selected_correct = 0
            hybrid_rule_selected_total = 0
            hybrid_llm_selected_correct = 0
            hybrid_llm_selected_total = 0
            hybrid_rule_latency_total = 0.0
            hybrid_llm_latency_total = 0.0
            hybrid_trigger_distribution = {}
            fallback_invocation_count = 0
            fallback_success_count = 0
            fallback_failure_count = 0
            rule_after_fallback_failure_count = 0
            fallback_usage_by_router = {}
            consecutive_fallback_failures = 0
            circuit_open = False
            case_stats = {}
            
            for row in records:
                question = row.get("question", "")
                history = row.get("history", [])
                res = None
                hybrid_runtime = None
                
                # Evaluate
                try:
                    if rid == "hybrid":
                        effective_config = hybrid_config
                        if circuit_open:
                            effective_config = hybrid_config.model_copy(update={
                                "fallback_on_low_confidence": False,
                                "fallback_on_unknown_subject": False,
                                "fallback_on_need_clarification": False,
                                "fallback_on_rule_error": False,
                            })
                        res = service.route(question=question, history=history, config=effective_config)
                    else:
                        res = service.route(question=question, history=history)
                    decision = res.decision.model_dump()
                    latency = res.runtime.latency_ms
                    runtime = res.runtime.model_dump()
                    valid_json_count += 1 if is_llm_router and res.runtime.parse_success else 0
                    schema_success_count += 1 if is_llm_router and res.runtime.schema_success else 0
                    total_input_tokens += res.runtime.input_tokens or 0
                    total_output_tokens += res.runtime.output_tokens or 0
                    total_tokens += res.runtime.total_tokens or 0
                    if res.runtime.cost is not None:
                        total_cost += res.runtime.cost
                        cost_count += 1
                    retry_count_total += res.runtime.retry_count
                    hybrid_runtime = res.runtime.hybrid
                    if hybrid_runtime:
                        if hybrid_runtime.selected_source == "rule":
                            hybrid_rule_only_count += 1
                        if hybrid_runtime.fallback_called:
                            fallback_invocation_count += 1
                            fallback_usage_by_router[hybrid_runtime.fallback_router_id] = fallback_usage_by_router.get(hybrid_runtime.fallback_router_id, 0) + 1
                            hybrid_llm_called_count += 1
                        if hybrid_runtime.selected_source == "fallback":
                            fallback_success_count += 1
                            consecutive_fallback_failures = 0
                            hybrid_llm_success_count += 1
                        if hybrid_runtime.selected_source == "rule_after_fallback_failure":
                            fallback_failure_count += 1
                            rule_after_fallback_failure_count += 1
                            consecutive_fallback_failures += 1
                            if consecutive_fallback_failures >= 3:
                                circuit_open = True
                            hybrid_llm_failure_count += 1
                        elif hybrid_runtime.selected_source != "fallback":
                            consecutive_fallback_failures = 0
                        if hybrid_runtime.degraded_mode:
                            hybrid_degraded_count += 1
                        hybrid_rule_latency_total += hybrid_runtime.rule_latency_ms
                        hybrid_llm_latency_total += hybrid_runtime.llm_latency_ms
                        for trigger in hybrid_runtime.fallback_triggers:
                            hybrid_trigger_distribution[trigger] = hybrid_trigger_distribution.get(trigger, 0) + 1
                    failure_code = None
                except Exception as e:
                    # Fallback to empty for scoring on failure
                    decision = {"primary_subject": "error", "intent": "error", "target_slm": "error", "need_clarification": False}
                    latency = 0.0
                    runtime = None
                    failure_code = getattr(e, "code", "router_error")
                    failed_prediction_count += 1

                total_time += latency
                latencies.append(latency)
                prediction_artifacts.append({
                    "router_id": rid,
                    "sample_id": row.get("id", ""),
                    "gold": {k: row.get(k) for k in eval_fields},
                    "prediction": {k: decision.get(k) for k in eval_fields},
                    "execution_metadata": runtime,
                    "error_code": failure_code,
                })

                case_type = row.get("case_type", "unknown")
                case_stat = case_stats.setdefault(case_type, {
                    "total_samples": 0,
                    "primary_subject_correct": 0,
                    "intent_correct": 0,
                    "target_slm_correct": 0,
                    "need_clarification_correct": 0,
                    "core_exact_match_correct": 0,
                    "full_exact_match_correct": 0,
                })
                case_stat["total_samples"] += 1
                
                # Compare
                wrong_fields = []
                
                if decision.get("primary_subject") == row.get("primary_subject"):
                    correct_ps += 1
                    case_stat["primary_subject_correct"] += 1
                else:
                    wrong_fields.append("primary_subject")
                    
                if decision.get("intent") == row.get("intent"):
                    correct_intent += 1
                    case_stat["intent_correct"] += 1
                else:
                    wrong_fields.append("intent")
                    
                if decision.get("target_slm") == row.get("target_slm"):
                    correct_slm += 1
                    case_stat["target_slm_correct"] += 1
                else:
                    wrong_fields.append("target_slm")
                    
                if decision.get("need_clarification") == row.get("need_clarification"):
                    correct_nc += 1
                    case_stat["need_clarification_correct"] += 1
                else:
                    wrong_fields.append("need_clarification")

                if not wrong_fields:
                    core_exact_matches += 1
                    case_stat["core_exact_match_correct"] += 1
                    
                gold_secondary = set(row.get("secondary_subjects", []))
                predicted_secondary = set(decision.get("secondary_subjects", []))
                if gold_secondary == predicted_secondary:
                    secondary_exact_matches += 1
                secondary_tp += len(gold_secondary & predicted_secondary)
                secondary_fp += len(predicted_secondary - gold_secondary)
                secondary_fn += len(gold_secondary - predicted_secondary)

                if gold_secondary != predicted_secondary:
                    wrong_fields.append("secondary_subjects")

                if len(wrong_fields) == 0:
                    full_exact_matches += 1
                    case_stat["full_exact_match_correct"] += 1
                else:
                    # Log error
                    all_errors.append(ErrorItem(
                        id=row.get("id", ""),
                        question=question,
                        history=history,
                        case_type=row.get("case_type", "unknown"),
                        router_id=rid,
                        gold={k: row.get(k) for k in eval_fields},
                        prediction={k: decision.get(k) for k in eval_fields},
                        wrong_fields=wrong_fields
                    ))

                if hybrid_runtime:
                    selected_source = hybrid_runtime.selected_source
                    if selected_source == "rule":
                        hybrid_rule_selected_total += 1
                        hybrid_rule_selected_correct += 1 if not wrong_fields else 0
                    elif selected_source == "fallback":
                        hybrid_llm_selected_total += 1
                        hybrid_llm_selected_correct += 1 if not wrong_fields else 0

            def accuracy_for(correct: int, denominator: int) -> float:
                return correct / denominator if denominator else 0.0

            precision = secondary_tp / (secondary_tp + secondary_fp) if secondary_tp + secondary_fp else 0.0
            recall = secondary_tp / (secondary_tp + secondary_fn) if secondary_tp + secondary_fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            case_metrics = {
                case_type: {
                    "total_samples": values["total_samples"],
                    "primary_subject_accuracy": accuracy_for(values["primary_subject_correct"], values["total_samples"]),
                    "intent_accuracy": accuracy_for(values["intent_correct"], values["total_samples"]),
                    "target_slm_accuracy": accuracy_for(values["target_slm_correct"], values["total_samples"]),
                    "need_clarification_accuracy": accuracy_for(values["need_clarification_correct"], values["total_samples"]),
                    "exact_match_accuracy": accuracy_for(values["core_exact_match_correct"], values["total_samples"]),
                    "full_exact_match_accuracy": accuracy_for(values["full_exact_match_correct"], values["total_samples"]),
                }
                for case_type, values in case_stats.items()
            }
            
            # Aggregate metrics
            total = len(records)
            is_hybrid_router = rid == "hybrid"
            sorted_latencies = sorted(latencies)
            p95_index = min(len(sorted_latencies) - 1, max(0, int(len(sorted_latencies) * 0.95) - 1)) if sorted_latencies else 0
            metrics_dict[rid] = RouterMetrics(
                total_samples=total,
                primary_subject_accuracy=correct_ps / total if total else 0,
                intent_accuracy=correct_intent / total if total else 0,
                target_slm_accuracy=correct_slm / total if total else 0,
                need_clarification_accuracy=correct_nc / total if total else 0,
                exact_match_accuracy=core_exact_matches / total if total else 0,
                total_errors=total - core_exact_matches,
                average_latency_ms=total_time / total if total else 0,
                full_total_errors=total - full_exact_matches,
                secondary_subject_exact_set_accuracy=secondary_exact_matches / total if total else 0,
                secondary_subject_micro_precision=precision,
                secondary_subject_micro_recall=recall,
                secondary_subject_micro_f1=f1,
                full_exact_match_accuracy=full_exact_matches / total if total else 0,
                metrics_by_case_type=case_metrics,
                median_latency_ms=statistics.median(latencies) if latencies else 0.0,
                p95_latency_ms=sorted_latencies[p95_index] if sorted_latencies else 0.0,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_tokens=total_tokens,
                average_tokens_per_sample=total_tokens / total if total else 0.0,
                total_cost=total_cost if cost_count else None,
                average_cost_per_sample=total_cost / total if cost_count and total else None,
                cost_coverage_rate=cost_count / total if total else 0.0,
                valid_json_rate=valid_json_count / total if is_llm_router and total else 0.0,
                schema_success_rate=schema_success_count / total if is_llm_router and total else 0.0,
                failed_prediction_rate=failed_prediction_count / total if is_llm_router and total else 0.0,
                retry_count=retry_count_total,
                rule_only_usage_rate=hybrid_rule_only_count / total if is_hybrid_router and total else 0.0,
                fallback_invocation_count=fallback_invocation_count,
                fallback_invocation_rate=fallback_invocation_count / total if is_hybrid_router and total else 0.0,
                fallback_success_count=fallback_success_count,
                fallback_failure_count=fallback_failure_count,
                fallback_selected_accuracy=(hybrid_llm_selected_correct / hybrid_llm_selected_total) if is_hybrid_router and hybrid_llm_selected_total else None,
                rule_after_fallback_failure_count=rule_after_fallback_failure_count,
                fallback_usage_by_router=fallback_usage_by_router,
                llm_fallback_rate=fallback_invocation_count / total if is_hybrid_router and total else 0.0,
                llm_success_rate=(fallback_success_count / fallback_invocation_count) if is_hybrid_router and fallback_invocation_count else 0.0,
                llm_failure_rate=(fallback_failure_count / fallback_invocation_count) if is_hybrid_router and fallback_invocation_count else 0.0,
                degraded_mode_rate=hybrid_degraded_count / total if is_hybrid_router and total else 0.0,
                rule_selected_accuracy=(hybrid_rule_selected_correct / hybrid_rule_selected_total) if is_hybrid_router and hybrid_rule_selected_total else None,
                llm_selected_accuracy=(hybrid_llm_selected_correct / hybrid_llm_selected_total) if is_hybrid_router and hybrid_llm_selected_total else None,
                accuracy_by_selected_source={
                    "rule": hybrid_rule_selected_correct / hybrid_rule_selected_total
                    if hybrid_rule_selected_total else 0.0,
                    "fallback": hybrid_llm_selected_correct / hybrid_llm_selected_total
                    if hybrid_llm_selected_total else 0.0,
                    "llm": hybrid_llm_selected_correct / hybrid_llm_selected_total
                    if hybrid_llm_selected_total else 0.0,
                } if is_hybrid_router else {},
                rule_latency_ms=hybrid_rule_latency_total / total if is_hybrid_router and total else 0.0,
                llm_latency_ms=hybrid_llm_latency_total / hybrid_llm_called_count if is_hybrid_router and hybrid_llm_called_count else 0.0,
                degraded_mode_count=hybrid_degraded_count if is_hybrid_router else 0,
                fallback_trigger_distribution=hybrid_trigger_distribution if is_hybrid_router else {},
            )
            
        # Save output to disk
        metrics_json = {
            "run_id": run_id,
            "routers": {k: v.model_dump() for k, v in metrics_dict.items()}
        }
        with open(os.path.join(run_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(metrics_json, f, indent=2, ensure_ascii=False)
            
        errors_json = {
            "run_id": run_id,
            "errors": [e.model_dump() for e in all_errors]
        }
        with open(os.path.join(run_dir, "errors.json"), "w", encoding="utf-8") as f:
            json.dump(errors_json, f, indent=2, ensure_ascii=False)

        with open(os.path.join(run_dir, "run_config.json"), "w", encoding="utf-8") as f:
            json.dump({"router_configs": run_configs}, f, indent=2, ensure_ascii=False)

        with open(os.path.join(run_dir, "predictions.jsonl"), "w", encoding="utf-8") as f:
            for prediction in prediction_artifacts:
                f.write(json.dumps(prediction, ensure_ascii=False) + "\n")
            
        summary_json = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "total_errors": len(all_errors),
            "routers": router_ids,
            "run_config_file": "run_config.json",
            "predictions_file": "predictions.jsonl",
        }
        with open(os.path.join(run_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary_json, f, indent=2, ensure_ascii=False)
            
        return EvaluationResponse(
            run_id=run_id,
            status="completed",
            metrics=metrics_dict,
            errors_count=len(all_errors)
        )

    def get_metrics(self, run_id: str) -> dict:
        path = os.path.join(self.RUNS_DIR, run_id, "metrics.json")
        if not os.path.exists(path):
            raise FileNotFoundError("Metrics not found")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_errors(self, run_id: str) -> dict:
        path = os.path.join(self.RUNS_DIR, run_id, "errors.json")
        if not os.path.exists(path):
            raise FileNotFoundError("Errors not found")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def get_summary(self, run_id: str) -> dict:
        path = os.path.join(self.RUNS_DIR, run_id, "summary.json")
        if not os.path.exists(path):
            raise FileNotFoundError("Summary not found")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_analysis(self, run_id: str) -> dict:
        errors_data = self.get_errors(run_id)
        errors = errors_data.get("errors", [])
        
        from collections import defaultdict
        
        total_errors_by_router = defaultdict(int)
        errors_by_field = defaultdict(int)
        errors_by_case_type = defaultdict(int)
        errors_by_router_and_case_type = defaultdict(lambda: defaultdict(int))
        errors_by_router_and_field = defaultdict(lambda: defaultdict(int))
        clarification_errors = defaultdict(lambda: {"false_positive": 0, "false_negative": 0})
        
        subject_conf = defaultdict(int)
        intent_conf = defaultdict(int)

        for err in errors:
            rid = err.get("router_id", "unknown")
            case_type = err.get("case_type", "unknown")
            wrong_fields = err.get("wrong_fields", [])
            gold = err.get("gold", {})
            pred = err.get("prediction", {})
            
            total_errors_by_router[rid] += 1
            errors_by_case_type[case_type] += 1
            errors_by_router_and_case_type[rid][case_type] += 1
            
            for field in wrong_fields:
                errors_by_field[field] += 1
                errors_by_router_and_field[rid][field] += 1
                
                if field == "need_clarification":
                    g_val = gold.get("need_clarification")
                    p_val = pred.get("need_clarification")
                    if g_val is False and p_val is True:
                        clarification_errors[rid]["false_positive"] += 1
                    elif g_val is True and p_val is False:
                        clarification_errors[rid]["false_negative"] += 1
                
                if field == "primary_subject":
                    g_subj = str(gold.get("primary_subject", ""))
                    p_subj = str(pred.get("primary_subject", ""))
                    subject_conf[(rid, g_subj, p_subj)] += 1
                    
                if field == "intent":
                    g_int = str(gold.get("intent", ""))
                    p_int = str(pred.get("intent", ""))
                    intent_conf[(rid, g_int, p_int)] += 1
                    
        # Format confusions
        subject_confusion_list = []
        for (rid, g, p), count in subject_conf.items():
            subject_confusion_list.append({"router_id": rid, "gold": g, "predicted": p, "count": count})
            
        intent_confusion_list = []
        for (rid, g, p), count in intent_conf.items():
            intent_confusion_list.append({"router_id": rid, "gold": g, "predicted": p, "count": count})
            
        # Sort confusions by count desc
        subject_confusion_list.sort(key=lambda x: x["count"], reverse=True)
        intent_confusion_list.sort(key=lambda x: x["count"], reverse=True)

        return {
            "run_id": run_id,
            "total_errors_by_router": dict(total_errors_by_router),
            "errors_by_field": dict(errors_by_field),
            "errors_by_case_type": dict(errors_by_case_type),
            "errors_by_router_and_case_type": {k: dict(v) for k, v in errors_by_router_and_case_type.items()},
            "errors_by_router_and_field": {k: dict(v) for k, v in errors_by_router_and_field.items()},
            "clarification_errors": {k: dict(v) for k, v in clarification_errors.items()},
            "subject_confusion": subject_confusion_list,
            "intent_confusion": intent_confusion_list
        }

evaluation_service = EvaluationService()
