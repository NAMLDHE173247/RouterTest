"""Write final-config, adversarial and per-field Phase 5 artifacts."""

import argparse
import hashlib
import json
import os
import subprocess

from rule_router import route_question
from phase5_artifacts import comparison, dump


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "phase_5")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--development", required=True)
    parser.add_argument("--validation", required=True)
    args = parser.parse_args()
    dump(os.path.join(OUT, "v3_phase_5_final_config.json"), {
        "selected": {"secondary_score_ratio": 0.30, "ambiguous_min_score": 4,
                      "out_of_scope_min_score": 5, "out_of_scope_max_stem_score": 2,
                      "cross_domain_max_margin": 1},
        "semantic_fixed": {"minimum_subject_score": 2, "history_inherit_max_score": 3,
                            "domain_owner_min_score": 4, "domain_owner_math_ratio": 0.55},
        "selection_reason": "All three bounded feasible configurations had identical development and validation metrics; selected the lowest secondary ratio as the least restrictive valid candidate.",
        "holdout_policy": "Lock before one final holdout run; no tuning or rule changes after holdout.",
        "config_sha256": sha256(os.path.join(ROOT, "src", "threshold_config.py")),
    })
    dump(os.path.join(OUT, "v3_phase_5_comparison_by_field.json"), comparison(args.development, args.baseline))
    cases = [
        ("multimeaning_tan", "Tính tan 30 độ trong lượng giác", "math"),
        ("reverse_negation_hint", "Không cần gợi ý, hãy giải bài rơi tự do", "solve_problem"),
        ("entity_only", "CO2", "unknown"),
        ("stem_oos", "Tính pH của dung dịch HCl", "CONFIRMED_STEM"),
        ("oos", "Thời tiết hôm nay có mưa không?", "CONFIRMED_OUT_OF_SCOPE"),
        ("interdisciplinary", "Tính áp suất khí CO2 theo PV=nRT trong bình kín", "physics"),
        ("missing_history", "Còn cách khác không?", True),
    ]
    results = []
    for case_id, question, expected in cases:
        prediction = route_question(question, [])
        actual = prediction.get("intent") if case_id == "reverse_negation_hint" else prediction.get("primary_subject")
        if case_id in ("stem_oos", "oos"):
            actual = prediction.get("trace", {}).get("scope", {}).get("scope_state")
        if case_id == "missing_history":
            actual = prediction.get("need_clarification")
        results.append({"id": case_id, "question": question, "expected": expected, "actual": actual,
                        "pass": actual == expected, "trace": prediction.get("trace", {})})
    dump(os.path.join(OUT, "v3_phase_5_adversarial_results.json"), {"total": len(results), "passed": sum(r["pass"] for r in results), "cases": results})


if __name__ == "__main__":
    main()
