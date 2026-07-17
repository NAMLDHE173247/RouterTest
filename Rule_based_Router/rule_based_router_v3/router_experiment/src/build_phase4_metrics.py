"""Create Phase 4 secondary and clarification reason coverage artifacts."""

import argparse
import json
from collections import Counter


def read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def read_jsonl(path):
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def main(output_dir):
    metrics_path = f"{output_dir}/v3_phase_4_metrics.json"
    predictions = read_jsonl(f"{output_dir}/v3_phase_4_predictions.jsonl")
    metrics = read_json(metrics_path)
    secondary_tp = secondary_fp = secondary_fn = 0
    gold_counts = Counter()
    pred_counts = Counter()
    reason_counts = Counter()
    for item in predictions:
        gold = set(item["gold"].get("secondary_subjects", []))
        predicted = set(item["prediction"].get("secondary_subjects", []))
        secondary_tp += len(gold & predicted)
        secondary_fp += len(predicted - gold)
        secondary_fn += len(gold - predicted)
        gold_counts.update(gold)
        pred_counts.update(predicted)
        if item["prediction"].get("need_clarification"):
            reason = item["prediction"].get("clarification_reason_code") or item["prediction"].get("trace", {}).get("clarification_reason_code")
            reason_counts[reason or "MISSING_REASON_CODE"] += 1
    precision = secondary_tp / (secondary_tp + secondary_fp) if secondary_tp + secondary_fp else 0.0
    recall = secondary_tp / (secondary_tp + secondary_fn) if secondary_tp + secondary_fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    with open(f"{output_dir}/v3_phase_4_secondary_metrics.json", "w", encoding="utf-8") as file:
        json.dump({
            "phase": "phase_4",
            "secondary_micro_precision": round(precision, 4),
            "secondary_micro_recall": round(recall, 4),
            "secondary_micro_f1": round(f1, 4),
            "true_positive": secondary_tp,
            "false_positive": secondary_fp,
            "false_negative": secondary_fn,
            "gold_counts": dict(gold_counts),
            "prediction_counts": dict(pred_counts),
        }, file, ensure_ascii=False, indent=2)
    with open(f"{output_dir}/v3_phase_4_reason_code_coverage.json", "w", encoding="utf-8") as file:
        json.dump({
            "phase": "phase_4",
            "clarifying_predictions": sum(reason_counts.values()),
            "reason_codes": dict(reason_counts),
            "missing_reason_code_count": reason_counts.get("MISSING_REASON_CODE", 0),
        }, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    main(args.output_dir)
