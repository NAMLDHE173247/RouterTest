"""Phase 1 Subject -> Branch -> Topic -> Concept taxonomy.

Entities are deliberately separated from strong/support evidence. An entity
such as CO2, O2 or H2 cannot select Chemistry by itself.
"""

from dataclasses import replace

from models import TopicDefinition


TOPIC_DEFINITIONS = (
    # Math: algebra and number topics.
    TopicDefinition(
        "math.algebra.linear_equation", "math", "algebra",
        strong_terms=("hệ phương trình", "giải phương trình", "phương trình bậc nhất", "chuyển vế", "phương trình tuyến tính"),
        support_terms=("phương trình", "nghiệm", "ẩn số", "thế vào"),
        formula_patterns=(r"\b[xyz]\s*[=+\-]\s*\d", r"\b\d*[xyz]\s*[+\-]\s*\d+"),
        description="Linear equations and systems.",
    ),
    TopicDefinition(
        "math.algebra.quadratic", "math", "algebra",
        strong_terms=("phương trình bậc hai", "nghiệm kép", "delta", "biệt thức"),
        support_terms=("parabol", "tam thức bậc hai", "nghiệm"),
        formula_patterns=(r"\bx\s*\^\s*2\b", r"\bx²\b"),
        description="Quadratic equations and functions.",
    ),
    TopicDefinition(
        "math.algebra.inequality", "math", "algebra",
        strong_terms=("bất phương trình", "đổi chiều dấu"),
        support_terms=("lớn hơn", "nhỏ hơn", "miền nghiệm"),
        formula_patterns=(r"[xyz]\s*(?:>|<|<=|>=|≤|≥)" ,),
        description="Inequalities.",
    ),
    TopicDefinition(
        "math.algebra.fraction", "math", "algebra",
        strong_terms=("phân thức", "phân số tối giản", "rút gọn phân số", "tử số", "mẫu số"),
        support_terms=("phân số", "rút gọn", "điều kiện xác định"),
        formula_patterns=(r"\d+\s*/\s*\d+",),
        description="Fractions and rational expressions.",
    ),
    TopicDefinition(
        "math.sequences.arithmetic", "math", "algebra",
        strong_terms=("cấp số cộng", "công sai", "dãy số"),
        support_terms=("số hạng đầu", "tổng số hạng", "dãy số"),
        formula_patterns=(r"u\s*\d+\s*=",),
        description="Arithmetic progressions.",
    ),
    TopicDefinition(
        "math.sequences.geometric", "math", "algebra",
        strong_terms=("cấp số nhân", "công bội"),
        support_terms=("số hạng", "dãy số"),
        description="Geometric progressions.",
    ),
    TopicDefinition(
        "math.calculus.derivative", "math", "calculus",
        strong_terms=("đạo hàm", "bảng biến thiên", "cực trị", "hàm số chẵn", "hàm số lẻ"),
        support_terms=("hàm số tăng", "hàm số giảm", "đồng biến", "nghịch biến"),
        description="Derivatives, monotonicity and extrema.",
    ),
    TopicDefinition(
        "math.calculus.integral", "math", "calculus",
        strong_terms=("tích phân", "nguyên hàm"),
        support_terms=("diện tích dưới đồ thị", "đổi biến"),
        description="Integrals and antiderivatives.",
    ),
    TopicDefinition(
        "math.calculus.limit", "math", "calculus",
        strong_terms=("giới hạn", "x tiến tới"),
        support_terms=("vô cực", "liên tục"),
        description="Limits.",
    ),
    TopicDefinition(
        "math.geometry.plane", "math", "geometry",
        strong_terms=("hình học phẳng", "tam giác", "đường tròn", "góc đối đỉnh", "đường trung tuyến", "đường thẳng song song"),
        support_terms=("chu vi", "diện tích tam giác", "góc", "song song", "vuông góc"),
        description="Plane geometry.",
    ),
    TopicDefinition(
        "math.geometry.solid", "math", "geometry",
        strong_terms=("hình chóp", "hình trụ", "hình cầu", "thể tích hình cầu"),
        support_terms=("thể tích", "diện tích đáy", "chiều cao", "bán kính"),
        unit_patterns=(r"\d+\s*cm\s*(?:2|3)?\b",),
        description="Solid geometry and volume.",
    ),
    TopicDefinition(
        "math.geometry.coordinate", "math", "geometry",
        strong_terms=("tọa độ", "hệ số góc", "trung điểm", "khoảng cách từ một điểm đến một đường thẳng"),
        support_terms=("mặt phẳng", "phương trình đường thẳng"),
        description="Coordinate geometry.",
    ),
    TopicDefinition(
        "math.trigonometry", "math", "algebra",
        strong_terms=("lượng giác", "sin", "cos", "tan"),
        support_terms=("góc", "đẳng thức"),
        description="Trigonometry.",
    ),
    TopicDefinition(
        "math.probability_statistics", "math", "probability_statistics",
        strong_terms=("xác suất", "trung bình cộng", "ngẫu nhiên", "hoán vị", "chỉnh hợp"),
        support_terms=("chọn", "tần số", "dữ liệu"),
        description="Probability and statistics.",
    ),
    TopicDefinition(
        "math.complex_numbers", "math", "algebra",
        strong_terms=("số phức", "môđun"),
        support_terms=("phần thực", "phần ảo"),
        description="Complex numbers.",
    ),
    TopicDefinition(
        "math.exponential_logarithm", "math", "algebra",
        strong_terms=("logarit", "hàm mũ", "căn bậc hai", "căn thức"),
        support_terms=("tập xác định", "số mũ"),
        description="Exponential, logarithmic and radical expressions.",
    ),

    # Physics: owner topics for gas, energy, electricity and optics.
    TopicDefinition(
        "physics.mechanics.motion", "physics", "mechanics",
        strong_terms=("rơi tự do", "vận tốc", "gia tốc", "chuyển động", "quãng đường", "ném thẳng đứng"),
        support_terms=("thời gian", "đứng yên", "nhanh dần đều", "chuyển động tròn"),
        unit_patterns=(r"\b(?:m/s|km/h)\b",),
        description="Motion and kinematics.",
    ),
    TopicDefinition(
        "physics.mechanics.force", "physics", "mechanics",
        strong_terms=("định luật newton", "lực ma sát", "hợp lực", "trọng lượng", "lực đẩy ác-si-mét", "lực đàn hồi"),
        support_terms=("lực", "khối lượng", "mặt phẳng ngang", "vật nổi"),
        unit_patterns=(r"\d+\s*(?:newton|n)\b", r"\d+\s*kg\b"),
        description="Forces and Newtonian mechanics.",
    ),
    TopicDefinition(
        "physics.mechanics.inertia", "physics", "mechanics",
        strong_terms=("quán tính", "phanh gấp", "chúi về phía trước"),
        support_terms=("xe", "đứng yên"),
        description="Inertia.",
    ),
    TopicDefinition(
        "physics.energy.work", "physics", "mechanics",
        strong_terms=("công cơ học", "cơ năng", "động năng", "thế năng", "công suất"),
        support_terms=("bảo toàn năng lượng", "điện năng", "p = a/t", "mốc thế năng"),
        unit_patterns=(r"\b(?:joule|watt|wh|kwh)\b",),
        description="Work, power and mechanical energy.",
    ),
    TopicDefinition(
        "physics.thermodynamics.ideal_gas", "physics", "thermodynamics",
        strong_terms=("khí lí tưởng", "phương trình khí lí tưởng", "áp suất khí", "số mol khí", "định luật khí", "pv = nrt"),
        support_terms=("bình kín", "thể tích", "áp suất", "nhiệt độ", "phân tử va chạm", "áp suất riêng phần"),
        formula_patterns=(r"\bp\s*v\s*=\s*n\s*r\s*t\b",),
        unit_patterns=(r"\b(?:atm|lít|lit|pa)\b",),
        entities=("co2", "o2", "h2", "n2", "heli", "hêli"),
        description="Ideal gas and gas laws; gas entities alone are not Chemistry evidence.",
    ),
    TopicDefinition(
        "physics.thermodynamics.heat_transfer", "physics", "thermodynamics",
        strong_terms=("nhiệt lượng", "truyền nhiệt", "dẫn nhiệt", "nhiệt độ", "bay hơi", "nhiệt học"),
        support_terms=("đun nóng", "làm lạnh", "tỏa nhiệt", "thu nhiệt", "kim loại", "nước nóng"),
        description="Heat, temperature and heat transfer.",
    ),
    TopicDefinition(
        "physics.electricity.circuits", "physics", "electricity",
        strong_terms=("điện trở", "hiệu điện thế", "cường độ dòng điện", "mạch điện", "tụ điện", "dòng điện"),
        support_terms=("mắc nối tiếp", "mắc song song", "dây dẫn", "bóng đèn", "máy biến áp"),
        formula_patterns=(r"\b(?:u\s*=\s*r\s*\.\s*i|i\s*=\s*u\s*/\s*r)\b",),
        unit_patterns=(r"\d+\s*(?:v|a|ohm|ôm|w)\b",),
        description="Electric circuits and quantities.",
    ),
    TopicDefinition(
        "physics.electricity.electromagnetism", "physics", "electricity",
        strong_terms=("cảm ứng điện từ", "lực từ", "điện từ", "điện tích"),
        support_terms=("dòng điện", "từ trường", "cuộn dây"),
        description="Electromagnetism.",
    ),
    TopicDefinition(
        "physics.optics", "physics", "optics",
        strong_terms=("khúc xạ", "gương phẳng", "ảnh ảo", "thấu kính", "phản xạ toàn phần", "pháp tuyến"),
        support_terms=("tia sáng", "ánh sáng", "ảnh thật", "môi trường"),
        description="Geometric optics.",
    ),
    TopicDefinition(
        "physics.waves", "physics", "waves",
        strong_terms=("sóng cơ", "bước sóng", "tần số", "âm thanh", "chân không"),
        support_terms=("môi trường truyền sóng", "dao động"),
        unit_patterns=(r"\bhz\b",),
        description="Waves and sound.",
    ),
    TopicDefinition(
        "physics.oscillation", "physics", "mechanics",
        strong_terms=("dao động điều hòa", "con lắc", "lò xo", "chu kỳ dao động", "biên độ"),
        support_terms=("tần số", "vận tốc cực đại"),
        description="Oscillation.",
    ),

    # Chemistry: owner topics; formula entities are not enough by themselves.
    TopicDefinition(
        "chemistry.atomic_structure", "chemistry", "atomic_structure",
        strong_terms=("nguyên tử", "phân tử", "nguyên tố hóa học", "đơn chất", "hóa trị", "số oxi hóa"),
        support_terms=("electron", "ion", "khối lượng mol"),
        entities=("co2", "o2", "h2", "n2", "h2o", "nacl", "naoh"),
        description="Atomic structure, elements and valence.",
    ),
    TopicDefinition(
        "chemistry.bonds", "chemistry", "chemical_bonds",
        strong_terms=("liên kết ion", "liên kết cộng hóa trị", "liên kết hóa học"),
        support_terms=("ion", "electron hóa trị"),
        description="Chemical bonds.",
    ),
    TopicDefinition(
        "chemistry.reactions", "chemistry", "chemical_reactions",
        strong_terms=("phản ứng hóa học", "cân bằng phương trình", "phản ứng oxi hóa khử", "phản ứng thế", "phản ứng trao đổi", "phản ứng trung hòa", "kết tủa"),
        support_terms=("phản ứng", "phương trình hóa học", "chất tham gia", "sản phẩm"),
        formula_patterns=(r"[a-z0-9]+\s*(?:->|→)\s*[a-z0-9]+",),
        description="Chemical reactions and equations.",
    ),
    TopicDefinition(
        "chemistry.stoichiometry", "chemistry", "stoichiometry",
        strong_terms=("số mol", "mol", "nồng độ mol", "khối lượng mol", "tỉ lệ mol", "thể tích khí"),
        support_terms=("tính khối lượng", "điều kiện tiêu chuẩn", "dung dịch"),
        entities=("co2", "h2", "o2", "n2", "h2o", "caco3", "hcl", "naoh"),
        description="Moles, concentration and stoichiometry.",
    ),
    TopicDefinition(
        "chemistry.acids_bases", "chemistry", "acids_bases",
        strong_terms=("axit", "bazơ", "pH", "quỳ tím", "phenolphthalein", "trung hòa"),
        support_terms=("môi trường axit", "môi trường bazơ", "dung dịch"),
        entities=("hcl", "naoh", "h2so4"),
        description="Acids, bases and indicators.",
    ),
    TopicDefinition(
        "chemistry.organic", "chemistry", "organic_chemistry",
        strong_terms=("hóa học hữu cơ", "đốt cháy hoàn toàn", "nhiên liệu", "cồn", "xăng"),
        support_terms=("carbon", "hydrocarbon", "năng lượng hóa học", "phản ứng cháy"),
        entities=("ch4", "c2h5oh", "co2"),
        description="Organic chemistry and combustion.",
    ),
    TopicDefinition(
        "chemistry.electrochemistry", "chemistry", "electrochemistry",
        strong_terms=("điện phân", "pin điện hóa", "ắc quy", "điện cực", "dòng electron"),
        support_terms=("oxi hóa khử", "nguồn điện", "dung dịch muối"),
        description="Electrochemistry.",
    ),
)

