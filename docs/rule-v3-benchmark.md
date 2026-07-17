# Rule V3 benchmark

## Baseline và Phase 0

Dataset: `Rule_based_Router/rule_based_router_v2/router_experiment/data/test_router.jsonl`

| Metric | V2 baseline | V3 Phase 0 |
| --- | ---: | ---: |
| Samples | 300 | 300 |
| Primary subject accuracy | 0.7667 | 0.7667 |
| Intent accuracy | 0.7000 | 0.7000 |
| Target SLM accuracy | 0.6800 | 0.6800 |
| Need clarification accuracy | 0.7600 | 0.7600 |
| Legacy exact match accuracy | 0.5133 | 0.5133 |
| Full exact match accuracy | not measured | 0.2400 |
| Secondary exact set accuracy | not measured | 0.5667 |
| Secondary micro precision | not measured | 0.2222 |
| Secondary micro recall | not measured | 0.0135 |
| Secondary micro F1 | not measured | 0.0255 |
| Legacy errors | 146 | 146 |
| Full errors | not measured | 228 |

Phase 0 đạt mục tiêu tương đương V2 trên bốn field legacy. Khi bật evaluation
đầy đủ cho `secondary_subjects`, full exact match là `0.24`; đây là thông tin
quan trọng để không nhầm metric legacy với full contract. Đây là kết quả
baseline, không phải claim rằng V3 đã đạt các target cuối cùng.

## Evaluation additions

Backend evaluation hiện bổ sung secondary-subject exact set match, micro
precision/recall/F1 và metric theo `case_type`. Error output cũng ghi
`secondary_subjects` trong expected/predicted khi field này sai.

## Next benchmark rule

Phase 1 trở đi phải lưu riêng summary, field metrics, case-type metrics, lỗi
đã sửa, regression mới và latency; không tune trên test split cuối.
