"""Create a pre-change taxonomy for Phase 2 intent errors."""

import argparse
import json
from collections import Counter, defaultdict


def load_errors(path: str):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def classify(item: dict) -> str:
    gold = item["gold"].get("intent")
    predicted = item["prediction"].get("intent")
    question = item.get("question", "").lower()

    if gold == "ask_follow_up":
        if predicted == "solve_problem":
            return "follow_up_overridden_by_solve"
        return "follow_up_context_not_detected"
    if gold in {"explain_concept", "solve_problem"} and predicted == "unknown":
        return "missing_strong_intent_phrase"
    if gold == "explain_concept" and predicted == "solve_problem":
        return "explain_vs_solve_weak_token_collision"
    if gold == "solve_problem" and predicted == "explain_concept":
        return "solve_vs_explain_phrase_collision"
    if gold == "give_hint" and predicted in {"unknown", "solve_problem"}:
        return "hint_phrase_missing_or_solve_not_vetoed"
    if gold in {"diagnose_error", "check_answer"} and predicted in {"diagnose_error", "check_answer"}:
        return "diagnose_vs_check_answer_collision"
    if gold == "diagnose_error" and predicted == "unknown":
        return "diagnose_phrase_missing"
    if gold == "check_answer" and predicted == "unknown":
        return "check_answer_phrase_missing"
    if gold == "unknown" and predicted != "unknown":
        return "false_positive_intent_or_oos_veto_gap"
    if "công sai" in question:
        return "keyword_sai_collision_in_công_sai"
    return "other_context_or_priority_error"


def analyze(error_path: str):
    errors = load_errors(error_path)
    counts = Counter()
    examples = defaultdict(list)
    by_pair = Counter()
    by_case_type = Counter()
    for item in errors:
        if "intent" not in item.get("wrong_fields", []):
            continue
        cause = classify(item)
        gold = item["gold"].get("intent")
        predicted = item["prediction"].get("intent")
        counts[cause] += 1
        by_pair[(gold, predicted)] += 1
        by_case_type[item.get("case_type", "unknown")] += 1
        if len(examples[cause]) < 5:
            examples[cause].append({
                "id": item.get("id"),
                "question": item.get("question"),
                "gold": gold,
                "predicted": predicted,
            })
    return {
        "error_count": sum(counts.values()),
        "causes": [
            {"cause": cause, "count": count, "examples": examples[cause]}
            for cause, count in counts.most_common()
        ],
        "confusion_pairs": [
            {"gold": gold, "predicted": predicted, "count": count}
            for (gold, predicted), count in by_pair.most_common()
        ],
        "errors_by_case_type": dict(by_case_type),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--errors", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = analyze(args.errors)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=True, indent=2))
