import os
import json
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Dict, Any

from prompt import build_messages
from schema import RouterDecision

class RouterGenerationError(Exception):
    """Exception raised when Router fails to generate valid output after retries."""
    pass

class QwenRouter:
    def __init__(
        self, 
        model_name: str = "Qwen/Qwen2.5-7B-Instruct", 
        max_input_tokens: int = 2048, 
        max_new_tokens: int = 256, 
        seed: int = 42
    ):
        self.model_name = model_name
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens
        self.seed = seed
        
        # Kiểm tra môi trường GPU
        if not torch.cuda.is_available():
            raise RuntimeError(
                "GPU không khả dụng. Vui lòng bật GPU trong Google Colab (Runtime -> Change runtime type -> T4 GPU). "
                "Qwen2.5-7B không thể chạy hiệu quả trên CPU cho mục tiêu này."
            )
            
        torch.manual_seed(self.seed)
        
        # Tải tokenizer
        hf_token = os.environ.get("HF_TOKEN")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, token=hf_token)
        
        # Cấu hình 4-bit
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
        
        # Tải model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            token=hf_token
        )
        self.model.eval()
        
    def warmup(self):
        """Warm-up CUDA and model cache with a dummy input."""
        messages = [{"role": "user", "content": "Xin chào"}]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=self.max_input_tokens
        ).to(self.model.device)
        
        with torch.inference_mode():
            _ = self.model.generate(
                **inputs, 
                max_new_tokens=10, 
                do_sample=False, 
                use_cache=True, 
                pad_token_id=self.tokenizer.eos_token_id
            )
            
    def _extract_json(self, raw_text: str) -> dict:
        text = raw_text.strip()
        
        # 1. Thử parse trực tiếp
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # 2. Loại bỏ code fence nếu có
        lines = text.split('\n')
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
        text_no_fence = '\n'.join(lines).strip()
        try:
            return json.loads(text_no_fence)
        except json.JSONDecodeError:
            pass
            
        # 3. Tìm dấu { và } cuối cùng
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
                
        raise ValueError("Không thể trích xuất JSON hợp lệ từ output.")

    def route(self, question: str, history=None, max_retries: int = 2) -> Dict[str, Any]:
        retries = 0
        last_error = None
        last_raw_response = ""
        
        while retries <= max_retries:
            strict = (retries > 0)
            messages = build_messages(question, history, strict=strict)
            
            if strict and last_error:
                truncated_raw = last_raw_response[:800]
                error_context = (
                    "Phản hồi trước không hợp lệ vì lỗi schema sau:\n"
                    f"{last_error}\n\n"
                    "Raw JSON trước đó:\n"
                    f"{truncated_raw}\n\n"
                    "Hãy sửa lại thành đúng JSON object hợp lệ.\n"
                    "Không dùng nhãn con như geometry, algebra, mechanics, pH trong secondary_subjects.\n"
                    "secondary_subjects chỉ được chứa math, physics, chemistry hoặc [] nếu không có môn phụ."
                )
                messages[-1]["content"] += f"\n\n{error_context}"
            
            # Xây prompt
            prompt_text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.tokenizer(
                prompt_text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=self.max_input_tokens
            ).to(self.model.device)
            
            input_length = inputs.input_ids.shape[1]
            
            # Inference và đo latency
            torch.cuda.synchronize()
            start_time = time.perf_counter()
            
            with torch.inference_mode():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    use_cache=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
                
            torch.cuda.synchronize()
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            
            # Tách output mới
            new_tokens = outputs[0][input_length:]
            raw_response = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
            last_raw_response = raw_response
            output_tokens = len(new_tokens)
            
            # JSON Extraction & Validation
            try:
                parsed_json = self._extract_json(raw_response)
                decision = RouterDecision.model_validate(parsed_json)
                
                return {
                    "prediction": decision.model_dump(),
                    "raw_response": raw_response,
                    "model": self.model_name,
                    "latency_ms": latency_ms,
                    "input_tokens": input_length,
                    "output_tokens": output_tokens,
                    "retries": retries,
                    "parse_success": True
                }
            except (json.JSONDecodeError, ValueError) as e:
                last_error = f"Lỗi Parse/Validation: {str(e)}"
                retries += 1
                
        # Nếu vượt quá max_retries
        truncated_response = last_raw_response[:500] + "..." if len(last_raw_response) > 500 else last_raw_response
        raise RouterGenerationError(
            f"Generation thất bại sau {max_retries} retries. Lỗi cuối: {last_error}. Raw response cuối: {truncated_response}"
        )


_ROUTER_INSTANCE = None

def get_router() -> QwenRouter:
    global _ROUTER_INSTANCE
    if _ROUTER_INSTANCE is None:
        _ROUTER_INSTANCE = QwenRouter()
    return _ROUTER_INSTANCE

if __name__ == "__main__":
    print("Khởi tạo router...")
    try:
        router = get_router()
        print("Warmup...")
        router.warmup()
        
        question = "Một vật rơi tự do trong 5 giây, hãy tính vận tốc cuối cùng."
        history = []
        
        print(f"Câu hỏi: {question}")
        print("Routing...")
        result = router.route(question, history=history)
        
        print("\nKết quả:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Lỗi khi chạy smoke test: {e}")
