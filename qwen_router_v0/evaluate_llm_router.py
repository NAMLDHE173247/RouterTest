import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

try:
    import torch
    TORCH_AVAILABLE = True
    TORCH_VERSION = torch.__version__
    CUDA_AVAILABLE = torch.cuda.is_available()
    GPU_NAME = torch.cuda.get_device_name(0) if CUDA_AVAILABLE else None
except ImportError:
    TORCH_AVAILABLE = False
    TORCH_VERSION = None
    CUDA_AVAILABLE = False
    GPU_NAME = None

from llm_router import QwenRouter, RouterGenerationError, get_router


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

logger = setup_logger()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Qwen Router on a JSONL dataset.")
    parser.add_argument("--data", type=str, default="data/dev_router.jsonl", help="Path to the JSONL dataset.")
    parser.add_argument("--output-dir", type=str, default="outputs/qwen25_7b_dev", help="Path to the output directory.")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-7B-Instruct", help="Model name.")
    parser.add_argument("--max-input-tokens", type=int, default=2048, help="Max input tokens.")
    parser.add_argument("--max-new-tokens", type=int, default=256, help="Max new tokens.")
    parser.add_argument("--max-retries", type=int, default=2, help="Max retries for generation.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of samples to process.")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--resume", action="store_true", help="Resume from an existing predictions.jsonl file.")
    group.add_argument("--overwrite", action="store_true", help="Overwrite existing output directory.")
    
    return parser


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')


def save_json(path: Path, data: Any) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_existing_predictions(path: Path) -> Tuple[List[Dict[str, Any]], set[str]]:
    records = []
    completed_ids = set()
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                records.append(record)
                completed_ids.add(record['id'])
    return records, completed_ids


def get_run_config(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "model_name": args.model,
        "dataset_path": args.data,
        "output_dir": args.output_dir,
        "max_input_tokens": args.max_input_tokens,
        "max_new_tokens": args.max_new_tokens,
        "max_retries": args.max_retries,
        "seed": args.seed,
        "decoding": "greedy (do_sample=False)",
        "quantization": "bitsandbytes 4-bit NF4",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "torch_version": TORCH_VERSION,
        "cuda_available": CUDA_AVAILABLE,
        "gpu_name": GPU_NAME
    }


