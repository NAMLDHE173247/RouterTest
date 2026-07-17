"""Central Phase 5 threshold policy.

Semantic thresholds are contract-like safety rules. Tunable thresholds are
the only values eligible for search; both groups retain the Phase 4 defaults.
"""

SEMANTIC_THRESHOLDS = {
    "minimum_subject_score": 2,
    "history_inherit_max_score": 3,
    "domain_owner_min_score": 4,
    "domain_owner_math_ratio": 0.55,
}

TUNABLE_THRESHOLDS = {
    "secondary_min_score": 2,
    "secondary_score_ratio": 0.35,
    "ambiguous_min_score": 4,
    "out_of_scope_min_score": 5,
    "out_of_scope_max_stem_score": 2,
    "cross_domain_min_score": 4,
    "cross_domain_max_margin": 1,
}

DEFAULT_THRESHOLDS = {**SEMANTIC_THRESHOLDS, **TUNABLE_THRESHOLDS}
