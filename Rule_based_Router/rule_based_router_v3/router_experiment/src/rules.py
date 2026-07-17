# rules.py  —  v1

SUBJECT_RULES = {
    "math": [
        {"term": "đạo hàm", "weight": 5, "type": "domain_specific"},
        {"term": "tích phân", "weight": 5, "type": "domain_specific"},
        {"term": "hàm số", "weight": 5, "type": "domain_specific"},
        {"term": "logarit", "weight": 5, "type": "domain_specific"},
        {"term": "ma trận", "weight": 5, "type": "domain_specific"},
        {"term": "xác suất", "weight": 5, "type": "domain_specific"},
        {"term": "tổ hợp", "weight": 4, "type": "domain_specific"},
        {"term": "chỉnh hợp", "weight": 4, "type": "domain_specific"},
        {"term": "phương trình bậc hai", "weight": 4, "type": "domain_specific"},
        {"term": "bất phương trình", "weight": 4, "type": "domain_specific"},
        {"term": "tam giác", "weight": 3, "type": "domain_specific"},
        {"term": "hình học", "weight": 3, "type": "domain_specific"},
        {"term": "tọa độ", "weight": 3, "type": "domain_specific"},
        {"term": "vectơ", "weight": 3, "type": "domain_specific"},
        {"term": "đồ thị", "weight": 3, "type": "domain_specific"},
        {"term": "nghiệm", "weight": 2, "type": "general"},
        {"term": "phương trình", "weight": 1, "type": "general"},
        {"term": "sin", "weight": 3, "type": "domain_specific"},
        {"term": "cos", "weight": 3, "type": "domain_specific"},
        {"term": "tan", "weight": 3, "type": "domain_specific"},
    ],

    "physics": [
        {"term": "rơi tự do", "weight": 5, "type": "domain_specific"},
        {"term": "vận tốc", "weight": 5, "type": "domain_specific"},
        {"term": "gia tốc", "weight": 5, "type": "domain_specific"},
        {"term": "định luật newton", "weight": 5, "type": "domain_specific"},
        {"term": "lực ma sát", "weight": 5, "type": "domain_specific"},
        {"term": "động năng", "weight": 5, "type": "domain_specific"},
        {"term": "thế năng", "weight": 5, "type": "domain_specific"},
        {"term": "điện trở", "weight": 5, "type": "domain_specific"},
        {"term": "hiệu điện thế", "weight": 5, "type": "domain_specific"},
        {"term": "cường độ dòng điện", "weight": 5, "type": "domain_specific"},
        {"term": "từ trường", "weight": 5, "type": "domain_specific"},
        {"term": "dao động", "weight": 4, "type": "domain_specific"},
        {"term": "sóng", "weight": 4, "type": "domain_specific"},
        {"term": "tần số", "weight": 4, "type": "domain_specific"},
        {"term": "bước sóng", "weight": 4, "type": "domain_specific"},
        {"term": "thấu kính", "weight": 4, "type": "domain_specific"},
        {"term": "nhiệt lượng", "weight": 4, "type": "domain_specific"},
        {"term": "chuyển động", "weight": 3, "type": "domain_specific"},
        {"term": "quãng đường", "weight": 3, "type": "domain_specific"},
        {"term": "vật", "weight": 2, "type": "general"},
        {"term": "lực", "weight": 3, "type": "domain_specific"},
        {"term": "khối lượng", "weight": 2, "type": "general"},
        {"term": "thời gian", "weight": 1, "type": "general"},
    ],

    "chemistry": [
        {"term": "phương trình hóa học", "weight": 5, "type": "domain_specific"},
        {"term": "phản ứng hóa học", "weight": 5, "type": "domain_specific"},
        {"term": "cân bằng phương trình", "weight": 5, "type": "domain_specific"},
        {"term": "mol", "weight": 5, "type": "domain_specific"},
        {"term": "nồng độ mol", "weight": 5, "type": "domain_specific"},
        {"term": "độ ph", "weight": 5, "type": "domain_specific"},
        {"term": "axit", "weight": 5, "type": "domain_specific"},
        {"term": "bazơ", "weight": 5, "type": "domain_specific"},
        {"term": "oxi hóa", "weight": 5, "type": "domain_specific"},
        {"term": "khử", "weight": 5, "type": "domain_specific"},
        {"term": "kết tủa", "weight": 5, "type": "domain_specific"},
        {"term": "dung dịch", "weight": 4, "type": "domain_specific"},
        {"term": "nồng độ", "weight": 4, "type": "domain_specific"},
        {"term": "nguyên tử", "weight": 4, "type": "domain_specific"},
        {"term": "phân tử", "weight": 4, "type": "domain_specific"},
        {"term": "electron", "weight": 4, "type": "domain_specific"},
        {"term": "liên kết hóa học", "weight": 4, "type": "domain_specific"},
        {"term": "phản ứng", "weight": 3, "type": "domain_specific"},
        {"term": "muối", "weight": 3, "type": "domain_specific"},
        {"term": "khí", "weight": 2, "type": "general"},
        {"term": "chất", "weight": 1, "type": "general"},
        {"term": "naoh", "weight": 5, "type": "domain_specific"},
        {"term": "hcl", "weight": 5, "type": "domain_specific"},
        {"term": "co2", "weight": 5, "type": "domain_specific"},
        {"term": "h2o", "weight": 5, "type": "domain_specific"},
        {"term": "h2", "weight": 4, "type": "domain_specific"},
        {"term": "o2", "weight": 4, "type": "domain_specific"},
        {"term": "caco3", "weight": 5, "type": "domain_specific"},
    ],
}


