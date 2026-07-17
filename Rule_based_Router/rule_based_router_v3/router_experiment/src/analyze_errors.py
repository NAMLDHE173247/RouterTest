"""Analyze a Rule-based Router V3 phase error file."""

import argparse
import json
import os
import re
from collections import Counter, defaultdict


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_ERROR_PATH = os.path.join(
    EXPERIMENT_DIR, "outputs", "phase_0", "v3_phase_0_errors.json"
)


def load_errors(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def classify_primary_error(item: dict) -> str | None:
    gold = item["gold"].get("primary_subject")
    prediction = item["prediction"].get("primary_subject")
    if gold == prediction:
        return None
    question = item.get("question", "").lower()
    entities = re.findall(r"\b(?:co2|o2|h2|n2|h2o|nacl|naoh|hcl|caco3|nh4no3)\b", question)
    mixed_markers = ("cả", "liên quan", "hóa học và vật lý", "vật lý hay hóa")
    formula_markers = ("=", "công thức", "phương trình", "mol", "pH", "nồng độ")
    if entities and prediction == "chemistry" and gold == "physics":
        return "entity_dominance_over_physics"
    if any(marker in question for marker in mixed_markers):
        return "interdisciplinary_topic_competition"
    if prediction == "unknown" and entities:
        return "entity_only_or_missing_topic_evidence"
    if prediction == "unknown" and any(marker in question for marker in formula_markers):
        return "formula_or_unit_not_covered"
    if prediction == "unknown":
        return "weak_or_missing_topic_evidence"
    return "wrong_topic_or_subject_competition"


def analyze(error_path: str = DEFAULT_ERROR_PATH):
    errors = load_errors(error_path)
    case_type_counter = Counter()
    field_error_counter = Counter()
    subject_confusion = Counter()
    intent_confusion = Counter()
    target_confusion = Counter()
    examples_by_case = defaultdict(list)
    primary_error_taxonomy = Counter()
    taxonomy_examples = defaultdict(list)

    for item in errors:
        case_type = item.get("case_type", "unknown_case")
        case_type_counter[case_type] += 1
        gold = item["gold"]
        pred = item["prediction"]
        cause = classify_primary_error(item)
        if cause:
            primary_error_taxonomy[cause] += 1
            if len(taxonomy_examples[cause]) < 5:
                taxonomy_examples[cause].append({"id": item.get("id"), "question": item.get("question"), "gold": gold.get("primary_subject"), "predicted": pred.get("primary_subject")})

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
        "primary_error_taxonomy": [
            {"cause": cause, "count": count, "examples": taxonomy_examples[cause]}
            for cause, count in primary_error_taxonomy.most_common()
        ],
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--errors", default=DEFAULT_ERROR_PATH)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = analyze(args.errors)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