# Error-set additions kept separate from the initial taxonomy declaration so
# each Phase 1 rule remains auditable and easy to map back to a missed case.
_ERROR_SET_EVIDENCE = {
    "math.sequences.arithmetic": ("dãy số",),
    "math.algebra.linear_equation": ("giải phương trình",),
    "math.calculus.derivative": ("hàm số chẵn", "hàm số lẻ"),
    "physics.mechanics.force": ("lực đẩy archimedes", "lực nổi", "archimedes"),
    "physics.energy.work": ("công khí thực hiện",),
    "physics.thermodynamics.ideal_gas": (
        "khí hidro", "khí heli", "lực nổi", "áp suất riêng phần", "động cơ nhiệt",
    ),
    "physics.thermodynamics.heat_transfer": ("tỏa nhiệt", "phản ứng tỏa nhiệt"),
    "physics.electricity.circuits": ("suất điện động",),
    "chemistry.atomic_structure": ("muối ăn", "tan trong nước", "ion hòa tan"),
    "chemistry.reactions": ("oxi hóa - khử", "dãy hoạt động hóa học"),
    "chemistry.stoichiometry": ("nồng độ phần trăm", "phần trăm dung dịch"),
    "chemistry.organic": ("năng lượng phản ứng cháy",),
    "chemistry.electrochemistry": ("dung dịch muối dẫn điện", "ion trong dung dịch"),
}

TOPIC_DEFINITIONS = tuple(
    replace(topic, strong_terms=topic.strong_terms + _ERROR_SET_EVIDENCE.get(topic.topic_id, ()))
    for topic in TOPIC_DEFINITIONS
)

TOPIC_BY_ID = {topic.topic_id: topic for topic in TOPIC_DEFINITIONS}
