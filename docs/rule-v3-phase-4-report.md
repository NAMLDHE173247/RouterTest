# Rule V3 Phase 4 — Interdisciplinary Ownership, Secondary Subjects, OOS & Clarification

## Executive summary

> **Reproducibility note:** Phase 4 is the locked development baseline for Phase 5. Its artifacts are referenced by the Phase 5 manifest using file paths and SHA256 checksums; they are not recursively copied.

Phase 4 đã triển khai ownership theo topic, supporting/tool subject evidence, secondary-subject reasons, ba trạng thái scope và clarification reason codes trong V3 core/evaluation.

Trên 300 mẫu, primary đạt `96.00%`, intent `88.00%`, interdisciplinary primary `85.48%`, secondary micro-F1 `0.7626`, OOS target/clarification `96.55%`, clarification tổng `96.00%`, multi-turn `100%`. Gate **PASSED**; không bắt đầu Phase 5.

## Scope và non-scope

Chỉ thay đổi Rule-based Router V3 core và evaluation liên quan đến interdisciplinary ownership, secondary subjects, out-of-scope và clarification. Không thay đổi V0/V1/V2 và không tuning threshold theo phạm vi Phase 5.

## Baseline Phase 3 đã khóa

- Primary: `0.9400`
- Intent: `0.8467`
- Target: `0.8433`
- Clarification: `0.8800`
- Legacy exact: `0.7400`
- Full exact: `0.4467`
- Secondary micro-F1: `0.2712`
- Interdisciplinary primary: `0.7581`
- OOS target: `0.1724`
- OOS clarification: `0.1724`

Phase 3 artifacts đã freeze tại `outputs/phase_4/phase_3_frozen/`. Taxonomy history được đổi tên nhất quán thành `outputs/phase_3/v3_phase_3_history_error_taxonomy.json`.

## Error analysis trước khi sửa

Artifacts phân tích baseline:

- `v3_phase_4_interdisciplinary_error_taxonomy.json`: missing secondary `118`, primary misresolution `18`, spurious secondary `5`.
- `v3_phase_4_secondary_error_taxonomy.json`: secondary recall missing `118`, false positive `5`.
- `v3_phase_4_oos_error_taxonomy.json`: target mismatch `24`, clarification mismatch `24`, intent mismatch `10`.
- `v3_phase_4_clarification_error_taxonomy.json`: clarification mismatch `36`.

## Ownership và secondary evidence

- Reaction + thermal/pressure focus có ownership rule `subject.chemistry.override.reaction_thermal_focus`.
- Kinematics equation có ownership rule `subject.physics.override.kinematics_equation_focus`.
- Ideal-gas CO2 thêm Chemistry supporting evidence bằng rule `subject.chemistry.supporting.ideal_gas_entity_context`, nhưng Physics vẫn là primary.
- Math chỉ được thêm như tool subject khi có công thức/tính toán độc lập; entity đơn độc không tạo secondary.
- Trace ghi `ownership_override` và `secondary_reasons`.

Các case bắt buộc đã kiểm tra:

- Ideal gas + CO2 → Physics primary, Chemistry secondary.
- Reaction + heat/pressure → Chemistry primary.
- Physics kinematics equation → Physics primary, Math secondary.
- CO2/HCl/O2 đơn độc → không primary/secondary.

## Scope resolution

Scope gồm:

- `CONFIRMED_STEM`: subject evidence đủ mạnh; STEM thắng OOS keyword đa nghĩa.
- `CONFIRMED_OUT_OF_SCOPE`: OOS context rõ; target `general_tutor`, không clarification.
- `UNKNOWN_SCOPE`: không đủ STEM/OOS evidence; yêu cầu clarification.

Trace scope ghi state, score, matched terms và context rule IDs.

## Clarification reason codes

Mọi route có `need_clarification=true` đều có reason code. Coverage cuối: `41` clarifying predictions, missing reason code `0`.

Các code xuất hiện: `NO_SUBJECT_EVIDENCE`, `MISSING_HISTORY_FOR_FOLLOW_UP`, `SUBJECT_SCORE_TIE`, `CROSS_DOMAIN_CONFLICT`, `UNKNOWN_INTENT`, `INCOMPLETE_REFERENCE`, `LOW_CONFIDENCE`. `OUT_OF_SCOPE_CONFIRMED` được dành cho scope confirmed và không bật clarification.

## Kết quả tổng và theo nhóm

Từ `outputs/phase_4/v3_phase_4_metrics.json`:

- Primary: `96.00%`
- Intent: `88.00%`
- Target SLM: `94.00%`
- Clarification: `96.00%`
- Legacy exact: `83.33%`
- Full exact: `71.33%`
- Secondary micro-F1: `0.7626` (precision `0.8991`, recall `0.6622`)
- Interdisciplinary primary: `85.48%`
- OOS target: `96.55%`
- OOS clarification: `96.55%`
- Multi-turn primary/intent: `100%/100%`

## Fixed và regressions so với Phase 3

- Fixed primary errors: `6`
- New primary regressions: `0`
- Fixed > regressions: đạt.
- Multi-turn giữ `100%`.

Artifacts: `v3_phase_4_fixed_errors.json`, `v3_phase_4_regressions.json`, `v3_phase_4_comparison_with_phase_3.json`.

## Latency và reproducibility

Latency cùng lần chạy cuối: mean `4.1976 ms`, median `3.5051 ms`, P95 `7.1909 ms`.

- Code/evaluation commit: `162549e234925b910396871e80334c228ae4315c`
- Dataset SHA256: `5d25fb93a173733033a632fec3ca7bfc5b29fffb0db2a8b3676ee919301ec5cf`
- Config hash: `1ca032b379b937f0d0540337c5e1c7d4d327e82b75cd49538eea35926ec9be4c`
- Generated at UTC: `2026-07-17T18:13:47.549857+00:00`

## Test results

Command:

```text
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_rule_v3_phase4_scope_ownership.py backend/tests/test_rule_v3_phase3_dialogue_context.py backend/tests/test_rule_v3_phase2_intent_resolution.py backend/tests/test_rule_v3_phase1_subject_resolution.py -q
```

Kết quả: `61 passed`.

## Limitations

Interdisciplinary intent vẫn thấp hơn primary do các câu hỏi yêu cầu giải thích hai lĩnh vực; Phase 4 không thực hiện threshold tuning, OOS nâng cao hoặc clarification nâng cao ngoài reason-code/state resolution.

## Phase gate decision

**PASSED_FOR_PHASE_4_COMPLETION**: primary `96.00%` ≥ `93%`, intent `88.00%` ≥ `84%`, interdisciplinary primary `85.48%` ≥ `82%`, secondary F1 `0.7626` ≥ `0.50`, OOS target/clarification `96.55%` ≥ `80%`, clarification `96.00%` ≥ `90%`, multi-turn `100%`, fixed `6` > regressions `0`. Không bắt đầu Phase 5.

## Artifacts

`outputs/phase_4/` gồm metrics, predictions, errors, ba error taxonomies, fixed/regressions, comparison Phase 3, secondary metrics, reason-code coverage và frozen Phase 3 artifacts.
