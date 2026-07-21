# Router Test Backend

## Hybrid Router V0

`hybrid` là Router Rule-first, LLM-fallback. Request có thể truyền `hybrid_config` để chọn một Rule Router và một OpenRouter LLM Router. Rule được chạy trước; LLM chỉ được gọi khi policy kích hoạt fallback. Nếu LLM lỗi nhưng Rule đã có decision hợp lệ, Hybrid trả lại Rule decision ở degraded mode. Hybrid config được snapshot trong evaluation run và không chứa API key.

Contract mới dùng `fallback_router_id`, hỗ trợ `qwen_v0` qua GPU service và ba OpenRouter Router. `llm_router_id` là alias deprecated. Backend resolve family/model từ registry, kiểm tra `can_be_hybrid_fallback` và availability lúc execute. Qwen health được cache ngắn hạn để router listing không gọi mạng mỗi lần.

## OpenRouter LLM Router V0

Ba router độc lập được cung cấp qua OpenRouter: `llm_deepseek_v0`, `llm_gemini_v0` và `llm_openai_v0`, tương ứng với DeepSeek, Gemini và OpenAI. API key được nhập tại tab OpenRouter Config hoặc cấu hình qua `OPENROUTER_API_KEY`; runtime key chỉ nằm trong memory backend và không được lưu vào file, browser storage hay evaluation artifact.

API Server sử dụng FastAPI làm cầu nối để giao tiếp với các Rule-based Router nguyên gốc (V0, V1, V2).

## Yêu cầu
- Python 3.9+
- `pip`

## Cài đặt dependencies
Tạo môi trường ảo và cài đặt thư viện cần thiết:
```bash
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate

# Cài đặt requirements
pip install -r requirements.txt
# Nếu chưa có python-multipart (cho tính năng Upload), chạy:
pip install python-multipart
```

## Khởi chạy server
Chạy Uvicorn ở cổng 8000:
```bash
python -m uvicorn app.main:app --port 8000
```
Swagger UI có thể xem tại: `http://localhost:8000/docs`

## Các Endpoints chính
- `GET /health`: Kiểm tra trạng thái server.
- `GET /api/v1/routers`: Trả về danh sách Router (rule_v0, rule_v1, rule_v2).
- `POST /api/v1/route`: Gọi một Router duy nhất để xử lý câu hỏi và lịch sử.
- `POST /api/v1/compare`: Chạy đồng thời nhiều Router để lấy kết quả đối chiếu.
- `GET /api/v1/datasets`: Lấy danh sách dataset (mặc định + đã upload).
- `POST /api/v1/datasets/upload`: Upload file dataset `.jsonl` / `.json` mới, tự động validate theo Pydantic schema.
- `POST /api/v1/evaluations`: Chạy batch test hàng loạt trên bộ dataset được chỉ định.
- `GET /api/v1/evaluations/{run_id}/errors`: Truy xuất danh sách lỗi.
- `GET /api/v1/evaluations/{run_id}/analysis`: Phân tích thống kê chi tiết lỗi (Error Analysis Lite).

## Chạy Test
Server cần được tắt trước khi chạy test, hoặc test tự cấu hình test client tùy chỉnh. Dùng pytest hoặc script:
```bash
python tests/test_api_v2.py
python tests/test_all_routers.py
python tests/test_api_compare.py
python tests/test_api_evaluation.py
python tests/test_api_dataset.py
```
