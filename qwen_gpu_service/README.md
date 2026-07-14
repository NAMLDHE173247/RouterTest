# Qwen GPU Service (Standalone FastAPI)

Đây là microservice độc lập chứa core router của hệ thống AI Tutor. 
Microservice này được thiết kế để triển khai dễ dàng trên Google Colab với tài nguyên GPU miễn phí.

## Thành phần
- `llm_router.py`: Logic gọi model Qwen2.5-7B-Instruct (4-bit).
- `prompt.py`: System prompt cho quyết định routing.
- `schema.py`: Pydantic Models.
- `app.py`: Ứng dụng FastAPI wrapper.
- `run_colab.ipynb`: Notebook để chạy trên Google Colab qua ngrok.

## Cài đặt trên Google Colab

1. Tải thư mục này lên Google Drive hoặc copy `run_colab.ipynb` vào Google Colab.
2. Tại Google Colab:
   - Chọn Runtime -> Change runtime type -> Hardware accelerator: **T4 GPU**
   - Mở thanh bên trái, chọn biểu tượng chìa khóa (Secrets) và thêm:
     - `HF_TOKEN`: API Token của Hugging Face (cần được cấp quyền truy cập Qwen2.5).
     - `NGROK_AUTHTOKEN`: Authtoken từ ngrok.com.
3. Chạy toàn bộ các cell trong Notebook `run_colab.ipynb`.
4. Copy đường dẫn `Ngrok Tunnel URL` ở cell thứ 4 và sử dụng làm Base URL.

## API Endpoints

### `GET /`
Trả về `{"status": "running"}`.

### `GET /health`
Trả về `{"status": "healthy"}`.

### `GET /model/status`
Trả về trạng thái của model:
```json
{
  "model_loaded": true,
  "model_name": "Qwen/Qwen2.5-7B-Instruct",
  "startup_error": null
}
```

### `POST /route`
Nhận vào câu hỏi và lịch sử trò chuyện. Trả về quyết định định tuyến.
**Request**:
```json
{
  "question": "Tính vận tốc của vật rơi tự do trong 5s",
  "history": []
}
```
**Response**:
```json
{
  "router": "qwen_v0",
  "decision": {
    "primary_subject": "physics",
    "secondary_subjects": ["math"],
    "intent": "solve_problem",
    "target_slm": "physics_slm",
    "confidence": 0.9,
    "need_clarification": false,
    "reason": "Bài toán rơi tự do thuộc cơ học."
  },
  "runtime": {
    "latency_ms": 1250,
    "input_tokens": 150,
    "output_tokens": 80,
    "retries": 0,
    "parse_success": true
  },
  "raw_response": "..."
}
```

### `POST /batch-route`
**Request**:
```json
{
  "items": [
    { "question": "Câu 1", "history": [] },
    { "question": "Câu 2", "history": [] }
  ]
}
```
**Response**: Trả về mảng chứa kết quả của từng request.
