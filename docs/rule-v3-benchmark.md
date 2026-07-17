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
| Exact match accuracy | 0.5133 | 0.5133 |
| Total errors | 146 | 146 |

Phase 0 đạt mục tiêu tương đương V2 trên dataset hiện tại. Đây là kết quả
baseline, không phải claim rằng V3 đã đạt các target cuối cùng.

## Evaluation additions

Backend evaluation hiện bổ sung secondary-subject exact set match, micro
precision/recall/F1 và metric theo `case_type`. Error output cũng ghi
`secondary_subjects` trong expected/predicted khi field này sai.

## Next benchmark rule

Phase 1 trở đi phải lưu riêng summary, field metrics, case-type metrics, lỗi
đã sửa, regression mới và latency; không tune trên test split cuối.
