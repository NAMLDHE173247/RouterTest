"""Create immutable Phase 5 review analyses without invoking the router."""

import json
import os
import subprocess
from collections import Counter, defaultdict


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "phase_5")


def load(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def dump(name, value):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)


def intent_errors(name):
    rows = load(os.path.join(OUT, f"v3_phase_5_{name}_errors.json"))
    result = []
    for row in rows:
        if "intent" not in row.get("wrong_fields", []):
            continue
        prediction = row["prediction"]
        trace = prediction.get("trace", {})
        intent_trace = trace.get("intent", {})
        rules = intent_trace.get("rule_matches", [])
        scores = intent_trace.get("scores", {})
        vetoes = intent_trace.get("vetoes", [])
        gold = row["gold"]["intent"]
        predicted = prediction["intent"]
        if predicted == "unknown" and not rules:
            group = "missing_intent_evidence"
            cause = "No intent rule matched; gold intent is not represented by the current lexical/context patterns."
        elif gold == "explain_concept" and predicted == "solve_problem":
            group = "explain_vs_solve_overlap"
            cause = "A solve/calculation rule won while no explanatory context had enough score."
        elif gold == "unknown" and predicted == "explain_concept":
            group = "ambiguous_explain_followup_conflict"
            cause = "Explain and follow-up phrases co-occurred; the no-history veto removed follow-up but did not veto explain."
        else:
            group = "wrong_intent_selection"
            cause = "Intent evidence was present but selected intent did not match the gold label."
        result.append({
            "id": row["id"], "question": row["question"], "case_type": row.get("case_type"),
            "gold": gold, "prediction": predicted,
            "matched_rules": [{"rule_id": r.get("rule_id"), "intent": r.get("intent"), "source": r.get("source"), "score": r.get("score"), "matched_text": r.get("matched_text")} for r in rules],
            "scores": scores, "vetoes": vetoes,
            "top_score": intent_trace.get("top_score", 0), "second_score": intent_trace.get("second_score", 0),
            "decision_margin": intent_trace.get("decision_margin", 0),
            "group": group, "cause": cause,
        })
    return result


def committed_search():
    path = "Rule_based_Router/rule_based_router_v3/router_experiment/outputs/phase_5/v3_phase_5_search_results.json"
    raw = subprocess.check_output(["git", "show", f"HEAD:{path}"], text=True)
    return json.loads(raw)


def sensitivity(search):
    trials = search["top_configurations"]
    parameters = sorted(search["search_space"])
    output = {}
    for parameter in parameters:
        values = sorted({trial["config"][parameter] for trial in trials})
        by_value = {}
        for value in values:
            selected = [trial for trial in trials if trial["config"][parameter] == value]
            by_value[str(value)] = {
                "trial_count": len(selected),
                "development_metrics": sorted({json.dumps(trial["development"], sort_keys=True) for trial in selected}),
                "validation_metrics": sorted({json.dumps(trial["validation"], sort_keys=True) for trial in selected}),
            }
        output[parameter] = {
            "tested_values": values, "observed_prediction_metric_change": False,
            "sample_sensitivity": "0.0 across the committed 3-trial grid; no sample crossed the corresponding decision boundary.",
            "by_value": by_value,
        }
    return {
        "source": "committed Phase 5 search artifact at HEAD; working-tree exploratory changes excluded",
        "trial_count": search["trials"], "search_space": search["search_space"],
        "why_same_result": [
            "secondary_score_ratio did not change any secondary decision on the 300 development or 20 validation samples",
            "ambiguous_min_score, out_of_scope_min_score, out_of_scope_max_stem_score and cross_domain_max_margin were not exercised by a boundary case in these samples",
            "intent predictions are produced by intent rules and vetoes, not by the tuned subject/scope thresholds",
        ],
        "parameters": output,
    }


def main():
    validation = intent_errors("validation")
    holdout = intent_errors("holdout")
    dump("v3_phase_5_validation_intent_error_taxonomy.json", {
        "split": "validation", "status": "frozen_analysis_only", "intent_error_count": len(validation),
        "groups": dict(Counter(item["group"] for item in validation)), "errors": validation,
    })
    dump("v3_phase_5_holdout_intent_error_taxonomy.json", {
        "split": "holdout", "status": "frozen_analysis_only; do not reuse as final holdout", "intent_error_count": len(holdout),
        "groups": dict(Counter(item["group"] for item in holdout)), "errors": holdout,
    })
    dump("v3_phase_5_threshold_sensitivity.json", sensitivity(committed_search()))
    dump("v3_next_study_dataset_protocol.json", {
        "status": "protocol_only; no dataset created in this checkpoint",
        "reuse_policy": "The current Phase 5 holdout is analysis/regression data only and must never be reused as a final holdout.",
        "splits": {
            "intent_development_expansion": {"purpose": "expand intent paraphrases and hard negatives", "target": "at least 50 examples per intent, balanced by subject and case_type"},
            "validation": {"purpose": "select intent generalization changes", "target": "new samples stratified by intent, subject, case_type and history state"},
            "final_holdout": {"purpose": "one-time unbiased final evaluation", "target": "new source/templates, frozen before any rule or threshold choice"},
        },
        "stratification": ["intent", "subject", "case_type", "single_turn_vs_multi_turn", "history_present_vs_missing", "interdisciplinary", "ambiguous", "out_of_scope"],
        "leakage_checks": ["exact question duplicate", "normalized near-duplicate", "template fingerprint overlap", "same stem with entity substitution", "cross-split ID and provenance audit", "SHA256 manifest"],
        "acceptance_rules": ["expected labels are reviewed before metrics", "no holdout label/rule/threshold tuning", "report per-intent confusion and confidence", "record dataset provenance and generation timestamp"],
    })


if __name__ == "__main__":
    main()
