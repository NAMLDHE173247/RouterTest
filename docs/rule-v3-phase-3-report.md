# Rule V3 Phase 3 — Dialogue Context & History Resolution

## Executive summary

Phase 3 đã bổ sung `RouterContext` cho V3 core, gồm subject/topic/intent/entity gần nhất, số lượt từ subject rõ ràng, pending clarification, context confidence, history decay và provenance trace.

Kết quả trên 300 mẫu: primary `94.00%`, intent `84.67%`, multi-turn `100%`. Gate đạt; không bắt đầu Phase 4.

## Scope và non-scope

Chỉ thay đổi xử lý history và multi-turn trong Rule V3 core/evaluation. Không mở rộng subject taxonomy, không nhồi thêm intent phrase, không triển khai OOS hoặc clarification nâng cao.

## Baseline Phase 2 đã khóa

- Primary: `0.9400`
- Intent: `0.8433`
- Target: `0.8433`
- Clarification: `0.8800`
- Legacy exact: `0.7367`
- Full exact: `0.4467`

Phase 2 đã được freeze tại `outputs/phase_3/phase_2_frozen/`, có manifest SHA256 tại `outputs/phase_3/phase_2_frozen_manifest.json`.

## Phân tích lỗi history/multi-turn trước khi sửa

Baseline có 14 mẫu chứa history, gồm 12 multi-turn. 12 multi-turn đạt đúng 100%; 2 lỗi history/context còn lại là:

- `q246`: current gas/physics evidence giữ physics, trong khi gold là chemistry.
- `q247`: intent `solve_problem` lấn át `ask_follow_up` do current calculation token.

Artifact: `outputs/phase_3/v3_phase_3_history_error_taxonomy.json`.

## RouterContext và policy

RouterContext lưu:

- `last_explicit_subject`, `last_topic`, `last_intent`, `active_entities`
- `turns_since_explicit_subject`, `pending_clarification`
- `context_confidence`, `history_weight`, `source_turn`
- `inherited_fields`, `reset_reason`, `missing_history`

Decay mặc định là `0.75 ** turns_since_explicit_subject`; history có weight dưới `0.25` không được kế thừa mạnh. Current subject/topic evidence thắng history. Subject switch reset context; topic switch trong cùng subject chỉ reset topic. Follow-up không có history trả `missing_history` và yêu cầu clarification.

## Adversarial Phase 2 protection

Đã bổ sung test bảo vệ phủ định ngược:

- “không cần gợi ý, giải luôn bài này” → `solve_problem`
- “đừng chỉ gợi ý, hãy giải đầy đủ” → `solve_problem`

Các veto và rule IDs được ghi trong intent trace.

## Kết quả tổng và theo case type

Artifact chính: `outputs/phase_3/v3_phase_3_metrics.json`.

- Primary: `94.00%`
- Intent: `84.67%`
- Target SLM: `84.33%`
- Clarification: `88.00%`
- Legacy exact: `74.00%`
- Full exact: `44.67%`
- Single-turn primary: `98.21%`
- Single-turn intent: `95.83%`
- Multi-turn primary: `100%`
- Multi-turn intent: `100%`

## Fixed và regressions so với Phase 2

History comparison: `outputs/phase_3/v3_phase_3_history_comparison_with_phase_2.json`.

- Fixed history errors: `1` (`q247` intent)
- New history regressions: `0`
- Unchanged history limitation: `q246`
- Multi-turn accuracy: `100% → 100%`

So sánh toàn bộ primary subject với Phase 2: fixed `0`, regressions `0`; subject được giữ nguyên ngoài phạm vi history có chủ ý.

## Trace và reproducibility

Trace đã có `source_turn`, `history_weight`, `inherited_fields`, `reset_reason`, `context_confidence`, cùng `history_context` trong intent trace.

Latency của cùng lần chạy cuối: mean `3.1490 ms`, median `2.6477 ms`, P95 `5.9995 ms`.

- Code/evaluation commit: `1f0ed63c4b8a18043c2a1c18252f103b25dbb052`
- Dataset SHA256: `5d25fb93a173733033a632fec3ca7bfc5b29fffb0db2a8b3676ee919301ec5cf`
- Config hash: `c028ac001f02c878814a4d8b61dcb90fa4424143d454b339b849cf0880c01d80`
- Generated at UTC: `2026-07-17T17:58:05.797340+00:00`

## Test results

Command:

```text
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_rule_v3_phase3_dialogue_context.py backend/tests/test_rule_v3_phase2_intent_resolution.py backend/tests/test_rule_v3_phase1_subject_resolution.py -q
```

Kết quả: `49 passed`.

## Limitations

`q246` vẫn là lỗi labeling/context interdisciplinary được giữ lại vì current evidence mạnh phải thắng history theo yêu cầu Phase 3. Phase này chưa xử lý OOS nâng cao, clarification nâng cao hoặc dialogue history ngoài RouterContext cấu hình được.

## Phase gate decision

**PASSED_FOR_PHASE_3_COMPLETION**: multi-turn không giảm và đạt `100%`, single-turn primary không giảm, intent `84.67%` ≥ `84%`, primary `94.00%` ≥ `93%`, fixed history `1` > regressions `0`. Không bắt đầu Phase 4.

## Artifacts

`outputs/phase_3/` gồm predictions, errors, metrics, subject/intent confusion, fixed/regressions, comparison với Phase 2, rule coverage, history taxonomy, history comparison và frozen Phase 2 artifacts.
