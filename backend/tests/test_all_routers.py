import requests
import json

def test_routers():
    url = "http://127.0.0.1:8000/api/v1/route"
    payload = {
        "question": "Một vật rơi tự do trong 5 giây, tính vận tốc cuối cùng.",
        "history": []
    }
    
    for router_id in ["rule_v0", "rule_v1", "rule_v2"]:
        payload["router_id"] = router_id
        response = requests.post(url, json=payload)
        print(f"--- {router_id} ---")
        print("Status Code:", response.status_code)
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_routers()
