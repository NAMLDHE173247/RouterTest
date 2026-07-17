# Rule V3 Phase 1 Report

## Executive summary

Phase 1 adds a structured Subject → Branch → Topic → Concept taxonomy and a typed primary-subject resolver for Rule-based Router V3. Strong terms, support terms, formulas, units and entities are represented separately. Entity evidence has zero ownership weight, so a standalone chemical formula cannot select Chemistry.

On the frozen 300-case dataset, primary-subject accuracy increased from 0.7667 in the Phase 0 baseline to 0.8800. Target accuracy increased from 0.6800 to 0.7933, and clarification accuracy increased from 0.7600 to 0.8567. Phase 2 has not been started.

## Scope và non-scope

Scope: V3 core subject resolution, topic taxonomy, rule IDs, debug trace, evaluation metadata and Phase 1 artifacts.

Non-scope: V0/V1/V2 behavior, contextual intent, dialogue-history redesign, advanced OOS detection and advanced clarification.

## Baseline

Phase 0 artifacts are frozen under `outputs/phase_0/` and are not overwritten. The baseline has 300 samples, primary accuracy 0.7667, intent accuracy 0.7000, target accuracy 0.6800, clarification accuracy 0.7600, legacy exact accuracy 0.5133 and 146 legacy errors. Full exact accuracy, including secondary subjects, is 0.2400.

The Phase 0 primary-subject error set contains 68 errors. The pre-change taxonomy artifact groups them into weak/missing topic evidence (31), formula/unit coverage gaps (14), wrong topic or subject competition (13), entity dominance over Physics (10), and interdisciplinary competition (2).

## Error taxonomy trước khi sửa

The complete analysis is stored in `outputs/phase_1/v3_phase_0_error_taxonomy.json`. The largest group was weak or missing topic evidence. The most actionable repeated pattern was a chemistry entity such as CO2, O2 or H2 appearing in a Physics gas or buoyancy question; this was handled by separating entity matches from owning evidence.

## Rules/topics đã thêm

- Math: algebra, sequences, calculus, geometry, trigonometry, probability/statistics, complex numbers and exponential/logarithm concepts.
- Physics: motion, force, inertia, work/energy, ideal gas, heat transfer, circuits, electromagnetism, optics, waves and oscillation.
- Chemistry: atomic structure, bonds, reactions, stoichiometry, acids/bases, organic chemistry and electrochemistry.
- Each match produces a rule ID such as `subject.physics.thermodynamics.ideal_gas.strong_term`.
- Topic and matched rule IDs are present in `prediction.trace`; rule coverage is measured in `v3_phase_1_rule_coverage.json`.
- Strong/support/formula/unit/entity evidence is kept distinct. Entity matches have score zero and cannot own a subject.

## Kết quả tổng và theo từng subject/case type

Overall: primary 0.8800, intent 0.7000, target 0.7933, clarification 0.8567, legacy exact 0.5733, full exact 0.3267, secondary micro-F1 0.2011.

By case type, primary accuracy is 0.9286 for single-turn, 1.0000 for multi-turn, 0.6129 for interdisciplinary, 1.0000 for ambiguous and 1.0000 for out-of-scope cases. Interdisciplinary cases remain the main difficulty.

The Phase 1 subject confusion matrix contains 36 primary errors: Chemistry→Physics 12, Chemistry→unknown 11, Physics→unknown 6, Physics→Chemistry 6 and Chemistry→Math 1.

## Fixed errors

Compared with the frozen Phase 0 predictions, 60 primary-subject errors were fixed. Full per-sample records are in `v3_phase_1_fixed_errors.json`.

## Regressions

There are 26 new primary-subject regressions against Phase 0. Full records are in `v3_phase_1_regressions.json`. They are concentrated in interdisciplinary Chemistry–Physics examples and are retained for review rather than hidden by a V2-equality test.

## Net improvement

Primary accuracy improved by +0.1133 absolute, target accuracy by +0.1133, clarification accuracy by +0.0967, legacy exact accuracy by +0.0600 and full exact accuracy by +0.0867. Primary errors fell from 68 to 36. The result is an improvement on the Phase 0 baseline, with a known interdisciplinary regression surface.

## Test results

- `pytest backend/tests/test_phase0_hardening.py -q`: 8 passed.
- Python compilation for V3 source: passed.
- Evaluation dataset: 300 samples; Phase 1 artifacts generated successfully.
- Existing V0, V1 and V2 code paths were not changed.

## Limitations

The resolver is still lexical and rule-based. Interdisciplinary intent is represented only through subject scores and secondary subjects; it does not use dialogue history or contextual inference. The dataset is small and synthetic, and the 26 regressions require domain-owner review before broadening the taxonomy.

## Phase gate decision

Phase 1 is ready for approval as an isolated V3 core/evaluation change: the primary-subject target improved and the artifacts are reproducible. Approval should explicitly acknowledge the remaining interdisciplinary regression set. Phase 2 is not started.

## Reproducibility metadata

The Phase 1 metrics and every derived artifact include git commit, dataset SHA256, config SHA256, config file list, UTC generation time and phase label. Current metadata is recorded in `outputs/phase_1/v3_phase_1_metrics.json`; Phase 0 remains frozen under `outputs/phase_0/`.

Artifacts: predictions, errors, metrics, subject confusion, fixed errors, regressions, comparison with Phase 0, rule coverage and the Phase 0 error taxonomy are all under `outputs/phase_1/`.
