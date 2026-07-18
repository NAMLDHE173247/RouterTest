# Router Test Frontend

Tab `Hybrid Config` cho phép chọn Rule Router, LLM Router, confidence threshold và các fallback policy. Cùng một cấu hình được dùng trong Playground, Compare và Evaluation; frontend không hiển thị API key.

## OpenRouter Configuration

Tab OpenRouter Config cho phép verify, lưu runtime key trong memory backend và xóa runtime key. Frontend không lưu API key vào localStorage/sessionStorage. Ba LLM Router xuất hiện trong Playground, Compare và Evaluation; chỉ router được chọn mới được gọi.

Web UI cho Router Test Project, được xây dựng bằng Next.js (App Router), TypeScript, và TailwindCSS. 
Thiết kế tập trung vào sự gọn nhẹ, tối ưu UI MVP, không dùng quá nhiều thư viện cấu trúc phức tạp.

## Yêu cầu
- Node.js >= 18
- npm

## Cài đặt
Di chuyển vào thư mục frontend và cài đặt dependencies:
```bash
npm install
```

## Khởi chạy
Đảm bảo đã chạy Backend ở cổng 8000 trước.

Sao chép `.env.example` (nếu có) thành `.env.local` hoặc cấu hình biến môi trường trực tiếp. Mặc định hệ thống gọi `http://127.0.0.1:8000` (được set trong `src/lib/api.ts`).

Chạy server dev:
```bash
npm run dev
```

Mở trình duyệt: `http://localhost:3000`

## Các Mode UI

**1. Single Router**
- Chọn 1 Router bất kỳ (V0, V1, V2).
- Điền Current Question và History (Optional).
- Bấm Run để xem dự đoán Intent, Subject, Target SLM chi tiết bằng thẻ màu.

**2. Compare Routers**
- Chỉ định 1 input duy nhất.
- Chạy qua toàn bộ 3 bản Router đồng thời.
- Highlight tự động các thuộc tính nào có sự sai lệch (khác biệt) giữa các Router (viền vàng nổi bật).

**3. Evaluation Dashboard & Analysis**
- Bấm nút "Run Evaluation on Dataset" để hệ thống ném toàn bộ file dataset qua các Router.
- **Upload Dataset**: Hỗ trợ tải file JSONL / JSON qua nút Choose File. Dataset được validate ngay lập tức, báo lỗi nếu sai cấu trúc. Dataset hợp lệ sẽ vào Select Box.
- Bảng tổng hợp Metrics hiển thị % chính xác, tô màu xanh (`highlight`) những thông số cao nhất.
- Bảng Analysis bóc tách kỹ lỗi False Positive/Negative và Confusion Matrix.
- Bảng lọc lỗi chi tiết theo từng Router và Case Type. 
