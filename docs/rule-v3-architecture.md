# Rule-based Router V3

## Phase status

V3 hiện hoàn thành Phase 0.1 Hardening: core nằm tại
`Rule_based_Router/rule_based_router_v3/router_experiment/src/` và có output
chuẩn giống V2 trên các field legacy. Phase 0.1 chưa thay đổi thuật toán;
mục đích là tạo baseline độc lập, kiểm tra per-sample và làm rõ evaluation
contract.

Các phase cải tiến tiếp theo sẽ tách riêng:

- Phase 1: structured rules và topic taxonomy.
- Phase 2: contextual intent resolution.
- Phase 3: dialogue context và history weighting.
- Phase 4: interdisciplinary ownership, OOS và clarification reason code.
- Phase 5: threshold tuning trên development/validation/test split.

Mỗi phase phải giữ output benchmark riêng, regression test riêng và đối chiếu
với V2 trước khi được xem là hoàn thành.

## Output contract

Core vẫn trả các field hiện hữu: `primary_subject`, `secondary_subjects`,
`intent`, `target_slm`, `confidence`, `need_clarification`, `reason`. Các
field debug/metadata mới trong backend schema đều optional.

## Known limitations

Phase 0 vẫn dùng rule và priority của V2. Vì vậy chưa giải quyết các lỗi
keyword đa nghĩa, context nhiều lượt, topic ownership hoặc calibration.
