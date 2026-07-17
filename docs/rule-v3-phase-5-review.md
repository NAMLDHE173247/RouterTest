# Rule V3 Phase 5 Review và Intent Generalization Plan

## Trạng thái

- Phase 5 methodology: **APPROVED**
- Rule V3 status: **RESEARCH_CANDIDATE**
- Final production/generalization approval: **NOT APPROVED**

Holdout Phase 5 đã fail intent với `0.7000`. Trong checkpoint này không sửa core rules, không sửa threshold, không chạy lại holdout và không tạo dataset mới.

## Artifacts freeze và phạm vi sử dụng

Toàn bộ Phase 5 artifacts tại `outputs/phase_5/` được xem là frozen. Holdout hiện tại từ nay chỉ là analysis/regression data; không được tái sử dụng làm final holdout ở vòng sau. Report Phase 5 đã được giữ nguyên metric và kết luận, đồng thời chuẩn hóa cấu trúc Markdown và bổ sung trạng thái review.

## Intent error analysis

### Validation

Có `7` intent errors:

- `6` lỗi `missing_intent_evidence`: gold chủ yếu là `explain_concept`, prediction là `unknown`, không có matched intent rule, mọi score bằng `0`, không có veto. Đây là paraphrase/concept-explanation coverage gap.
- `1` lỗi `ambiguous_explain_followup_conflict`: câu `v012` có explain và follow-up evidence; `explain_concept` đạt score `13`, follow-up bị veto do thiếu history, nên prediction không còn là gold `unknown`.

Chi tiết đầy đủ gồm gold, prediction, matched rules, score, veto, margin, nguyên nhân và group trong [v3_phase_5_validation_intent_error_taxonomy.json](../Rule_based_Router/rule_based_router_v3/router_experiment/outputs/phase_5/v3_phase_5_validation_intent_error_taxonomy.json).

### Holdout

Có `6` intent errors:

- `5` lỗi `missing_intent_evidence`: các câu explain concept, check answer hoặc solve problem không có intent rule match và trả `unknown`.
- `1` lỗi `explain_vs_solve_overlap`: `h011` là multi-turn, solve rule đạt score `8` trong khi explain không có evidence, nên current-turn solve thắng.
- `1` lỗi `missing_intent_evidence` thuộc nhóm follow-up/ambiguous không có pattern phù hợp.

Các lỗi khác trong holdout chỉ thuộc secondary subjects và không được tính là intent error. Chi tiết nằm trong [v3_phase_5_holdout_intent_error_taxonomy.json](../Rule_based_Router/rule_based_router_v3/router_experiment/outputs/phase_5/v3_phase_5_holdout_intent_error_taxonomy.json).

Không thêm rule nào dựa trên các lỗi này trong checkpoint review.

## Vì sao ba search configurations cho cùng kết quả

Phân tích chỉ dùng search artifact đã commit, gồm 3 trial với `secondary_score_ratio` là `0.30`, `0.35`, `0.45`; các threshold còn lại giữ nguyên.

- `secondary_score_ratio`: không có mẫu nào nằm quanh boundary làm thay đổi secondary prediction.
- `ambiguous_min_score`, `out_of_scope_min_score`, `out_of_scope_max_stem_score`, `cross_domain_max_margin`: mỗi parameter chỉ có một giá trị trong grid 3 trial, vì vậy không thể đo sensitivity nội tại của parameter đó; các sample hiện tại cũng không kích hoạt boundary tương ứng.
- Intent không phụ thuộc trực tiếp vào các threshold subject/scope này. Intent prediction do intent rules, score và veto quyết định; do đó threshold search không thể cải thiện intent.

Sensitivity theo parameter, tested values và metric snapshot nằm trong [v3_phase_5_threshold_sensitivity.json](../Rule_based_Router/rule_based_router_v3/router_experiment/outputs/phase_5/v3_phase_5_threshold_sensitivity.json). Kết luận `0.0` là observed sensitivity trên sample hiện có, không phải bằng chứng threshold đó không bao giờ có tác động.

## Protocol vòng nghiên cứu tiếp theo

### Intent development expansion

Mở rộng development intent với ít nhất 50 mẫu cho mỗi intent, cân bằng subject và case type. Bổ sung paraphrase tự nhiên, câu ngắn, câu hỏi khái niệm, negative/contrastive phrasing, ambiguous follow-up và hard negatives giữa `explain_concept`, `solve_problem`, `check_answer`, `give_hint`, `ask_follow_up`, `diagnose_error`, `unknown`.

### Validation mới

Tạo validation mới sau khi chốt bộ development expansion, stratify theo intent, subject, case type, single-turn/multi-turn, có/không history, interdisciplinary, ambiguous và OOS. Validation dùng để phân tích và chọn thay đổi; không dùng holdout cũ.

### Final holdout mới

Tạo final holdout mới từ nguồn/template khác, freeze trước mọi rule hoặc threshold selection, chạy đúng một lần sau khi config được khóa. Holdout cũ chỉ dùng regression/analysis.

### Leakage checks

Kiểm tra exact duplicate, normalized near-duplicate, template fingerprint, cùng stem thay entity, split ID/provenance và SHA256 manifest. Expected labels phải được review trước metric và không được sửa sau khi thấy kết quả.

Protocol đầy đủ, chưa tạo dataset, nằm trong [v3_next_study_dataset_protocol.json](../Rule_based_Router/rule_based_router_v3/router_experiment/outputs/phase_5/v3_next_study_dataset_protocol.json).

## Gate decision

Phase 5 methodology được duyệt về quy trình. Rule V3 vẫn là **RESEARCH_CANDIDATE**; chưa có final production/generalization approval. Bước tiếp theo chỉ được bắt đầu sau khi có phê duyệt riêng cho intent generalization study.