def compute_field_matches(gold: Dict[str, Any], prediction: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    if not prediction:
        return {
            "primary_subject": False,
            "intent": False,
            "target_slm": False,
            "need_clarification": False
        }
        
    return {
        "primary_subject": gold.get("primary_subject") == prediction.get("primary_subject"),
        "intent": gold.get("intent") == prediction.get("intent"),
        "target_slm": gold.get("target_slm") == prediction.get("target_slm"),
        "need_clarification": gold.get("need_clarification") == prediction.get("need_clarification")
    }


def compute_case_type_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    case_type_stats = {}
    
    for record in records:
        case_type = record.get("case_type", "unknown")
        if not case_type:
            case_type = "unknown"
            
        if case_type not in case_type_stats:
            case_type_stats[case_type] = {
                "total": 0,
                "exact_match_count": 0,
                "primary_subject_count": 0,
                "intent_count": 0,
                "target_slm_count": 0,
                "need_clarification_count": 0
            }
            
        stats = case_type_stats[case_type]
        stats["total"] += 1
        
        if record.get("exact_match", False):
            stats["exact_match_count"] += 1
            
        matches = record.get("field_matches", {})
        if matches.get("primary_subject", False):
            stats["primary_subject_count"] += 1
        if matches.get("intent", False):
            stats["intent_count"] += 1
        if matches.get("target_slm", False):
            stats["target_slm_count"] += 1
        if matches.get("need_clarification", False):
            stats["need_clarification_count"] += 1
            
    case_type_metrics = {}
    for ct, stats in case_type_stats.items():
        total = stats["total"]
        case_type_metrics[ct] = {
            "total": total,
            "exact_match_accuracy": stats["exact_match_count"] / total if total > 0 else 0,
            "primary_subject_accuracy": stats["primary_subject_count"] / total if total > 0 else 0,
            "intent_accuracy": stats["intent_count"] / total if total > 0 else 0,
            "target_slm_accuracy": stats["target_slm_count"] / total if total > 0 else 0,
            "need_clarification_accuracy": stats["need_clarification_count"] / total if total > 0 else 0,
        }
        
    return case_type_metrics


def compute_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_samples = len(records)
    if total_samples == 0:
        return {"total_samples": 0}
        
    successful_predictions = 0
    failed_predictions = 0
    exact_matches = 0
    
    primary_subject_correct = 0
    intent_correct = 0
    target_slm_correct = 0
    need_clarification_correct = 0
    
    total_retries = 0
    total_input_tokens = 0
    total_output_tokens = 0
    latencies = []
    
    for record in records:
        if record.get("parse_success", False) and not record.get("failure"):
            successful_predictions += 1
            total_retries += record.get("retries", 0)
            total_input_tokens += record.get("input_tokens", 0)
            total_output_tokens += record.get("output_tokens", 0)
            
            latency = record.get("latency_ms")
            if latency is not None:
                latencies.append(latency)
        else:
            failed_predictions += 1
            
        if record.get("exact_match", False):
            exact_matches += 1
            
        matches = record.get("field_matches", {})
        if matches.get("primary_subject", False): primary_subject_correct += 1
        if matches.get("intent", False): intent_correct += 1
        if matches.get("target_slm", False): target_slm_correct += 1
        if matches.get("need_clarification", False): need_clarification_correct += 1

    latencies.sort()
    
    metrics = {
        "accuracy": {
            "primary_subject_accuracy": primary_subject_correct / total_samples,
            "intent_accuracy": intent_correct / total_samples,
            "target_slm_accuracy": target_slm_correct / total_samples,
            "need_clarification_accuracy": need_clarification_correct / total_samples,
            "exact_match_accuracy": exact_matches / total_samples
        },
        "generation": {
            "total_samples": total_samples,
            "successful_predictions": successful_predictions,
            "failed_predictions": failed_predictions,
            "json_parse_success_rate": successful_predictions / total_samples,
            "total_errors": failed_predictions,
            "total_retries": total_retries,
            "average_retries": total_retries / successful_predictions if successful_predictions > 0 else 0,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "average_input_tokens": total_input_tokens / successful_predictions if successful_predictions > 0 else 0,
            "average_output_tokens": total_output_tokens / successful_predictions if successful_predictions > 0 else 0
        },
        "latency": {},
        "case_type_metrics": compute_case_type_metrics(records)
    }
    
    if latencies:
        metrics["latency"] = {
            "average_latency_ms": sum(latencies) / len(latencies),
            "median_latency_ms": latencies[len(latencies)//2],
            "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
            "min_latency_ms": latencies[0],
            "max_latency_ms": latencies[-1]
        }
        
    return metrics


def evaluate(args: argparse.Namespace) -> None:
    data_path = Path(args.data)
    output_dir = Path(args.output_dir)
    predictions_path = output_dir / "predictions.jsonl"
    
    # Validation logic for output_dir
    if output_dir.exists() and predictions_path.exists():
        if not args.resume and not args.overwrite:
            raise ValueError(
                f"Output directory {output_dir} already exists and contains predictions.jsonl. "
                f"Please use --resume to continue or --overwrite to clear old results."
            )
            
    if args.overwrite and output_dir.exists():
        logger.info(f"Overwriting output directory: {output_dir}")
        for file in output_dir.glob("*"):
            if file.is_file():
                file.unlink()
            
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save config
    run_config = get_run_config(args)
    save_json(output_dir / "run_config.json", run_config)
    
    # Read dataset
    dataset = read_jsonl(data_path)
    logger.info(f"Loaded {len(dataset)} items from {data_path}")
    
    # Handle limit
    if args.limit is not None:
        dataset = dataset[:args.limit]
        logger.info(f"Limited evaluation to first {args.limit} items.")
        
    # Handle resume
    completed_records = []
    completed_ids = set()
    if args.resume and predictions_path.exists():
        completed_records, completed_ids = load_existing_predictions(predictions_path)
        logger.info(f"Resuming evaluation. Found {len(completed_ids)} completed items.")
        
    # Load Router
    logger.info("Initializing Router...")
    router = QwenRouter(
        model_name=args.model,
        max_input_tokens=args.max_input_tokens,
        max_new_tokens=args.max_new_tokens,
        seed=args.seed
    )
    # Inject vào Singleton pattern nếu hàm nào khác vô tình dùng tới get_router()
    import llm_router
    llm_router._ROUTER_INSTANCE = router
    
    logger.info("Starting evaluation loop...")
    processed_count = 0
    
    for item in dataset:
        item_id = item.get("id")
        
        if item_id in completed_ids:
            continue
            
        question = item.get("question", "")
        history = item.get("history", [])
        case_type = item.get("case_type", "unknown")
        
        gold = {
            "primary_subject": item.get("primary_subject"),
            "intent": item.get("intent"),
            "target_slm": item.get("target_slm"),
            "need_clarification": item.get("need_clarification")
        }
        
        prediction = None
        raw_response = None
        latency_ms = None
        input_tokens = None
        output_tokens = None
        retries = None
        parse_success = False
        failure_msg = None
        
        try:
            # Lưu ý KHÔNG truyền các tham số gold vào hàm route, Router chỉ thấy question và history
            result = router.route(question=question, history=history, max_retries=args.max_retries)
            prediction = result.get("prediction")
            raw_response = result.get("raw_response")
            latency_ms = result.get("latency_ms")
            input_tokens = result.get("input_tokens")
            output_tokens = result.get("output_tokens")
            retries = result.get("retries")
            parse_success = result.get("parse_success", False)
        except RouterGenerationError as e:
            logger.warning(f"Failed to generate for item {item_id}: {e}")
            failure_msg = str(e)
            
        except Exception as e:
            # Ghi rõ lỗi nghiêm trọng, ví dụ RuntimeError/CUDA OOM
            logger.error(f"Critical error on item {item_id}: {e}")
            failure_msg = f"Critical Error: {str(e)}"
            # Raise lên để Colab không chạy tiếp mù quáng khi OOM
            if "CUDA out of memory" in str(e) or "out of memory" in str(e).lower():
                raise e
                
        field_matches = compute_field_matches(gold, prediction)
        exact_match = all(field_matches.values())
        
        record = {
            "id": item_id,
            "question": question,
            "history": history,
            "case_type": case_type,
            "gold": gold,
            "prediction": prediction,
            "field_matches": field_matches,
            "exact_match": exact_match,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "retries": retries,
            "parse_success": parse_success,
            "raw_response": raw_response,
            "failure": failure_msg
        }
        
        append_jsonl(predictions_path, record)
        completed_records.append(record)
        completed_ids.add(item_id)
        
        processed_count += 1
        if processed_count % 10 == 0:
            logger.info(f"Processed {processed_count} items in current run...")
            
    logger.info("Evaluation loop completed. Computing metrics...")
    
    # Filter errors
    errors = [r for r in completed_records if not r.get("exact_match") or not r.get("parse_success")]
    save_json(output_dir / "errors.json", errors)
    
    # Compute metrics
    metrics = compute_metrics(completed_records)
    save_json(output_dir / "metrics.json", metrics)
    
    logger.info("Metrics:")
    logger.info(json.dumps(metrics.get("accuracy", {}), indent=2))
    logger.info(f"Saved results to {output_dir}")


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    evaluate(args)
