"""Evaluate Rule-based Router V3 and write phase-specific artifacts."""

import argparse
import json
import os
import time
from collections import defaultdict
from typing import Any

from rule_router import route_question


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_DATASET_PATH = os.path.join(EXPERIMENT_DIR, "data", "test_router.jsonl")
DEFAULT_OUTPUT_DIR = os.path.join(EXPERIMENT_DIR, "outputs", "phase_0")


def load_jsonl(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def accuracy(correct: int, total: int) -> float:
    return round(correct / total, 4) if total else 0.0


def evaluate(
    dataset_path: str = DEFAULT_DATASET_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    phase: str = "phase_0",
) -> dict[str, Any]:
    dataset = load_jsonl(dataset_path)
    total = len(dataset)
    prefix = f"v3_{phase}"
    prediction_path = os.path.join(output_dir, f"{prefix}_predictions.jsonl")
    error_path = os.path.join(output_dir, f"{prefix}_errors.json")
    metrics_path = os.path.join(output_dir, f"{prefix}_metrics.json")
    os.makedirs(output_dir, exist_ok=True)

    field_names = (
        "primary_subject",
        "intent",
        "target_slm",
        "need_clarification",
    )
    correct = defaultdict(int)
    core_exact = 0
    full_exact = 0
    secondary_exact = 0
    secondary_tp = 0
    secondary_fp = 0
    secondary_fn = 0
    total_latency = 0.0
    errors = []
    case_stats: dict[str, dict[str, int]] = defaultdict(lambda: {
        "total_samples": 0,
        "primary_subject_correct": 0,
        "intent_correct": 0,
        "target_slm_correct": 0,
        "need_clarification_correct": 0,
        "core_exact_correct": 0,
        "full_exact_correct": 0,
    })

    with open(prediction_path, "w", encoding="utf-8") as pred_file:
        for item in dataset:
            started = time.perf_counter()
            prediction = route_question(
                question=item["question"],
                history=item.get("history", []),
            )
            total_latency += (time.perf_counter() - started) * 1000

            case_type = item.get("case_type", "unknown")
            stats = case_stats[case_type]
            stats["total_samples"] += 1
            wrong_fields = []

            for field in field_names:
                if prediction.get(field) == item.get(field):
                    correct[field] += 1
                    stats[f"{field}_correct"] += 1
                else:
                    wrong_fields.append(field)

            gold_secondary = set(item.get("secondary_subjects", []))
            predicted_secondary = set(prediction.get("secondary_subjects", []))
            secondary_tp += len(gold_secondary & predicted_secondary)
            secondary_fp += len(predicted_secondary - gold_secondary)
            secondary_fn += len(gold_secondary - predicted_secondary)

            if gold_secondary == predicted_secondary:
                secondary_exact += 1
            else:
                wrong_fields.append("secondary_subjects")

            is_core_exact = not any(field in wrong_fields for field in field_names)
            is_full_exact = not wrong_fields
            if is_core_exact:
                core_exact += 1
                stats["core_exact_correct"] += 1
            if is_full_exact:
                full_exact += 1
                stats["full_exact_correct"] += 1

            record = {
                "id": item.get("id"),
                "question": item["question"],
                "case_type": case_type,
                "gold": {field: item.get(field) for field in (*field_names, "secondary_subjects")},
                "prediction": prediction,
            }
            pred_file.write(json.dumps(record, ensure_ascii=False) + "\n")

            if wrong_fields:
                errors.append({**record, "wrong_fields": wrong_fields})

    precision = secondary_tp / (secondary_tp + secondary_fp) if secondary_tp + secondary_fp else 0.0
    recall = secondary_tp / (secondary_tp + secondary_fn) if secondary_tp + secondary_fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    metrics_by_case_type = {}
    for case_type, stats in case_stats.items():
        denominator = stats["total_samples"]
        metrics_by_case_type[case_type] = {
            "total_samples": denominator,
            "primary_subject_accuracy": accuracy(stats["primary_subject_correct"], denominator),
            "intent_accuracy": accuracy(stats["intent_correct"], denominator),
            "target_slm_accuracy": accuracy(stats["target_slm_correct"], denominator),
            "need_clarification_accuracy": accuracy(stats["need_clarification_correct"], denominator),
            "exact_match_accuracy": accuracy(stats["core_exact_correct"], denominator),
            "full_exact_match_accuracy": accuracy(stats["full_exact_correct"], denominator),
        }

    metrics = {
        "phase": phase,
        "total_samples": total,
        "primary_subject_accuracy": accuracy(correct["primary_subject"], total),
        "intent_accuracy": accuracy(correct["intent"], total),
        "target_slm_accuracy": accuracy(correct["target_slm"], total),
        "need_clarification_accuracy": accuracy(correct["need_clarification"], total),
        # Legacy exact match intentionally excludes secondary_subjects.
        "exact_match_accuracy": accuracy(core_exact, total),
        "full_exact_match_accuracy": accuracy(full_exact, total),
        "secondary_subject_exact_set_accuracy": accuracy(secondary_exact, total),
        "secondary_subject_micro_precision": round(precision, 4),
        "secondary_subject_micro_recall": round(recall, 4),
        "secondary_subject_micro_f1": round(f1, 4),
        "total_errors": total - core_exact,
        "full_total_errors": total - full_exact,
        "average_latency_ms": round(total_latency / total, 4) if total else 0.0,
        "metrics_by_case_type": metrics_by_case_type,
    }

    save_json(error_path, errors)
    save_json(metrics_path, metrics)

    print("===== RULE-BASED ROUTER V3 EVALUATION =====")
    for key in (
        "total_samples",
        "primary_subject_accuracy",
        "intent_accuracy",
        "target_slm_accuracy",
        "need_clarification_accuracy",
        "exact_match_accuracy",
        "full_exact_match_accuracy",
        "secondary_subject_micro_f1",
        "total_errors",
        "full_total_errors",
    ):
        print(f"{key}: {metrics[key]}")
    print(f"outputs: {output_dir}")
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", default="phase_0")
    parser.add_argument("--dataset", default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_dir = args.output_dir or os.path.join(EXPERIMENT_DIR, "outputs", args.phase)
    evaluate(args.dataset, output_dir, args.phase)
