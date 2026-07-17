# Rule V3 Phase 1.1 Report — Subject Resolver Hardening

## Scope

Phase 1.1 hardens only Rule-based Router V3 subject resolution and evaluation. Intent rules were not changed. Phase 2 has not started.

## Primary accuracy trước/sau

On the same 300-sample dataset:

- Phase 0: `0.7667` primary accuracy, `70` primary errors.
- Phase 1: `0.8800` primary accuracy, `36` primary errors.
- Phase 1.1: `0.9200` primary accuracy, `24` primary errors.

Phase 1.1 improves primary accuracy by `+0.0400` absolute over Phase 1 and `+0.1533` over Phase 0.

## Accuracy theo subject

- Math: `1.0000` (`60/60`).
- Physics: `0.9024` (`74/82`).
- Chemistry: `0.8400` (`84/100`).

The remaining subject errors are concentrated in interdisciplinary Chemistry–Physics cases.

## Chemistry → Physics

Chemistry→Physics errors decreased from `12` in Phase 1 to `10` in Phase 1.1. The resolver now gives contextual Chemistry phrases priority without allowing standalone CO2/O2/H2/HCl entities to own a subject.

## Changes implemented

- Evidence is aggregated at subject level, so independent support terms from different topics can combine; one support term alone remains below threshold.
- `tan` and `nghiệm` use negative context guards for water/solubility and experiment contexts.
- Entity evidence is zero-weight alone, with explicit contextual rules for CO2–limewater, gas identification, HCl–metal and NaCl–water.
- Physics gas ownership now requires gas-law context; Chemistry reaction, solution, preparation and identification context is explicit.
- Tie-breaks use contextual phrase, phrase length, formula count, independent evidence count and score. Exact ties return unknown rather than relying on topic declaration order.
- Important terms and patterns receive distinct rule IDs; trace contains topic and matched rule IDs.
- Phase 0 test compares V2 with the immutable frozen artifact. A mutation test proves that changing that artifact fails the assertion.

## Fixed và regressions so với Phase 1

- Fixed primary errors: `16`.
- New primary regressions: `4`.
- Phase 1.1 comparison uses `outputs/phase_1/v3_phase_1_predictions.jsonl` as the baseline, recorded in `v3_phase_1_1_comparison_with_phase_1.json` with `baseline_phase: phase_1`.

## Kết quả từng near-miss group

The dedicated Phase 1.1 test suite passes all groups:

- Ambiguous `tan`: does not create a Math trigonometry match in “tan được trong nước”, “chất tan” or solution context.
- Ambiguous `nghiệm`: does not create Math equation support for “thí nghiệm” or “thực nghiệm”.
- Entity-only: CO2, H2, HCl and “khí hidro bay lên” remain unknown without domain context.
- Chemistry entity context: CO2–limewater, gas identification, HCl–metal and NaCl–water resolve to Chemistry.
- Physics gas context: CO2 with `PV=nRT` resolves to Physics; standalone gas entities do not.
- Independent support and required regressions: q046, q069, q075, q093, q136, q138, q143, q146 and q192 all resolve to their gold subject.
- True tie: synthetic equal evidence returns unknown instead of selecting by insertion order.

## Latency

- Average: `2.4872 ms`.
- P95: `3.3344 ms`.

## Tests

Command:

```text
python -m pytest backend/tests/test_phase0_hardening.py backend/tests/test_rule_v3_phase1_subject_resolution.py -q
```

Result: `30 passed` (6 framework/deprecation warnings). This is the historical Phase 1.1 count before the five Phase 1.2 invariant tests were added. The current focused command and `python -m pytest backend/tests -q` both report `35 passed`.

## Artifacts

`Rule_based_Router/rule_based_router_v3/router_experiment/outputs/phase_1_1/` contains predictions, errors, metrics, subject confusion matrix, fixed errors, regressions, comparison with Phase 1 and rule coverage.

## Commit provenance

- Code and resolver hardening commit: `806c914`.
- Evaluation baseline-selection/evaluation commit: `e8f0b33`.
- Report commit: committed separately after the final artifacts; the exact hash is the commit containing this file.

Each Phase 1.1 artifact records the evaluation commit, dataset SHA256, config SHA256, UTC generation time and phase label. The corrected Phase 1 report now records `70` Phase 0 primary errors.

## Phase gate decision

Phase 1.1 is ready for approval with fixes completed: primary accuracy improved to `0.9200`, the required near-miss/regression tests pass, and comparison against Phase 1 is reproducible. Do not start Phase 2 until this Phase 1.1 result is approved.