INTENT_PRIORITY = [
    "diagnose_error",
    "check_answer",
    "give_hint",
    "explain_concept",
    "solve_problem",
    "ask_follow_up",
]


INTENT_RULES = {
    "diagnose_error": [
        {"term": "sai ở đâu", "weight": 5},
        {"term": "sai chỗ nào", "weight": 5},
        {"term": "em sai bước nào", "weight": 5},
        {"term": "vì sao sai", "weight": 5},
        {"term": "chỉ ra lỗi", "weight": 5},
        {"term": "lỗi sai", "weight": 5},
        {"term": "sai", "weight": 3},
        {"term": "lỗi", "weight": 3},
    ],

    "check_answer": [
        {"term": "đúng không", "weight": 5},
        {"term": "đúng chưa", "weight": 5},
        {"term": "kiểm tra đáp án", "weight": 5},
        {"term": "kiểm tra giúp", "weight": 4},
        {"term": "kết quả này đúng không", "weight": 5},
        {"term": "em làm vậy đúng không", "weight": 5},
    ],

    "give_hint": [
        {"term": "gợi ý", "weight": 5},
        {"term": "hint", "weight": 5},
        {"term": "đừng giải hết", "weight": 5},
        {"term": "cho em hướng làm", "weight": 5},
        {"term": "hướng làm", "weight": 4},
        {"term": "nên bắt đầu từ đâu", "weight": 5},
    ],

    "explain_concept": [
        {"term": "là gì", "weight": 5},
        {"term": "giải thích", "weight": 4},
        {"term": "vì sao", "weight": 4},
        {"term": "tại sao", "weight": 4},
        {"term": "khái niệm", "weight": 4},
        {"term": "bản chất", "weight": 4},
        {"term": "nguyên lý", "weight": 4},
        {"term": "hiểu như thế nào", "weight": 4},
    ],

    "solve_problem": [
        {"term": "tính", "weight": 4},
        {"term": "tìm", "weight": 4},
        {"term": "xác định", "weight": 4},
        {"term": "giải bài", "weight": 4},
        {"term": "giải phương trình", "weight": 4},
        {"term": "rút gọn", "weight": 4},
        {"term": "chứng minh", "weight": 4},
        {"term": "cân bằng", "weight": 4},
        {"term": "bao nhiêu", "weight": 3},
    ],

    "ask_follow_up": [
        {"term": "câu trên", "weight": 5},
        {"term": "tiếp tục", "weight": 5},
        {"term": "làm tiếp", "weight": 5},
        {"term": "bước tiếp theo", "weight": 5},
        {"term": "phần này", "weight": 4},
        {"term": "ý đó", "weight": 4},
        {"term": "phần đó", "weight": 4},
    ],
}


FOLLOW_UP_RULES = [
    {
        "term": "câu trên",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "phần trên",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "ý đó",
        "weight": 4,
        "type": "medium"
    },
    {
        "term": "phần đó",
        "weight": 4,
        "type": "medium"
    },
    {
        "term": "bước này",
        "weight": 4,
        "type": "medium"
    },
    {
        "term": "bước trên",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "làm tiếp",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "tiếp tục",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "giải thích lại",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "vì sao vậy",
        "weight": 4,
        "type": "medium"
    },
    {
        "term": "sao lại vậy",
        "weight": 4,
        "type": "medium"
    }
]


AMBIGUOUS_RULES = [
    {
        "term": "cái này",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "phần này",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "bài này",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "chỗ này",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "đoạn này",
        "weight": 5,
        "type": "strong"
    },
    {
        "term": "nó",
        "weight": 3,
        "type": "medium"
    },
    {
        "term": "vậy là sao",
        "weight": 5,
        "type": "strong"
    }
]


THRESHOLDS = {
    "minimum_subject_score": 2,

    "history_inherit_max_score": 3,

    "secondary_min_score": 2,
    "secondary_score_ratio": 0.35,

    "domain_owner_min_score": 4,
    "domain_owner_math_ratio": 0.55,

    "ambiguous_min_score": 4,

    "out_of_scope_min_score": 5,
    "out_of_scope_max_stem_score": 2,

    "cross_domain_min_score": 4,
    "cross_domain_max_margin": 1
}


OUT_OF_SCOPE_RULES = [
    {"term": "viết email", "weight": 5},
    {"term": "dịch sang tiếng anh", "weight": 5},
    {"term": "dịch sang tiếng việt", "weight": 5},
    {"term": "văn học", "weight": 5},
    {"term": "lịch sử", "weight": 5},
    {"term": "địa lý", "weight": 5},
    {"term": "bóng đá", "weight": 5},
    {"term": "phim", "weight": 5},
    {"term": "game", "weight": 5},
    {"term": "tình yêu", "weight": 5},
    {"term": "mua hàng", "weight": 5},
    {"term": "du lịch", "weight": 5},
    {"term": "nấu ăn", "weight": 5},
    {"term": "lập trình", "weight": 5},
    {"term": "code web", "weight": 5},
]
