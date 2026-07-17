# Rule V3 Phase 1.2 Report — Subject Decision Consistency

## Scope và non-scope

Phase 1.2 changes only the V3 subject decision stage after `subject_scores` are produced. It does not expand the taxonomy and does not modify intent rules. Phase 2 has not started.

## Decision flow hardened

The resolver now aggregates subject evidence, selects the highest-scoring subject by default, applies tie logic only for equal scores (with configurable `NEAR_TIE_MARGIN = 1`), and applies only explicit ownership overrides for known contextual patterns. A near-tie cannot silently invert the score winner. Score gaps such as `9–4`, `7–4` and `6–3` remain owned by the score winner unless an explicit ownership rule is matched.

## Explicit ownership override contract

Every override contains `rule_id`, `reason`, `score_winner`, `score_winner_score`, `final_winner`, `final_winner_score`, `decision_margin` and `override_score_delta`. The trace field is `trace.ownership_override`.

Required cases:

- q213 → Chemistry: combustion stoichiometry.
- q229 → Chemistry: combustion stoichiometry.
- q240 → Physics: heat/phase-change calculation.
- q249 → Physics: electrical potential comparison.

Additional explicit contexts preserve prior behavior for buoyancy gas questions, fuel combustion energy, gas work/piston questions and chemical dissolution heat.

## Kết quả 300 samples

| Metric | Phase 1 | Phase 1.1 | Phase 1.2 |
|---|---:|---:|---:|
| Primary accuracy | 0.8800 | 0.9200 | 0.9400 |
| Target accuracy | 0.7933 | 0.8300 | 0.8433 |
| Intent accuracy | 0.7000 | 0.7000 | 0.7000 |
| Primary errors | 36 | 24 | 18 |

Accuracy by gold subject: Math `1.0000` (`60/60`), Physics `0.9512` (`78/82`), Chemistry `0.8600` (`86/100`).

Confusion matrix errors: Chemistry→Physics `9`, Chemistry→unknown `5`, Physics→unknown `2`, Physics→Chemistry `2`.

## Comparison với Phase 1 và Phase 1.1

- Compared with Phase 1.1: fixed `6`, new regressions `0`.
- Compared with Phase 1: fixed `18`, new regressions `0`.
- Chemistry→Physics: `9` in Phase 1.2, versus `10` in Phase 1.1 and `12` in Phase 1.
- Intent remains exactly `0.7000`; no intent rule was changed.

The comparison artifacts are `v3_phase_1_2_comparison_with_phase_1_1.json`, `v3_phase_1_2_fixed_errors_vs_phase_1_1.json`, `v3_phase_1_2_regressions_vs_phase_1_1.json`, and their `phase_1` counterparts.

## Invariant and regression tests

The dedicated subject-resolution suite verifies that no override means a unique score argmax is primary, override traces contain rule ID and reason, there is no silent winner inversion, equal evidence does not fall back to definition insertion order, and q213/q229/q240/q249 resolve to their required subjects.

Historical Phase 1.1 focused command result: `30 passed` before the five Phase 1.2 invariant tests were added. An intermediate full-backend run reported `35 passed` plus 6 legacy integration failures, before the final standalone-gas invariant correction. The final focused command reports `36 passed`:

```text
python -m pytest backend/tests/test_phase0_hardening.py backend/tests/test_rule_v3_phase1_subject_resolution.py -q
```

Current focused result: `36 passed`, with 6 existing framework/deprecation warnings. The legacy integration tests require a server at `127.0.0.1:8000`; they were not part of the subject-resolution gate. V3 source compilation and `git diff --check` passed.

## Latency

Measured by the final 300-sample evaluation run using the bundled Codex Python runtime on the local Windows workspace:

- Mean: `2.6088 ms`
- Median: `2.2991 ms`
- P95: `3.9574 ms`

These values are stored in `v3_phase_1_2_metrics.json`.

## Artifacts

All requested Phase 1.2 artifacts are under `Rule_based_Router/rule_based_router_v3/router_experiment/outputs/phase_1_2/`: predictions, errors, metrics, subject confusion, fixed errors, regressions, comparisons with Phase 1 and Phase 1.1, and rule coverage.

## Reproducibility and commit provenance

- Code commit used by the final evaluation: `7fb5bbc`.
- Evaluation metadata commit: `7fb5bbc`; dataset SHA256, config SHA256, UTC timestamp and phase are embedded in every artifact.
- Report commit: the separate commit containing this report.

## Phase gate decision

Phase 1.2 passes the requested gate: primary accuracy is above 92%, all four required regressions are fixed, new regressions are 0, and intent remains 70%. This result is ready for final approval. Do not start Phase 2 until approval is given.
