"""Build Phase 5 split artifacts and measured confidence/calibration summaries."""

import argparse
import json
import math
import os
import shutil
from collections import Counter


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "phase_5")


def load_jsonl(path):
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def dump(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)


def copy_eval(split, source):
    names = {
        "metrics": "metrics.json",
        "predictions": "predictions.jsonl",
        "errors": "errors.json",
    }
    for kind, suffix in names.items():
        src = os.path.join(source, f"v3_phase_5_{split}_{kind}.{ 'jsonl' if kind == 'predictions' else 'json'}")
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(OUT, f"v3_phase_5_{split}_{suffix}"))


def confidence_report(prediction_path):
    rows = load_jsonl(prediction_path)
    ranges = [(0.0, 0.5, "<0.50"), (0.5, 0.6, "0.50-0.59"),
              (0.6, 0.7, "0.60-0.69"), (0.7, 0.8, "0.70-0.79"),
              (0.8, 0.9, "0.80-0.89"), (0.9, 1.01, ">=0.90")]
    buckets = []
    for low, high, label in ranges:
        selected = [r for r in rows if low <= float(r.get("prediction", {}).get("confidence", 0.0)) < high]
        entry = {"bucket": label, "count": len(selected)}
        if selected:
            confidence = [float(r["prediction"].get("confidence", 0.0)) for r in selected]
            entry["mean_confidence"] = round(sum(confidence) / len(confidence), 4)
            for field, output in (("primary_subject", "primary_accuracy"),
                                  ("intent", "intent_accuracy"),
                                  ("target_slm", "target_accuracy"),
                                  ("need_clarification", "clarification_accuracy")):
                entry[output] = round(sum(r["prediction"].get(field) == r["gold"].get(field) for r in selected) / len(selected), 4)
        buckets.append(entry)
    def ece(field, confidence_field="confidence"):
        total = len(rows) or 1
        value = 0.0
        for bucket in buckets:
            if not bucket["count"]:
                continue
            value += bucket["count"] / total * abs(bucket["mean_confidence"] - bucket[field])
        return round(value, 4)
    return {
        "sample_count": len(rows),
        "buckets": buckets,
        "ece": {"primary": ece("primary_accuracy"), "intent": ece("intent_accuracy"),
                 "target": ece("target_accuracy"), "clarification": ece("clarification_accuracy")},
        "brier": {
            field: round(sum((float(r["prediction"].get("confidence", 0.0)) -
                              (r["prediction"].get(field) == r["gold"].get(field))) ** 2 for r in rows) / (len(rows) or 1), 4)
            for field in ("primary_subject", "intent", "target_slm", "need_clarification")
        },
        "calibration_claim": "not_calibrated; measured only; no post-hoc calibration was applied",
    }


def field_value(row, field):
    gold, pred = row["gold"], row["prediction"]
    if field == "secondary_subjects":
        return set(gold.get(field, [])), set(pred.get(field, []))
    if field == "legacy_exact":
        keys = ("primary_subject", "intent", "target_slm", "need_clarification")
        return all(gold.get(k) == pred.get(k) for k in keys), True
    if field == "full_exact":
        keys = ("primary_subject", "intent", "target_slm", "need_clarification")
        return all(gold.get(k) == pred.get(k) for k in keys) and set(gold.get("secondary_subjects", [])) == set(pred.get("secondary_subjects", [])), True
    return gold.get(field), pred.get(field)


def comparison(current_path, baseline_path):
    current = {r["id"]: r for r in load_jsonl(current_path)}
    baseline = {r["id"]: r for r in load_jsonl(baseline_path)}
    fields = ("primary_subject", "intent", "target_slm", "need_clarification", "secondary_subjects", "legacy_exact", "full_exact")
    result = {}
    for field in fields:
        fixed, regressions = [], []
        for key, row in current.items():
            if key not in baseline:
                continue
            cb = field_value(row, field)
            bb = field_value(baseline[key], field)
            current_ok = cb[0] == cb[1] if field not in ("legacy_exact", "full_exact") else cb[0]
            baseline_ok = bb[0] == bb[1] if field not in ("legacy_exact", "full_exact") else bb[0]
            if current_ok and not baseline_ok:
                fixed.append(key)
            if baseline_ok and not current_ok:
                regressions.append(key)
        result[field] = {"fixed": fixed, "regressions": regressions, "fixed_count": len(fixed), "regression_count": len(regressions)}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True)
    parser.add_argument("--eval-dir", required=True)
    parser.add_argument("--baseline-predictions")
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    copy_eval(args.split, args.eval_dir)
    pred = os.path.join(OUT, f"v3_phase_5_{args.split}_predictions.jsonl")
    if os.path.exists(pred):
        dump(os.path.join(OUT, f"v3_phase_5_{args.split}_confidence_buckets.json"), confidence_report(pred))
    if args.baseline_predictions and os.path.exists(args.baseline_predictions):
        dump(os.path.join(OUT, f"v3_phase_5_{args.split}_comparison_by_field.json"), comparison(pred, args.baseline_predictions))


if __name__ == "__main__":
    main()
