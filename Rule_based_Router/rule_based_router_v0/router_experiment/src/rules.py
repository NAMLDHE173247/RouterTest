# rules.py

SUBJECT_KEYWORDS = {
    "math": [
        "toán", "phương trình", "bất phương trình", "hàm số", "đạo hàm",
        "tích phân", "giới hạn", "logarit", "căn bậc", "rút gọn",
        "tam giác", "hình học", "tọa độ", "vectơ", "xác suất",
        "tổ hợp", "chỉnh hợp", "ma trận", "nghiệm", "đồ thị",
        "sin", "cos", "tan"
    ],

    "physics": [
        "vật lý", "vận tốc", "gia tốc", "lực", "khối lượng",
        "trọng lực", "rơi tự do", "chuyển động", "quãng đường",
        "thời gian", "công", "công suất", "động năng", "thế năng",
        "nhiệt lượng", "điện trở", "hiệu điện thế", "cường độ dòng điện",
        "dao động", "sóng", "tần số", "bước sóng", "ánh sáng",
        "thấu kính", "từ trường"
    ],

    "chemistry": [
        "hóa học", "mol", "nồng độ", "dung dịch", "phản ứng",
        "phương trình hóa học", "cân bằng phương trình", "axit", "bazơ",
        "muối", "oxi hóa", "khử", "electron", "nguyên tử",
        "phân tử", "liên kết hóa học", "pH", "kết tủa",
        "khí", "NaOH", "HCl", "CO2", "H2", "O2", "CaCO3"
    ]
}


INTENT_KEYWORDS = {
    "solve_problem": [
        "tính", "giải", "tìm", "xác định", "bao nhiêu",
        "lập phương trình", "rút gọn", "chứng minh", "cân bằng"
    ],

    "explain_concept": [
        "là gì", "giải thích", "khái niệm", "vì sao",
        "tại sao", "nguyên lý", "bản chất", "hiểu như thế nào"
    ],

    "give_hint": [
        "gợi ý", "hint", "hướng làm", "đừng giải hết",
        "cho em hướng", "nên bắt đầu từ đâu"
    ],

    "check_answer": [
        "đúng không", "đúng chưa", "kiểm tra", "đáp án này",
        "em làm vậy đúng không", "kết quả này đúng không"
    ],

    "diagnose_error": [
        "sai ở đâu", "sai chỗ nào", "lỗi", "vì sao sai",
        "em sai bước nào", "chỉ ra lỗi"
    ],

    "ask_follow_up": [
        "câu trên", "tiếp tục", "ý đó", "phần này", "nó",
        "bước tiếp theo", "làm tiếp"
    ]
}


OUT_OF_SCOPE_KEYWORDS = [
    "viết email", "dịch", "lịch sử", "văn học", "địa lý",
    "bóng đá", "phim", "game", "tình yêu", "mua hàng",
    "du lịch", "nấu ăn", "lập trình", "code web"
]
