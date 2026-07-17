"""Analyze a Rule-based Router V3 phase error file."""

import argparse
import json
import os
from collections import Counter, defaultdict


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_ERROR_PATH = os.path.join(
    EXPERIMENT_DIR, "outputs", "phase_0", "v3_phase_0_errors.json"
)


def load_errors(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def analyze(error_path: str = DEFAULT_ERROR_PATH):
    errors = load_errors(error_path)
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

        for field, counter in (
            ("primary_subject", subject_confusion),
            ("intent", intent_confusion),
            ("target_slm", target_confusion),
        ):
            if gold.get(field) != pred.get(field):
                field_error_counter[field] += 1
                counter[(gold.get(field), pred.get(field))] += 1

        if gold.get("need_clarification") != pred.get("need_clarification"):
            field_error_counter["need_clarification"] += 1
        if set(gold.get("secondary_subjects", [])) != set(pred.get("secondary_subjects", [])):
            field_error_counter["secondary_subjects"] += 1

        if len(examples_by_case[case_type]) < 5:
            examples_by_case[case_type].append(item)

    result = {
        "error_count": len(errors),
        "errors_by_case_type": dict(case_type_counter),
        "errors_by_field": dict(field_error_counter),
        "subject_confusion": [
            {"gold": gold, "predicted": pred, "count": count}
            for (gold, pred), count in subject_confusion.most_common()
        ],
        "intent_confusion": [
            {"gold": gold, "predicted": pred, "count": count}
            for (gold, pred), count in intent_confusion.most_common()
        ],
        "target_confusion": [
            {"gold": gold, "predicted": pred, "count": count}
            for (gold, pred), count in target_confusion.most_common()
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--errors", default=DEFAULT_ERROR_PATH)
    analyze(parser.parse_args().errors)
