"""Evaluate Rule-based Router V3 and write phase-specific artifacts."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
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


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_files(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(os.path.basename(path).encode("utf-8"))
        with open(path, "rb") as file:
            digest.update(file.read())
    return digest.hexdigest()


def current_git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=EXPERIMENT_DIR,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def load_prediction_records(path: str) -> dict[str, dict[str, Any]]:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return {
            record["id"]: record
            for record in (json.loads(line) for line in file if line.strip())
        }


def accuracy(correct: int, total: int) -> float:
    return round(correct / total, 4) if total else 0.0


def percentile(values: list[float], percentile_rank: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(int(round((percentile_rank / 100) * (len(ordered) - 1))), len(ordered) - 1)
    return round(ordered[index], 4)


def evaluate(
    dataset_path: str = DEFAULT_DATASET_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    phase: str = "phase_0",
    baseline_dir: str | None = None,
    baseline_phase: str = "phase_0",
    additional_baseline_dir: str | None = None,
    additional_baseline_phase: str = "phase_0",
    comparison_field: str = "primary_subject",
    config_paths: list[str] | None = None,
) -> dict[str, Any]:
    dataset = load_jsonl(dataset_path)
    total = len(dataset)
    prefix = f"v3_{phase}"
    prediction_path = os.path.join(output_dir, f"{prefix}_predictions.jsonl")
    error_path = os.path.join(output_dir, f"{prefix}_errors.json")
    metrics_path = os.path.join(output_dir, f"{prefix}_metrics.json")
    confusion_path = os.path.join(output_dir, f"{prefix}_subject_confusion.json")
    intent_confusion_path = os.path.join(output_dir, f"{prefix}_intent_confusion.json")
    fixed_path = os.path.join(output_dir, f"{prefix}_fixed_errors.json")
    regressions_path = os.path.join(output_dir, f"{prefix}_regressions.json")
    comparison_path = os.path.join(output_dir, f"{prefix}_comparison_with_{baseline_phase}.json")
    coverage_path = os.path.join(output_dir, f"{prefix}_rule_coverage.json")
    os.makedirs(output_dir, exist_ok=True)

    config_paths = config_paths or [os.path.join(SCRIPT_DIR, "rules.py")]
    metadata = {
        "git_commit": current_git_commit(),
        "dataset_sha256": sha256_file(dataset_path),
        "config_sha256": sha256_files(config_paths),
        "config_files": [os.path.relpath(path, EXPERIMENT_DIR) for path in config_paths],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
    }

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
    latencies = []
    errors = []
    subject_confusion = Counter()
    intent_confusion = Counter()
    rule_coverage = Counter()
    subject_stats: dict[str, dict[str, int]] = defaultdict(lambda: {
        "total_samples": 0,
        "primary_subject_correct": 0,
    })
    intent_stats: dict[str, dict[str, int]] = defaultdict(lambda: {
        "total_samples": 0,
        "intent_correct": 0,
    })
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
            latency_ms = (time.perf_counter() - started) * 1000
            total_latency += latency_ms
            latencies.append(latency_ms)

            case_type = item.get("case_type", "unknown")
            stats = case_stats[case_type]
            stats["total_samples"] += 1
            gold_subject = item.get("primary_subject", "unknown")
            subject_stats[gold_subject]["total_samples"] += 1
            gold_intent = item.get("intent", "unknown")
            intent_stats[gold_intent]["total_samples"] += 1
            wrong_fields = []

            for field in field_names:
                if prediction.get(field) == item.get(field):
                    correct[field] += 1
                    stats[f"{field}_correct"] += 1
                    if field == "primary_subject":
                        subject_stats[gold_subject]["primary_subject_correct"] += 1
                    if field == "intent":
                        intent_stats[gold_intent]["intent_correct"] += 1
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
            trace_matches = list(prediction.get("trace", {}).get("rule_matches", []))
            trace_matches.extend(prediction.get("trace", {}).get("intent", {}).get("rule_matches", []))
            for match in trace_matches:
                rule_id = match.get("rule_id")
                if rule_id:
                    rule_coverage[rule_id] += 1
            pred_file.write(json.dumps(record, ensure_ascii=False) + "\n")

            if wrong_fields:
                errors.append({**record, "wrong_fields": wrong_fields})
            if prediction.get("primary_subject") != item.get("primary_subject"):
                subject_confusion[
                    (item.get("primary_subject"), prediction.get("primary_subject"))
                ] += 1
            if prediction.get("intent") != item.get("intent"):
                intent_confusion[
                    (item.get("intent"), prediction.get("intent"))
                ] += 1

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
        "metadata": metadata,
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
        "median_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "metrics_by_gold_subject": {
            subject: {
                "total_samples": stats["total_samples"],
                "primary_subject_accuracy": accuracy(
                    stats["primary_subject_correct"], stats["total_samples"]
                ),
            }
            for subject, stats in sorted(subject_stats.items())
        },
        "metrics_by_gold_intent": {
            intent: {
                "total_samples": stats["total_samples"],
                "intent_accuracy": accuracy(stats["intent_correct"], stats["total_samples"]),
            }
            for intent, stats in sorted(intent_stats.items())
        },
        "metrics_by_case_type": metrics_by_case_type,
    }

    save_json(error_path, errors)
    save_json(metrics_path, metrics)

    save_json(confusion_path, {
        "metadata": metadata,
        "items": [
            {"gold": gold, "predicted": predicted, "count": count}
            for (gold, predicted), count in subject_confusion.most_common()
        ],
    })
    save_json(intent_confusion_path, {
        "metadata": metadata,
        "items": [
            {"gold": gold, "predicted": predicted, "count": count}
            for (gold, predicted), count in intent_confusion.most_common()
        ],
    })

    baseline_dir = baseline_dir or os.path.join(EXPERIMENT_DIR, "outputs", "phase_0")
    baseline_records = load_prediction_records(
        os.path.join(baseline_dir, f"v3_{baseline_phase}_predictions.jsonl")
    )
    current_records = load_prediction_records(prediction_path)
    fixed_errors = []
    regressions = []
    comparison = {
        "metadata": metadata,
        "baseline_dir": baseline_dir,
        "baseline_phase": baseline_phase,
        "baseline_available": bool(baseline_records),
        f"fixed_{comparison_field}_errors": 0,
        f"new_{comparison_field}_regressions": 0,
        "comparison_field": comparison_field,
    }
    for sample_id, current in current_records.items():
        baseline = baseline_records.get(sample_id)
        if not baseline:
            continue
        gold_value = current["gold"].get(comparison_field)
        baseline_value = baseline["prediction"].get(comparison_field)
        current_value = current["prediction"].get(comparison_field)
        baseline_wrong = baseline_value != gold_value
        current_wrong = current_value != gold_value
        if baseline_wrong and not current_wrong:
            fixed_errors.append({"id": sample_id, "baseline": baseline, "current": current})
        elif not baseline_wrong and current_wrong:
            regressions.append({"id": sample_id, "baseline": baseline, "current": current})
    comparison[f"fixed_{comparison_field}_errors"] = len(fixed_errors)
    comparison[f"new_{comparison_field}_regressions"] = len(regressions)
    save_json(fixed_path, {"metadata": metadata, "items": fixed_errors})
    save_json(regressions_path, {"metadata": metadata, "items": regressions})
    save_json(comparison_path, comparison)
    if additional_baseline_dir:
        additional_records = load_prediction_records(
            os.path.join(additional_baseline_dir, f"v3_{additional_baseline_phase}_predictions.jsonl")
        )
        additional_fixed = []
        additional_regressions = []
        for sample_id, current in current_records.items():
            baseline = additional_records.get(sample_id)
            if not baseline:
                continue
            gold_value = current["gold"].get(comparison_field)
            baseline_wrong = baseline["prediction"].get(comparison_field) != gold_value
            current_wrong = current["prediction"].get(comparison_field) != gold_value
            if baseline_wrong and not current_wrong:
                additional_fixed.append({"id": sample_id, "baseline": baseline, "current": current})
            elif not baseline_wrong and current_wrong:
                additional_regressions.append({"id": sample_id, "baseline": baseline, "current": current})
        additional_prefix = f"{prefix}_comparison_with_{additional_baseline_phase}"
        save_json(os.path.join(output_dir, f"{prefix}_fixed_errors_vs_{additional_baseline_phase}.json"), {
            "metadata": metadata, "baseline_dir": additional_baseline_dir,
            "baseline_phase": additional_baseline_phase, "items": additional_fixed,
        })
        save_json(os.path.join(output_dir, f"{prefix}_regressions_vs_{additional_baseline_phase}.json"), {
            "metadata": metadata, "baseline_dir": additional_baseline_dir,
            "baseline_phase": additional_baseline_phase, "items": additional_regressions,
        })
        save_json(os.path.join(output_dir, f"{additional_prefix}.json"), {
            "metadata": metadata,
            "baseline_dir": additional_baseline_dir,
            "baseline_phase": additional_baseline_phase,
            "baseline_available": bool(additional_records),
            f"fixed_{comparison_field}_errors": len(additional_fixed),
            f"new_{comparison_field}_regressions": len(additional_regressions),
            "comparison_field": comparison_field,
        })
    save_json(coverage_path, {
        "metadata": metadata,
        "total_samples": total,
        "matched_rule_count": sum(rule_coverage.values()),
        "rules": dict(rule_coverage.most_common()),
    })

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
    parser.add_argument("--baseline-dir", default=None)
    parser.add_argument("--baseline-phase", default="phase_0")
    parser.add_argument("--additional-baseline-dir", default=None)
    parser.add_argument("--additional-baseline-phase", default="phase_0")
    parser.add_argument("--comparison-field", default="primary_subject")
    parser.add_argument("--config", action="append", default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_dir = args.output_dir or os.path.join(EXPERIMENT_DIR, "outputs", args.phase)
    config_paths = args.config or [os.path.join(SCRIPT_DIR, "rules.py")]
    evaluate(
        args.dataset, output_dir, args.phase, args.baseline_dir, args.baseline_phase,
        args.additional_baseline_dir, args.additional_baseline_phase, args.comparison_field, config_paths,
    )
