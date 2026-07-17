"""Create new Phase 5 validation and holdout data before threshold tuning.

The two lists are authored independently from the 300-sample development set.
They are frozen before search; the holdout is never read by tuning code.
"""

import argparse
import json
import os


def row(identifier, question, subject, intent, target, clarification=False, secondary=None, case_type="single_turn", history=None):
    return {
        "id": identifier,
        "question": question,
        "history": history or [],
        "primary_subject": subject,
        "secondary_subjects": secondary or [],
        "intent": intent,
        "target_slm": target,
        "need_clarification": clarification,
        "case_type": case_type,
    }


VALIDATION = [
    row("v001", "Tìm vận tốc của vật rơi tự do sau 4 giây, lấy g = 10 m/s^2.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("v002", "Đạo hàm âm trên khoảng thì hàm số tăng hay giảm?", "math", "explain_concept", "math_slm"),
    row("v003", "Xác định độ axit pH của mẫu HCl nồng độ 0,01 M.", "chemistry", "solve_problem", "chemistry_slm", secondary=["math"]),
    row("v004", "Bình CO2 tuân theo khí lí tưởng PV=nRT; áp suất thay đổi ra sao?", "physics", "explain_concept", "physics_slm", secondary=["chemistry"], case_type="interdisciplinary"),
    row("v005", "Phản ứng tỏa nhiệt làm nhiệt độ tăng, trọng tâm là phản ứng hóa học.", "chemistry", "explain_concept", "chemistry_slm", secondary=["physics"], case_type="interdisciplinary"),
    row("v006", "Giải phương trình mô tả chuyển động rơi tự do v = gt.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("v007", "CO2", "unknown", "unknown", "ask_clarification", True, case_type="ambiguous"),
    row("v008", "Ngày mai Hà Nội có mưa không?", "unknown", "unknown", "general_tutor", False, case_type="out_of_scope"),
    row("v009", "Gợi ý món ăn sáng nhanh trước giờ học.", "unknown", "unknown", "general_tutor", False, case_type="out_of_scope"),
    row("v010", "Vậy bước tiếp theo của bài này là gì?", "math", "ask_follow_up", "math_slm", history=["Em đang học phương trình bậc hai."], case_type="multi_turn"),
    row("v011", "Lực ma sát tác dụng lên vật thế nào?", "physics", "explain_concept", "physics_slm", history=["Em đang học phương trình bậc hai."], case_type="multi_turn"),
    row("v012", "Phần này là gì?", "unknown", "unknown", "ask_clarification", True, case_type="ambiguous"),
    row("v013", "Mạch có điện trở 5 ohm và dòng điện 2 A, tính hiệu điện thế.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("v014", "Cho 0,2 mol NaOH phản ứng với HCl, tìm số mol cần dùng.", "chemistry", "solve_problem", "chemistry_slm", secondary=["math"]),
    row("v015", "Điện phân dung dịch tạo electron và dòng điện trong mạch.", "chemistry", "explain_concept", "chemistry_slm", secondary=["physics"], case_type="interdisciplinary"),
    row("v016", "Đáp án em tính ra có đúng không?", "unknown", "check_answer", "ask_clarification", True, case_type="ambiguous"),
    row("v017", "Không cần gợi ý, hãy giải bài tính công suất.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("v018", "Đừng chỉ gợi ý, giải đầy đủ phương trình này.", "math", "solve_problem", "math_slm"),
    row("v019", "Một chất khí có CO2 và áp suất theo PV=nRT.", "physics", "explain_concept", "physics_slm", secondary=["chemistry"], case_type="interdisciplinary"),
    row("v020", "Tính thể tích H2 sinh ra khi Zn phản ứng với HCl.", "chemistry", "solve_problem", "chemistry_slm", secondary=["math"]),
]


HOLDOUT = [
    row("h001", "Một xe đi nhanh dần đều, sau 5 s vận tốc là 20 m/s; tính gia tốc.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("h002", "Giải thích ý nghĩa của cực trị trong khảo sát hàm số.", "math", "explain_concept", "math_slm"),
    row("h003", "Một mẫu dung dịch chứa 0,5 mol muối trong bình 2 lít; hãy tìm đại lượng mol.", "chemistry", "solve_problem", "chemistry_slm", secondary=["math"]),
    row("h004", "Khí O2 trong bình kín dùng định luật khí lí tưởng; áp suất phụ thuộc gì?", "physics", "explain_concept", "physics_slm", secondary=["chemistry"], case_type="interdisciplinary"),
    row("h005", "Phản ứng cháy tỏa nhiệt, hãy giải thích dưới góc nhìn hóa học.", "chemistry", "explain_concept", "chemistry_slm", secondary=["physics"], case_type="interdisciplinary"),
    row("h006", "Dùng phương trình để tính vận tốc của chuyển động rơi tự do.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("h007", "HCl", "unknown", "unknown", "ask_clarification", True, case_type="ambiguous"),
    row("h008", "Tối nay nên xem phim gì?", "unknown", "unknown", "general_tutor", False, case_type="out_of_scope"),
    row("h009", "Cách nấu mì trứng nhanh là gì?", "unknown", "unknown", "general_tutor", False, case_type="out_of_scope"),
    row("h010", "Vậy phải làm gì tiếp theo?", "chemistry", "ask_follow_up", "chemistry_slm", history=["Em đang làm bài phản ứng giữa Mg và HCl."], case_type="multi_turn"),
    row("h011", "Cường độ dòng điện thay đổi thế nào khi giảm điện trở?", "physics", "explain_concept", "physics_slm", history=["Em đang học phương trình đường thẳng."], case_type="multi_turn"),
    row("h012", "Công thức được nhắc đến dùng vào trường hợp nào?", "unknown", "unknown", "ask_clarification", True, case_type="ambiguous"),
    row("h013", "Bóng đèn 220 V công suất 60 W, tính dòng điện.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("h014", "Hoàn tất hệ số cho phương trình Na + H2O -> NaOH + H2.", "chemistry", "solve_problem", "chemistry_slm", secondary=["math"]),
    row("h015", "Ion trong dung dịch dẫn điện như thế nào?", "chemistry", "explain_concept", "chemistry_slm", secondary=["physics"], case_type="interdisciplinary"),
    row("h016", "Có thể tin cậy đáp số vừa nhận được không?", "unknown", "check_answer", "ask_clarification", True, case_type="ambiguous"),
    row("h017", "Đừng chỉ gợi ý, hãy giải phương trình bậc hai.", "math", "solve_problem", "math_slm"),
    row("h018", "Không cần gợi ý, tính lực trong bài này.", "physics", "solve_problem", "physics_slm", secondary=["math"]),
    row("h019", "CO2 trong bình có áp suất thay đổi theo PV=nRT.", "physics", "explain_concept", "physics_slm", secondary=["chemistry"], case_type="interdisciplinary"),
    row("h020", "Tính số mol khí H2 thu được sau phản ứng với axit.", "chemistry", "solve_problem", "chemistry_slm", secondary=["math"]),
]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        for item in rows:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    write_jsonl(os.path.join(args.output_dir, "validation.jsonl"), VALIDATION)
    write_jsonl(os.path.join(args.output_dir, "holdout.jsonl"), HOLDOUT)
    print(json.dumps({"validation": len(VALIDATION), "holdout": len(HOLDOUT)}, indent=2))
