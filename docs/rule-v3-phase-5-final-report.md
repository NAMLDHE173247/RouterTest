# Rule V3 Phase 5 — Threshold Tuning, Calibration và Final Validation

## Executive summary

Phase 5 đã khóa threshold config, chạy bounded search trên development/validation và chạy holdout final đúng một lần. Development đạt toàn bộ gate nội bộ. Holdout không đạt gate đề xuất vì intent accuracy chỉ đạt `0.7000` dưới ngưỡng `0.7800`; không sửa rule hoặc threshold sau holdout.

## Scope và non-scope

Chỉ thay đổi Rule-based Router V3, evaluator, test và benchmark artifacts. Không thay đổi V0/V1/V2, không mở rộng taxonomy và không bắt đầu Phase 6.

## Baseline Phase 4

Primary `0.9600`; intent `0.8800`; target `0.9400`; clarification `0.9600`; legacy exact `0.8333`; full exact `0.7133`; secondary precision/recall/F1 `0.8991/0.6622/0.7626`; interdisciplinary primary `0.8548`.

## Dataset và leakage

- Development: 300 mẫu lịch sử, dùng làm development/regression set trong Phase 1–4.
- Validation: 20 mẫu mới, tạo trước search.
- Holdout: 20 mẫu mới, freeze trước tuning, không được search đọc.
- Exact duplicate và near-duplicate giữa ba split: `0` và `0`.
- Hash/provenance: `v3_phase_5_duplicate_leakage_report.json`.

Không sửa expected label để tăng metric. Hai split mới là generated validation/holdout, vì vậy kết quả không đại diện cho một benchmark độc lập quy mô lớn.

## Threshold và search

Threshold tập trung tại `src/threshold_config.py`. Semantic thresholds được giữ cố định; tunable thresholds gồm secondary ratio, ambiguous/OOS/cross-domain thresholds. Search có giới hạn 3 cấu hình, objective kết hợp primary, intent, target, clarification, secondary F1 và full exact, kèm constraints development.

Ba cấu hình đều có cùng kết quả; cấu hình khóa chọn `secondary_score_ratio=0.30`, các giá trị còn lại giữ `4, 5, 2, 1`. Holdout không được dùng để chọn config.

## Kết quả theo split

### Development — 300 mẫu

- Primary `0.9600` — đạt gate `≥0.95`.
- Intent `0.8800` — đạt `≥0.87`.
- Target `0.9400` — đạt `≥0.93`.
- Clarification `0.9600` — đạt `≥0.95`.
- Secondary F1 `0.7626` — đạt `≥0.75`.
- Full exact `0.7133`; latency mean/median/P95 `5.5140/4.7297/13.3417 ms`.

### Validation — 20 mẫu

Primary `0.9000`, intent `0.6500`, target `0.9000`, clarification `0.9000`, secondary F1 `0.7000`. Split này dưới development gate; không dùng holdout để bù hoặc điều chỉnh kết quả.

### Holdout final — 20 mẫu, chạy một lần

Primary `0.9000` (đạt đề xuất `≥0.85`); intent `0.7000` (không đạt `≥0.78`); target `0.9000` (đạt `≥0.82`); clarification `0.9000` (đạt `≥0.85`); secondary F1 `0.7000` (đạt `≥0.55`). OOS có 2 mẫu và đạt đúng target/clarification; precision/recall OOS trên nhóm này là `1.0000/1.0000`.

Latency holdout mean/median/P95: `5.8466/4.1049/10.8900 ms`.

## Confidence và calibration

Đã báo cáo confidence buckets cho từng split và ECE/Brier trong `v3_phase_5_calibration_report.json`. Holdout ECE primary/intent lần lượt `0.2185/0.1985`; Brier primary/intent `0.1256/0.2316`. Confidence chưa được calibrated; đây là phép đo, không phải tuyên bố calibration.

## Adversarial tests

7/7 case đạt: đa nghĩa `tan`, phủ định ngược, entity-only, STEM/OOS ambiguity, interdisciplinary ownership và follow-up thiếu history. Test command:

```text
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_rule_v3_phase1_subject_resolution.py backend/tests/test_rule_v3_phase4_scope_ownership.py backend/tests/test_rule_v3_phase5_adversarial.py -q
```

Kết quả: `42 passed`.

## Fixed và regressions

Comparison theo từng field gồm primary, intent, target, clarification, secondary subjects, legacy exact và full exact nằm trong `v3_phase_5_comparison_by_field.json`; fixed/regressions tương ứng nằm trong hai artifact cùng tên. Với development so với Phase 4, không có thay đổi metric và không có regression mới.

## Artifacts

Thư mục `outputs/phase_5/` chứa final config, search results, metrics/predictions/errors của development/validation/holdout, confidence buckets, calibration, adversarial results, per-field comparison, fixed/regressions, subject confusion, rule coverage, duplicate/leakage report và reproducibility manifest. Manifest chỉ tham chiếu Phase 4 bằng path + SHA256, không copy đệ quy frozen artifacts.

## Limitations

Validation và holdout chỉ có 20 mẫu mỗi split và được tạo mới trong repository; intent coverage ngoài development còn yếu. Holdout đã fail intent gate, nên chưa có cơ sở tuyên bố Rule V3 đã hoàn tất hoặc calibrated.

## Phase gate decision

**NOT APPROVED / HOLDOUT GATE FAILED.** Development gate đạt; holdout fail intent (`70.00% < 78.00%`). Không bắt đầu phase tiếp theo. Vòng nghiên cứu sau phải tạo validation/holdout mới trước khi tiếp tục tuning.

## Reproducibility metadata

- Locked code/config commit: `7e938b3d7c8cad01f163add5e712024742c8cc17`.
- Development SHA256: `5d25fb93a173733033a632fec3ca7bfc5b29fffb0db2a8b3676ee919301ec5cf`.
- Validation SHA256: `7c3a10d9ec71292faf571ffe262975c5e2e6ec49b065919ed7cf3b8461a1d118`.
- Holdout SHA256: `1c786b2594013c4205c9c2425e6786919471c288158af09c480a3abad173614e`.
- Artifact manifest: `outputs/phase_5/v3_phase_5_reproducibility_manifest.json`.
