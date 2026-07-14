# Qwen Router V0

## 1. Mục tiêu
Dự án này triển khai một SLM-as-Router (Prompt-based) dành cho AI Tutor STEM tiếng Việt.
Hệ thống sử dụng model `Qwen/Qwen2.5-7B-Instruct` để phân tích câu hỏi người học và định tuyến đến các SLM chuyên môn phù hợp (Toán, Lý, Hóa, v.v.).

## 2. Yêu cầu môi trường
* Nền tảng: **Google Colab** (bắt buộc để có GPU miễn phí/tương đương)
* Phần cứng: **GPU T4** hoặc GPU tương đương có hỗ trợ CUDA.
* Phần mềm: Python 3
* Bắt buộc có CUDA khả dụng, mô hình load bằng bitsandbytes 4-bit (NF4).

## 3. Cài đặt
Cài đặt các thư viện yêu cầu:
```bash
pip install -r requirements.txt
```

## 4. Chạy smoke test
Thực thi trực tiếp file `llm_router.py` để kiểm tra khả năng suy luận:
```bash
python llm_router.py
```

## 5. Kết quả dự kiến
Model sẽ nhận diện câu hỏi, sinh text và code sẽ bóc tách để trả về một object JSON theo đúng định dạng `RouterDecision` đã định nghĩa. 
Ví dụ với câu hỏi Vật lý, mong đợi output chứa:
- `primary_subject`: `physics`
- `intent`: `solve_problem`
- `target_slm`: `physics_slm`
- `need_clarification`: `false`

## 6. Giới hạn hiện tại (Giai đoạn V0)
- Chưa có evaluation trên bộ test 300 test case.
- Chưa phân tích lỗi (error analysis).
- Chưa triển khai API bằng FastAPI và ngrok.
- Chưa có fine-tuning, Unsloth, vLLM.
