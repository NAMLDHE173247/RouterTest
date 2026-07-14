# evaluate_rule_router.py

import json
import os
import sys
from rule_router import route_question

sys.stdout.reconfigure(encoding="utf-8")


DATASET_PATH = "data/test_router.jsonl"
OUTPUT_DIR = "outputs"

PREDICTION_PATH = os.path.join(OUTPUT_DIR, "rule_router_predictions.jsonl")
ERROR_PATH = os.path.join(OUTPUT_DIR, "rule_router_errors.json")
METRICS_PATH = os.path.join(OUTPUT_DIR, "rule_router_metrics.json")


def load_jsonl(path):
    data = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                data.append(json.loads(line))

    return data


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def evaluate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dataset = load_jsonl(DATASET_PATH)
    total = len(dataset)

    correct_subject = 0
    correct_intent = 0
    correct_target_slm = 0
    correct_need_clarification = 0
    exact_match = 0

    errors = []

    with open(PREDICTION_PATH, "w", encoding="utf-8") as pred_file:
        for item in dataset:
            prediction = route_question(
                question=item["question"],
                history=item.get("history", [])
            )

            subject_ok = prediction["primary_subject"] == item["primary_subject"]
            intent_ok = prediction["intent"] == item["intent"]
            target_ok = prediction["target_slm"] == item["target_slm"]
            clarify_ok = prediction["need_clarification"] == item["need_clarification"]

            if subject_ok:
                correct_subject += 1

            if intent_ok:
                correct_intent += 1

            if target_ok:
                correct_target_slm += 1

            if clarify_ok:
                correct_need_clarification += 1

            if subject_ok and intent_ok and target_ok and clarify_ok:
                exact_match += 1
            else:
                errors.append({
                    "id": item.get("id"),
                    "question": item["question"],
                    "case_type": item.get("case_type"),
                    "gold": {
                        "primary_subject": item["primary_subject"],
                        "secondary_subjects": item.get("secondary_subjects", []),
                        "intent": item["intent"],
                        "target_slm": item["target_slm"],
                        "need_clarification": item["need_clarification"]
                    },
                    "prediction": prediction
                })

            record = {
                "id": item.get("id"),
                "question": item["question"],
                "gold": {
                    "primary_subject": item["primary_subject"],
                    "intent": item["intent"],
                    "target_slm": item["target_slm"],
                    "need_clarification": item["need_clarification"]
                },
                "prediction": prediction
            }

            pred_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    metrics = {
        "total_samples": total,
        "primary_subject_accuracy": round(correct_subject / total, 4),
        "intent_accuracy": round(correct_intent / total, 4),
        "target_slm_accuracy": round(correct_target_slm / total, 4),
        "need_clarification_accuracy": round(correct_need_clarification / total, 4),
        "exact_match_accuracy": round(exact_match / total, 4),
        "total_errors": len(errors)
    }

    save_json(ERROR_PATH, errors)
    save_json(METRICS_PATH, metrics)

    print("===== RULE-BASED ROUTER EVALUATION =====")
    print(f"Total samples            (Tổng số mẫu)                  : {metrics['total_samples']}")
    print(f"Primary subject accuracy (Độ chính xác nhận diện môn)   : {metrics['primary_subject_accuracy']}")
    print(f"Intent accuracy          (Độ chính xác nhận diện ý định) : {metrics['intent_accuracy']}")
    print(f"Target SLM accuracy      (Độ chính xác chọn mô hình)     : {metrics['target_slm_accuracy']}")
    print(f"Need clarification acc.  (Độ chính xác cần làm rõ)       : {metrics['need_clarification_accuracy']}")
    print(f"Exact match accuracy     (Độ chính xác khớp hoàn toàn)   : {metrics['exact_match_accuracy']}")
    print(f"Total errors             (Tổng số dự đoán sai)           : {metrics['total_errors']} / {metrics['total_samples']}")


if __name__ == "__main__":
    evaluate()
