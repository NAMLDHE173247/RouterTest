"""Bounded Phase 5 threshold search over development and validation only."""

import argparse
import itertools
import json
import os
from collections import defaultdict

import rules
from rule_router import route_question


SEARCH_SPACE = {
    "secondary_score_ratio": [0.30, 0.35, 0.45],
    "ambiguous_min_score": [4],
    "out_of_scope_min_score": [5],
    "out_of_scope_max_stem_score": [2],
    "cross_domain_max_margin": [1],
}


def load(path):
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def metric(rows):
    total = len(rows)
    correct = defaultdict(int)
    tp = fp = fn = full = 0
    by_case = defaultdict(lambda: [0, 0])
    for item in rows:
        gold = item
        pred = route_question(item["question"], item.get("history", []))
        for field in ("primary_subject", "intent", "target_slm", "need_clarification"):
            correct[field] += pred.get(field) == gold.get(field)
        gs = set(gold.get("secondary_subjects", []))
        ps = set(pred.get("secondary_subjects", []))
        tp += len(gs & ps)
        fp += len(ps - gs)
        fn += len(gs - ps)
        full += all(pred.get(field) == gold.get(field) for field in ("primary_subject", "intent", "target_slm", "need_clarification")) and gs == ps
        case = gold.get("case_type", "unknown")
        by_case[case][0] += 1
        by_case[case][1] += pred.get("primary_subject") == gold.get("primary_subject")
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {
        "samples": total,
        "primary": round(correct["primary_subject"] / total, 4),
        "intent": round(correct["intent"] / total, 4),
        "target": round(correct["target_slm"] / total, 4),
        "clarification": round(correct["need_clarification"] / total, 4),
        "secondary_precision": round(precision, 4),
        "secondary_recall": round(recall, 4),
        "secondary_f1": round(f1, 4),
        "full_exact": round(full / total, 4),
        "by_case_primary": {case: round(values[1] / values[0], 4) for case, values in by_case.items()},
    }


def objective(dev, validation):
    return round(
        0.22 * dev["primary"]
        + 0.18 * dev["intent"]
        + 0.14 * dev["target"]
        + 0.14 * dev["clarification"]
        + 0.16 * dev["secondary_f1"]
        + 0.06 * dev["full_exact"]
        + 0.05 * validation["primary"]
        + 0.05 * validation["secondary_f1"],
        6,
    )


def main(dev_path, validation_path, output_path):
    dev = load(dev_path)
    validation = load(validation_path)
    defaults = dict(rules.THRESHOLDS)
    results = []
    keys = list(SEARCH_SPACE)
    for values in itertools.product(*(SEARCH_SPACE[key] for key in keys)):
        candidate = dict(zip(keys, values))
        rules.THRESHOLDS.update(candidate)
        dev_metrics = metric(dev)
        validation_metrics = metric(validation)
        constraints = {
            "development_primary": dev_metrics["primary"] >= 0.95,
            "development_intent": dev_metrics["intent"] >= 0.87,
            "development_target": dev_metrics["target"] >= 0.93,
            "development_clarification": dev_metrics["clarification"] >= 0.95,
            "development_secondary_f1": dev_metrics["secondary_f1"] >= 0.75,
        }
        results.append({
            "config": candidate,
            "development": dev_metrics,
            "validation": validation_metrics,
            "objective": objective(dev_metrics, validation_metrics),
            "constraints": constraints,
            "feasible": all(constraints.values()),
        })
    rules.THRESHOLDS.clear()
    rules.THRESHOLDS.update(defaults)
    results.sort(key=lambda item: (item["feasible"], item["objective"]), reverse=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump({
            "phase": "phase_5",
            "search_space": SEARCH_SPACE,
            "trials": len(results),
            "selection_policy": "highest constrained objective; holdout not loaded",
            "top_configurations": results[:10],
        }, file, ensure_ascii=False, indent=2)
    print(json.dumps({"trials": len(results), "top": results[:3]}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--development", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    main(args.development, args.validation, args.output)
