# Hướng dẫn chạy Qwen Router GPU Service trên Google Colab

Qwen Router Service yêu cầu GPU có dung lượng VRAM ít nhất 15GB (T4 GPU trên Google Colab là lựa chọn phù hợp) để chạy mô hình `Qwen/Qwen2.5-7B-Instruct` với cấu hình 4-bit quantization.

## Các bước chạy

1. **Khởi tạo Colab Notebook**:
   - Mở [Google Colab](https://colab.research.google.com/).
   - Chọn **Runtime > Change runtime type > T4 GPU**.

2. **Clone source code và di chuyển vào thư mục**:
   ```bash
   !git clone https://github.com/NAMLDHE173247/RouterTest.git
   %cd RouterTest/qwen_router_v0
   ```

3. **Cài đặt thư viện**:
   ```bash
   !pip install -r requirements.txt
   ```
   *Lưu ý: Không bắt buộc cài đặt `unsloth` trừ khi bạn có nhu cầu fine-tune.*

4. **Cấu hình biến môi trường**:
   - Đặt Token Hugging Face của bạn để tải mô hình.
   - Lấy ngrok auth token từ [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).
   
   ```python
   import os
   os.environ["HF_TOKEN"] = "hf_xxx" # Thay token của bạn vào đây
   os.environ["NGROK_AUTHTOKEN"] = "ngrok_xxx" # Thay token ngrok vào đây
   os.environ["USE_UNSLOTH"] = "false"
   os.environ["ALLOWED_ORIGINS"] = "*"
   ```

5. **Mở port Ngrok & Chạy Server**:
   Sử dụng cell sau trong Colab để mở ngrok và khởi chạy FastAPI server chạy ngầm:
   ```python
   from pyngrok import ngrok
   import os

   # Ngắt các tunnel cũ nếu có
   ngrok.kill()
   
   # Mở tunnel mới port 5000
   public_url = ngrok.connect(5000).public_url
   print("=" * 50)
   print(f"👉 QWEN SERVICE URL CỦA BẠN: {public_url}")
   print("=> Copy URL này và dán vào Frontend Config!")
   print("=" * 50)
   
   # Chạy uvicorn server
   !uvicorn app:app --host 0.0.0.0 --port 5000
   ```

## Test API

Sau khi server khởi chạy và báo đã load mô hình thành công, bạn có thể gửi test từ terminal local hoặc Postman:

**Test Health Check:**
```bash
curl -X GET "<URL_NGROK>/health"
```

**Test Route Endpoint:**
```bash
curl -X POST "<URL_NGROK>/route" \
     -H "Content-Type: application/json" \
     -d '{"question":"Một vật rơi tự do trong 5 giây, hãy tính vận tốc cuối cùng.","history":[]}'
```
