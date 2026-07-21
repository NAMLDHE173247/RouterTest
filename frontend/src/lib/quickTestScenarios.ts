import { QuickTestScenario } from '@/types/router';

export const QUICK_TEST_SCENARIOS: QuickTestScenario[] = [
  {
    id: 'basic-math-solve',
    title: 'Toán · Giải bài',
    group: 'basic',
    question: 'Giải phương trình (x^2 - 5x + 6 = 0).',
    history: [],
    expectedRoute: { primarySubject: 'math', secondarySubjects: [], intent: 'solve_problem', targetSlm: 'math_slm', needClarification: false },
    expectedHybridBehavior: 'Rule thường đủ tự tin; fallback phụ thuộc threshold hiện tại.',
    note: 'Kiểm tra đường đi cơ bản cho bài Toán.'
  },
  {
    id: 'basic-physics-explain',
    title: 'Vật lý · Giải thích',
    group: 'basic',
    question: 'Vì sao một vật rơi tự do lại có vận tốc tăng dần?',
    history: [],
    expectedRoute: { primarySubject: 'physics', secondarySubjects: [], intent: 'explain_concept', targetSlm: 'physics_slm', needClarification: false },
    expectedHybridBehavior: 'Rule thường xử lý trực tiếp nếu confidence đủ cao.',
    note: 'Kiểm tra intent explain_concept.'
  },
  {
    id: 'basic-chemistry-check',
    title: 'Hóa học · Kiểm tra',
    group: 'basic',
    question: 'Em tính pH của dung dịch HCl 0,01 M là 2, kết quả này đúng không?',
    history: [],
    expectedRoute: { primarySubject: 'chemistry', secondarySubjects: ['math'], intent: 'check_answer', targetSlm: 'chemistry_slm', needClarification: false },
    expectedHybridBehavior: 'Có thể fallback nếu Rule confidence thấp ở câu liên môn.',
    note: 'Hóa học là môn chính, Toán là công cụ phụ.'
  },
  {
    id: 'basic-math-hint',
    title: 'Toán · Xin gợi ý',
    group: 'basic',
    question: 'Gợi ý cho em cách bắt đầu bài tìm giá trị lớn nhất của hàm số này, đừng giải hết.',
    history: [],
    expectedRoute: { primarySubject: 'math', secondarySubjects: [], intent: 'give_hint', targetSlm: 'math_slm', needClarification: false },
    expectedHybridBehavior: 'Rule có thể chọn trực tiếp nếu nhận diện rõ intent.',
    note: 'Phân biệt give_hint với solve_problem.'
  },
  {
    id: 'basic-physics-diagnose',
    title: 'Vật lý · Tìm lỗi sai',
    group: 'basic',
    question: 'Em tính công cơ học bằng (A = F/s), em sai ở đâu?',
    history: [],
    expectedRoute: { primarySubject: 'physics', secondarySubjects: ['math'], intent: 'diagnose_error', targetSlm: 'physics_slm', needClarification: false },
    expectedHybridBehavior: 'Có thể fallback nếu Rule nhầm diagnose_error thành check_answer.',
    note: 'Kiểm tra khả năng chẩn đoán lỗi trong lời giải.'
  },
  {
    id: 'basic-follow-up',
    title: 'Multi-turn · Hỏi tiếp',
    group: 'basic',
    question: 'Công thức này dùng trong trường hợp nào vậy ạ?',
    history: ['Em đang học về chuyển động rơi tự do.', 'Em thấy công thức s = 1/2 × g × t².'],
    expectedRoute: { primarySubject: 'physics', secondarySubjects: ['math'], intent: 'ask_follow_up', targetSlm: 'physics_slm', needClarification: false },
    expectedHybridBehavior: 'History giúp Rule xác định subject; fallback tùy confidence.',
    note: 'Kiểm tra intent hỏi tiếp dựa trên history.'
  },
  {
    id: 'challenge-ambiguous',
    title: 'Mơ hồ · Cần hỏi lại',
    group: 'hybrid_challenge',
    question: 'Chỗ này làm tiếp như thế nào ạ?',
    history: [],
    expectedRoute: { primarySubject: 'unknown', secondarySubjects: [], intent: 'ask_follow_up', targetSlm: 'ask_clarification', needClarification: true },
    expectedHybridBehavior: 'Có thể trigger fallback vì unknown_subject hoặc need_clarification nếu các trigger đang bật.',
    note: 'Rule clarification có thể đã là quyết định hợp lệ; không mặc định fallback luôn xảy ra.'
  },
  {
    id: 'challenge-out-of-scope',
    title: 'Ngoài phạm vi STEM',
    group: 'hybrid_challenge',
    question: 'Viết giúp em một email xin nghỉ học ngày mai.',
    history: [],
    expectedRoute: { primarySubject: 'unknown', secondarySubjects: [], intent: 'unknown', targetSlm: 'general_tutor', needClarification: false },
    expectedHybridBehavior: 'Có thể trigger fallback khi subject unknown tùy cấu hình Hybrid.',
    note: 'Phân biệt general_tutor với ask_clarification.'
  },
  {
    id: 'challenge-physics-math',
    title: 'Liên môn · Lý + Toán',
    group: 'hybrid_challenge',
    question: 'Dùng phương trình bậc hai để tính thời gian vật chạm đất từ độ cao 45 m.',
    history: [],
    expectedRoute: { primarySubject: 'physics', secondarySubjects: ['math'], intent: 'solve_problem', targetSlm: 'physics_slm', needClarification: false },
    expectedHybridBehavior: 'Có thể trigger low_confidence nếu Rule khó xác định môn chính và môn phụ.',
    note: 'Kiểm tra primary subject và secondary subject trong câu liên môn.'
  },
  {
    id: 'challenge-history-follow-up',
    title: 'Multi-turn · Phụ thuộc history',
    group: 'hybrid_challenge',
    question: 'Vậy tại sao chỗ này lại nhân với một phần hai?',
    history: ['Em đang làm bài vật rơi tự do.', 'Em dùng công thức s = 1/2 × g × t².'],
    expectedRoute: { primarySubject: 'physics', secondarySubjects: ['math'], intent: 'ask_follow_up', targetSlm: 'physics_slm', needClarification: false },
    expectedHybridBehavior: 'Có thể trigger low_confidence nếu không tận dụng được history.',
    note: 'Dùng đại từ và ngữ cảnh trước đó để kiểm tra khả năng nối hội thoại.'
  },
  {
    id: 'challenge-subject-switch',
    title: 'Multi-turn · Chuyển môn',
    group: 'hybrid_challenge',
    question: 'Bây giờ cân bằng phương trình H₂ + O₂ → H₂O giúp em.',
    history: ['Trước đó em đang tính vận tốc của một vật chuyển động thẳng.'],
    expectedRoute: { primarySubject: 'chemistry', secondarySubjects: [], intent: 'solve_problem', targetSlm: 'chemistry_slm', needClarification: false },
    expectedHybridBehavior: 'Không nên giữ subject cũ; fallback chỉ phụ thuộc policy và confidence hiện tại.',
    note: 'Evidence trong câu hiện tại phải thắng subject cũ trong history.'
  },
  {
    id: 'challenge-noisy-vietnamese',
    title: 'Mơ hồ · Tiếng Việt thiếu dấu',
    group: 'hybrid_challenge',
    question: 'giai thich giup em bai nay voi a em khong hieu lam',
    history: [],
    expectedRoute: { primarySubject: 'unknown', secondarySubjects: [], intent: 'unknown', targetSlm: 'ask_clarification', needClarification: true },
    expectedHybridBehavior: 'Có khả năng trigger low_confidence hoặc need_clarification tùy kết quả Rule.',
    note: 'Smoke test cho câu tiếng Việt nhiễu, viết tắt hoặc thiếu dấu.'
  },
  {
    id: 'challenge-wrong-solution',
    title: 'Tình huống · Học sinh làm sai',
    group: 'hybrid_challenge',
    question: 'Em làm bài này ra kết quả 49 m/s nhưng không chắc, em sai ở đâu?',
    history: ['Một vật rơi tự do trong 5 giây, lấy g = 9,8 m/s².'],
    expectedRoute: { primarySubject: 'physics', secondarySubjects: ['math'], intent: 'diagnose_error', targetSlm: 'physics_slm', needClarification: false },
    expectedHybridBehavior: 'Có thể fallback nếu Rule phân vân giữa diagnose_error và check_answer.',
    note: 'Kiểm tra phân biệt chẩn đoán lỗi với kiểm tra đáp án.'
  }
];

export const QUICK_TEST_SCENARIO_GROUPS = [
  { id: 'basic' as const, title: 'Câu cơ bản', description: 'Các intent và subject thường gặp.' },
  { id: 'hybrid_challenge' as const, title: 'Tình huống khó cho Hybrid', description: 'Các câu dễ tạo khác biệt giữa Rule và fallback.' }
];
