"""Build pre-change Phase 4 error taxonomies from a frozen evaluation."""

import argparse
import json
from collections import Counter, defaultdict


def load(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def add(bucket, cause, item):
    bucket[cause]["count"] += 1
    if len(bucket[cause]["examples"]) < 5:
        bucket[cause]["examples"].append({
            "id": item.get("id"),
            "question": item.get("question"),
            "gold": item.get("gold"),
            "predicted": item.get("prediction"),
        })


def finalize(bucket):
    return [
        {"cause": cause, **value}
        for cause, value in sorted(bucket.items(), key=lambda pair: pair[1]["count"], reverse=True)
    ]


def analyze(errors):
    interdisciplinary = defaultdict(lambda: {"count": 0, "examples": []})
    secondary = defaultdict(lambda: {"count": 0, "examples": []})
    oos = defaultdict(lambda: {"count": 0, "examples": []})
    clarification = defaultdict(lambda: {"count": 0, "examples": []})

    for item in errors:
        gold = item.get("gold", {})
        pred = item.get("prediction", {})
        wrong = set(item.get("wrong_fields", []))
        case_type = item.get("case_type")
        if case_type == "interdisciplinary" or "primary_subject" in wrong or "secondary_subjects" in wrong:
            if "primary_subject" in wrong:
                add(interdisciplinary, "primary_subject_misresolution", item)
            if "secondary_subjects" in wrong:
                gold_secondary = set(gold.get("secondary_subjects", []))
                pred_secondary = set(pred.get("secondary_subjects", []))
                if gold_secondary - pred_secondary:
                    add(interdisciplinary, "missing_secondary_subject_evidence", item)
                if pred_secondary - gold_secondary:
                    add(interdisciplinary, "spurious_secondary_subject_evidence", item)
                if gold_secondary - pred_secondary:
                    add(secondary, "secondary_recall_missing", item)
                if pred_secondary - gold_secondary:
                    add(secondary, "secondary_entity_or_weak_evidence_false_positive", item)
        if case_type == "out_of_scope":
            if "target_slm" in wrong:
                add(oos, "oos_target_misclassification", item)
            if "need_clarification" in wrong:
                add(oos, "oos_clarification_misclassification", item)
            if "intent" in wrong:
                add(oos, "oos_intent_misclassification", item)
        if "need_clarification" in wrong or gold.get("need_clarification"):
            if "need_clarification" in wrong:
                add(clarification, "clarification_boolean_mismatch", item)
            if gold.get("need_clarification") and pred.get("need_clarification"):
                add(clarification, "clarification_true_case", item)

    return {
        "interdisciplinary": finalize(interdisciplinary),
        "secondary": finalize(secondary),
        "oos": finalize(oos),
        "clarification": finalize(clarification),
        "source_error_count": len(errors),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--errors", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = analyze(load(args.errors))
    names = {
        "interdisciplinary": "v3_phase_4_interdisciplinary_error_taxonomy.json",
        "oos": "v3_phase_4_oos_error_taxonomy.json",
        "clarification": "v3_phase_4_clarification_error_taxonomy.json",
    }
    for key, name in names.items():
        with open(f"{args.output_dir}/{name}", "w", encoding="utf-8") as file:
            json.dump({"phase": "phase_4", "baseline_phase": "phase_3", "items": result[key]}, file, ensure_ascii=False, indent=2)
    with open(f"{args.output_dir}/v3_phase_4_secondary_error_taxonomy.json", "w", encoding="utf-8") as file:
        json.dump({"phase": "phase_4", "baseline_phase": "phase_3", "items": result["secondary"]}, file, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=True, indent=2))
