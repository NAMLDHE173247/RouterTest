# analyze_errors.py

import json
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

ERROR_PATH = "outputs/v2_rule_router_errors.json"


def load_errors(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze():
    errors = load_errors(ERROR_PATH)

    case_type_counter = Counter()
    field_error_counter = Counter()
    subject_confusion = Counter()
    intent_confusion = Counter()
    target_confusion = Counter()

    examples_by_case = defaultdict(list)

    for item in errors:
        case_type = item.get("case_type", "unknown_case")
        case_type_counter[case_type] += 1

        gold = item["gold"]
        pred = item["prediction"]

        if gold["primary_subject"] != pred["primary_subject"]:
            field_error_counter["primary_subject"] += 1
            subject_confusion[
                (gold["primary_subject"], pred["primary_subject"])
            ] += 1

        if gold["intent"] != pred["intent"]:
            field_error_counter["intent"] += 1
            intent_confusion[
                (gold["intent"], pred["intent"])
            ] += 1

        if gold["target_slm"] != pred["target_slm"]:
            field_error_counter["target_slm"] += 1
            target_confusion[
                (gold["target_slm"], pred["target_slm"])
            ] += 1

        if gold["need_clarification"] != pred["need_clarification"]:
            field_error_counter["need_clarification"] += 1

        if len(examples_by_case[case_type]) < 5:
            examples_by_case[case_type].append(item)

    print("\n===== ERROR BY CASE TYPE (Lỗi theo loại câu hỏi) =====")
    for case_type, count in case_type_counter.most_common():
        print(f"  {case_type}: {count}")

    print("\n===== ERROR BY FIELD (Lỗi theo trường dự đoán) =====")
    for field, count in field_error_counter.most_common():
        print(f"  {field}: {count}")

    print("\n===== SUBJECT CONFUSION (Nhầm lẫn môn học) =====")
    for (gold, pred), count in subject_confusion.most_common(15):
        print(f"  {gold} → {pred}: {count}")

    print("\n===== INTENT CONFUSION (Nhầm lẫn ý định) =====")
    for (gold, pred), count in intent_confusion.most_common(15):
        print(f"  {gold} → {pred}: {count}")

    print("\n===== TARGET SLM CONFUSION (Nhầm lẫn mô hình đích) =====")
    for (gold, pred), count in target_confusion.most_common(15):
        print(f"  {gold} → {pred}: {count}")

    print("\n===== SAMPLE ERRORS BY CASE TYPE (Ví dụ lỗi theo từng loại) =====")
    for case_type, items in examples_by_case.items():
        print(f"\n--- {case_type} ---")
        for item in items:
            print(f"  ID  : {item.get('id')}")
            print(f"  Q   : {item['question']}")
            print(f"  Gold: {item['gold']}")
            print(f"  Pred: {item['prediction']}")
            print()


if __name__ == "__main__":
    analyze()
