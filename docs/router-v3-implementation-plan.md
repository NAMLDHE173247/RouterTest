# Implementation plan

## Đã thực hiện

1. Kiểm kê repository, adapters, schemas, evaluation và frontend.
2. Tạo `RoutingService` facade cùng Rule-based/SLM registry.
3. Bọc V0, V1, V2, Qwen V0 thành version services; giữ adapter cũ.
4. Tạo Rule V3 Phase 0 độc lập từ V2.
5. Mở rộng metadata và evaluation theo secondary subject/case type.
6. Giữ endpoint legacy và cập nhật fallback frontend cho V3.

## Phase 0.1 hardening đã hoàn tất

- Evaluator V3 dùng `outputs/phase_0/`, tên `v3_phase_0_*` và có CLI.
- Regression test so sánh V2/V3 trên toàn bộ 300 sample.
- Tách legacy exact match và full exact match có secondary subjects.
- Evaluation reject router ID không hợp lệ thay vì silently skip.
- Qwen metadata dùng cached health và không gọi network khi list router.
- Legacy route được giữ nhưng ẩn khỏi OpenAPI schema.

## Giữ nguyên

- Core và router ID của V0, V1, V2.
- Evaluation history hiện có trong `data/evaluation_runs`.
- Qwen external service và cấu hình URL runtime.
- Response field bắt buộc hiện tại.

## Thứ tự tiếp theo

1. Bổ sung regression set từ V2 error output.
2. Tách taxonomy/rule model cho V3 Phase 1.
3. Thêm contextual intent resolver và test Phase 2.
4. Thêm dialogue context/history state Phase 3.
5. Thêm scope/ownership/clarification policy Phase 4.
6. Tạo stratified split và tuning script Phase 5.

Mỗi bước phải benchmark trước/sau và dừng nếu có regression chưa giải thích.
