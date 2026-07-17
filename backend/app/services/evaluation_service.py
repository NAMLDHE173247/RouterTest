import os
import json
import time
from uuid import uuid4
from datetime import datetime
from app.schemas.evaluation import EvaluationResponse, RouterMetrics, ErrorItem
from app.services.routing_service import routing_service
from app.schemas.routing import RouteRequest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DATASET_PATH = os.path.join(PROJECT_ROOT, "Rule_based_Router/rule_based_router_v2/router_experiment/data/test_router.jsonl")
RUNS_DIR = os.path.join(PROJECT_ROOT, "data/evaluation_runs")

class EvaluationService:
    RUNS_DIR = RUNS_DIR
    
    def run_evaluation(self, router_ids: list[str], dataset_id: str = None, limit: int = None) -> EvaluationResponse:
        unknown_router_ids = [
            router_id for router_id in router_ids
            if not routing_service.has_router(router_id)
        ]
        if unknown_router_ids:
            raise ValueError(
                "Unknown router IDs: " + ", ".join(unknown_router_ids)
            )

        run_id = f"eval_{datetime.now().strftime('%Y%md_%H%M%S')}_{uuid4().hex[:6]}"
        
        # Ensure directories
        run_dir = os.path.join(self.RUNS_DIR, run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        from app.services.dataset_service import dataset_service
        dataset_path = dataset_service.get_dataset_path(dataset_id)
        
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
        
        eval_fields = [
            "primary_subject",
            "secondary_subjects",
            "intent",
            "target_slm",
            "need_clarification",
        ]
        
        for rid in router_ids:
            service = routing_service.get_service(rid)
            
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
            case_stats = {}
            
            for row in records:
                question = row.get("question", "")
                history = row.get("history", [])
                
                # Evaluate
                try:
                    res = service.route(question=question, history=history)
                    decision = res.decision.model_dump()
                    latency = res.runtime.latency_ms
                except Exception as e:
                    # Fallback to empty for scoring on failure
                    decision = {"primary_subject": "error", "intent": "error", "target_slm": "error", "need_clarification": False}
                    latency = 0.0
                
                total_time += latency

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
            
        summary_json = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "total_errors": len(all_errors),
            "routers": router_ids
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
