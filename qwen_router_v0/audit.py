from schema import RouterDecision
import traceback

print("=== KIỂM TRA SCHEMA ===")
print("[Hợp lệ]")
try:
    d = RouterDecision(
        primary_subject="physics",
        secondary_subjects=["physics", "math", "math", "unknown"],
        intent="solve_problem",
        target_slm="physics_slm",
        confidence=0.9,
        need_clarification=False,
        reason="Test"
    )
    print(f"Validated secondary_subjects: {d.secondary_subjects}")
except Exception as e:
    print("Lỗi:", e)

print("\n[Thất bại]")
test_cases = [
    {"desc": "primary_subject sai", "data": dict(primary_subject="physic", intent="solve_problem", target_slm="physics_slm", confidence=0.9, need_clarification=False, reason="Test")},
    {"desc": "target_slm sai", "data": dict(primary_subject="physics", intent="solve_problem", target_slm="physics", confidence=0.9, need_clarification=False, reason="Test")},
    {"desc": "confidence > 1", "data": dict(primary_subject="physics", intent="solve_problem", target_slm="physics_slm", confidence=1.5, need_clarification=False, reason="Test")},
    {"desc": "reason rỗng", "data": dict(primary_subject="physics", intent="solve_problem", target_slm="physics_slm", confidence=0.9, need_clarification=False, reason="   ")},
    {"desc": "trường ngoài", "data": dict(primary_subject="physics", intent="solve_problem", target_slm="physics_slm", confidence=0.9, need_clarification=False, reason="Test", extra="field")},
]

for tc in test_cases:
    print(f"- {tc['desc']}: ", end="")
    try:
        RouterDecision(**tc['data'])
        print("Không báo lỗi (SAI)")
    except Exception as e:
        print("Đã chặn lỗi (ĐÚNG)")

print("\n=== KIỂM TRA PROMPT ===")
from prompt import build_messages
import json
msgs = build_messages("Giải thích định luật II Newton", history=[])
print("Normal prompt user content:")
print(msgs[1]["content"])

msgs_strict = build_messages("Vậy bước tiếp theo là gì?", history=[], strict=True)
print("\nStrict prompt user content:")
print(msgs_strict[1]["content"])

print("\n=== KIỂM TRA JSON PARSER ===")
from llm_router import QwenRouter
r = QwenRouter.__new__(QwenRouter) # Skip init

tests = [
    ("JSON thuần", '{"a": 1}'),
    ("JSON bọc trong code fence", '```json\n{"b": 2}\n```'),
    ("Một câu dẫn trước JSON", 'Đây là kết quả:\n{"c": 3}'),
    ("Output không có JSON", 'Tôi không biết.'),
]

for name, text in tests:
    print(f"- {name}: ", end="")
    try:
        res = r._extract_json(text)
        print(f"Thành công -> {res}")
    except Exception as e:
        print(f"Thất bại -> {e}")

