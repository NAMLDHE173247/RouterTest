# Router Test Project

Dự án này là môi trường kiểm thử và phân tích cho các thuật toán Router (Routing Service). Mục tiêu là chuyển đổi kiến trúc Router Test thành một hệ thống Client-Server gọn nhẹ, dễ dàng kiểm tra, so sánh và đánh giá các phiên bản Router khác nhau.

## Kiến trúc (Architecture)
Hệ thống được chia thành 3 phần chính:
1. **Frontend (Next.js)**: Giao diện người dùng Playground, Compare và Evaluation Dashboard.
2. **Backend (FastAPI)**: API server cung cấp các endpoint, xử lý logic dataset, chạy test, tính toán metrics.
3. **Core Adapters**: Nạp động (dynamic loading) các Rule-based Router (V0, V1, V2) nguyên bản mà không làm thay đổi hay phá vỡ module tĩnh ban đầu.

## Các Router hỗ trợ
- `rule_v0`: Phiên bản cơ sở (Base).
- `rule_v1`: Cập nhật logic phụ.
- `rule_v2`: Tối ưu nhận dạng Intent và Subject đa môn.

## Cấu trúc thư mục
- `/backend`: Mã nguồn API server (FastAPI).
- `/frontend`: Mã nguồn giao diện Web (Next.js).
- `/Rule_based_Router`: Nguồn chứa bộ Core Router nguyên bản không chỉnh sửa.
- `/data/evaluation_runs`: Nơi lưu kết quả đánh giá (metrics, errors, analysis).
- `/data/uploaded_datasets`: Nơi lưu dataset tùy chỉnh do người dùng upload.

## Yêu cầu định dạng Dataset (.jsonl hoặc .json)
Mỗi sample cần chứa đầy đủ các trường sau (dành cho Evaluation):
- `id`: Định danh câu hỏi.
- `question`: Nội dung câu hỏi.
- `history`: Danh sách hội thoại trước đó (array).
- `primary_subject`: `math`, `physics`, `chemistry`, `unknown`
- `secondary_subjects`: Array chứa các môn liên quan.
- `intent`: `solve_problem`, `explain_concept`, v.v...
- `target_slm`: `math_slm`, `general_tutor`, v.v...
- `need_clarification`: `true` hoặc `false`.
- `case_type`: Loại case (ví dụ: `interdisciplinary`).

## Các tính năng
1. **Single Router (Playground)**: Nhập câu hỏi và xem chi tiết dự đoán (raw JSON, badge).
2. **Compare Routers**: So sánh trực tiếp 3 Router V0, V1, V2 với cùng một input. Hiển thị highlight khác biệt.
3. **Evaluation Dashboard**: Đánh giá trên bộ dataset hàng loạt. Có bảng highlight best metrics.
4. **Error Analysis Lite**: Ma trận nhầm lẫn (confusion matrix), lỗi theo field, false positive / negative.
5. **Upload Dataset**: Upload file `.jsonl` hoặc `.json`, tự động validate schema và kiểm tra kết quả ngay lập tức.

## Hướng dẫn chạy

**1. Khởi động Backend**
Xem hướng dẫn chi tiết tại `backend/README.md`.
```bash
cd backend
python -m venv .venv
# Kích hoạt venv (Windows: .venv\Scripts\activate, Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

**2. Khởi động Frontend**
Xem hướng dẫn chi tiết tại `frontend/README.md`.
```bash
cd frontend
npm install
npm run dev
```
Truy cập `http://localhost:3000`.

## Technical Debt (Nợ kỹ thuật) & Hướng phát triển
- **Isolated Modules**: Các adapter hiện tại phải load module thông qua `importlib` và `sys.modules` caching (dirty hack) vì các thư mục V0, V1, V2 chưa được đóng gói chuẩn thành Python package (thiếu `__init__.py`).
- **Synchronous Evaluation**: Hệ thống eval đang chạy đồng bộ (Synchronous). Dù đủ cho Rule-based Router (do tốc độ rất cao ~0.2ms/sample), nhưng khi mở rộng sang Qwen Router hay LLM-based, cần chuyển sang Message Queue (Celery/RabbitMQ) hoặc Background Tasks bất đồng bộ.
- **Dataset Storage**: File dataset upload và output đang lưu vào Local Disk Storage (FileSystem). Trong production cần chuyển lên S3 / GCS hoặc lưu database (PostgreSQL/MongoDB).
- **Hỗ trợ thêm định dạng**: Tạm thời MVP chỉ hỗ trợ `.json` và `.jsonl`. Sẽ cần mở rộng sang `.csv` sau.
