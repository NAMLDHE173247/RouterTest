# Rule V3 Phase 2 — Contextual Intent Resolution

## Executive summary

Phase 2 đã triển khai contextual intent resolution trong V3 core/evaluation. Trên 300 mẫu, intent accuracy tăng từ `70.00%` ở Phase 1.2 lên `84.33%`; primary subject giữ `94.00%`. So với Phase 1.2 có `43` intent errors được sửa và `0` regression.

Gate Phase 2: **PASSED**. Không bắt đầu Phase 3.

## Scope và non-scope

Phạm vi chỉ gồm intent core và evaluation của Rule-based Router V3: strong phrase, weak-token disambiguation, negative context, veto, history context, score margin và traceability.

Không thay đổi V0/V1/V2, không mở rộng subject taxonomy, không triển khai dialogue history nâng cao, OOS nâng cao hoặc clarification nâng cao.

## Baseline

Baseline là Phase 1.2, 300 mẫu:

- Primary subject: `94.00%`
- Intent: `70.00%`
- Target SLM: `84.33%`
- Clarification: `88.00%`
- Intent errors: `90`
- Dataset SHA256: `5d25fb93a173733033a632fec3ca7bfc5b29fffb0db2a8b3676ee919301ec5cf`

## Intent error taxonomy trước khi sửa

Artifact đầy đủ: `outputs/phase_2/v3_phase_1_2_intent_error_taxonomy.json`.

- Missing strong intent phrase: `41`
- False-positive intent/OOS veto gap: `14`
- Follow-up context not detected: `10`
- Follow-up bị solve override: `8`
- Diagnose/check-answer collision: `4`
- Hint phrase missing hoặc solve chưa bị veto: `3`
- Explain/solve weak-token collision: `3`
- Các nguyên nhân khác: `7`

Theo case type: interdisciplinary `28`, single-turn `26`, ambiguous `14`, multi-turn `12`, OOS `10`.

## Rules và context đã thêm

- Strong phrase có rule ID riêng cho explain, solve, diagnose, check-answer, hint và follow-up.
- Negative/veto rule cho `công sai` và các yêu cầu chỉ gợi ý/không giải hết.
- Context history chỉ nâng follow-up khi có history; follow-up reference không có history bị veto.
- Formula-error context ưu tiên diagnose trong cụm “sai công thức”.
- Trace ghi rule IDs, veto reason, scores, top/second score và decision margin.
- Tie chỉ xử lý khi bằng điểm; không dùng insertion order để đảo winner.

## Kết quả tổng và theo intent

Kết quả cuối từ `outputs/phase_2/v3_phase_2_metrics.json`:

- Primary subject: `94.00%`
- Intent: `84.33%`
- Target SLM: `84.33%`
- Clarification: `88.00%`
- Exact match: `73.67%`
- Full exact match: `44.67%`

Intent accuracy theo gold intent: ask_follow_up `72.22%`, check_answer `84.62%`, diagnose_error `81.25%`, explain_concept `78.30%`, give_hint `100%`, solve_problem `97.75%`, unknown `71.43%`.

Theo case type, intent accuracy là single-turn `95.83%`, multi-turn `100%`, interdisciplinary `66.13%`, ambiguous `68.97%`, OOS `65.52%`.

## Confusion trước/sau

Trước Phase 2, confusion lớn nhất là explain → unknown `35`, ask_follow_up → unknown `10`, ask_follow_up → solve `8`, unknown → give_hint `8`.

Sau Phase 2, explain → unknown giảm còn `21`, ask_follow_up → unknown còn `4`, ask_follow_up → solve còn `1`; remaining confusion lớn nhất là unknown → give_hint `8`. Ma trận đầy đủ nằm ở `outputs/phase_2/v3_phase_2_intent_confusion.json`.

## Fixed errors và regressions

So với Phase 1.2:

- Fixed intent errors: `43`
- New intent regressions: `0`
- `q006` được sửa: “công sai” không còn bị hiểu là diagnose_error.
- Các nhóm bắt buộc “sai ở bước nào”, “đáp án có đúng không”, “chỉ gợi ý”, “đừng giải hết” và “không cần lời giải” đều có test và trace.

Artifacts: `v3_phase_2_fixed_errors.json`, `v3_phase_2_regressions.json`, `v3_phase_2_comparison_with_phase_1_2.json`.

## Net improvement và ảnh hưởng liên quan

Intent tăng `14.33` điểm phần trăm. Primary subject không giảm (`94.00%` trước/sau), target SLM giữ `84.33%`, clarification giữ `88.00%`. Không có thay đổi subject taxonomy.

Latency cùng lần chạy cuối: mean `3.1062 ms`, median `2.6959 ms`, P95 `6.0767 ms`.

## Test results

Command:

```text
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_rule_v3_phase2_intent_resolution.py backend/tests/test_rule_v3_phase1_subject_resolution.py -q
```

Kết quả: **40 passed**.

Benchmark command chạy evaluator trên 300 mẫu với `--comparison-field intent`; artifacts đầy đủ gồm predictions, errors, metrics, confusion matrices, taxonomy, fixed/regressions, comparison và rule coverage.

## Limitations

Interdisciplinary, ambiguous và OOS vẫn là nhóm yếu nhất về intent. Phase 2 không giải quyết đối thoại nhiều lượt nâng cao, OOS nâng cao hoặc clarification nâng cao theo đúng non-scope.

## Phase gate decision

**PASSED_FOR_PHASE_2_COMPLETION**: intent `84.33%` ≥ `75%`, primary `94.00%` ≥ `93%`, fixed `43` > regressions `0`, target không giảm, và `q006` đã sửa. Không bắt đầu Phase 3.

## Reproducibility metadata

- Code/evaluation commit: `8b5cb3f419d9699f25b3cf62ed7f80974a42730a`
- Dataset SHA256: `5d25fb93a173733033a632fec3ca7bfc5b29fffb0db2a8b3676ee919301ec5cf`
- Config hash: `8d55b9374414903025fc0edf54dbe36f61d6ba3c1a4810f401e82bb7fdca89c1`
- Generated at UTC: `2026-07-17T17:43:18.039366+00:00`
- Report commit: ghi nhận ở commit docs/artifacts sau khi benchmark cuối được lưu.
