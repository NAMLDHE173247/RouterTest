import requests
import json

def test_compare():
    url = "http://127.0.0.1:8000/api/v1/compare"
    payload = {
        "question": "Một vật rơi tự do trong 5 giây, tính vận tốc cuối cùng.",
        "history": []
    }
    
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_compare()
