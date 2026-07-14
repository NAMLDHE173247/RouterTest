import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_dataset_upload_and_list():
    # 1. Create a dummy invalid JSONL file
    invalid_data = """{"id": "q1", "question": "test", "history": [], "primary_subject": "invalid_subject", "secondary_subjects": [], "intent": "unknown", "target_slm": "math_slm", "need_clarification": false, "case_type": "single_turn"}
{"invalid_json"""
    
    with open("test_invalid.jsonl", "w") as f:
        f.write(invalid_data)
        
    print("--- Uploading invalid dataset ---")
    with open("test_invalid.jsonl", "rb") as f:
        res = requests.post(f"{BASE_URL}/datasets/upload", files={"file": ("test_invalid.jsonl", f, "application/json")})
        print(f"Status: {res.status_code}")
        print(res.json())
        assert res.status_code == 400
        
    # 2. Create a dummy valid JSON file
    valid_data = [
        {
            "id": "q1",
            "question": "1+1=?",
            "history": [],
            "primary_subject": "math",
            "secondary_subjects": [],
            "intent": "solve_problem",
            "target_slm": "math_slm",
            "need_clarification": False,
            "case_type": "single_turn"
        }
    ]
    with open("test_valid.json", "w") as f:
        json.dump(valid_data, f)
        
    print("\n--- Uploading valid dataset ---")
    with open("test_valid.json", "rb") as f:
        res = requests.post(f"{BASE_URL}/datasets/upload", files={"file": ("test_valid.json", f, "application/json")})
        print(f"Status: {res.status_code}")
        res_data = res.json()
        print(res_data)
        assert res.status_code == 200
        dataset_id = res_data["dataset_id"]
        
    print("\n--- Listing datasets ---")
    res = requests.get(f"{BASE_URL}/datasets")
    print(f"Status: {res.status_code}")
    list_data = res.json()
    print(list_data)
    assert any(d["dataset_id"] == dataset_id for d in list_data)
    
    # 3. Clean up
    os.remove("test_invalid.jsonl")
    os.remove("test_valid.json")
    
    print("\n--- Test Evaluation with custom dataset ---")
    payload = {
        "router_ids": ["rule_v2"],
        "dataset_id": dataset_id
    }
    res = requests.post(f"{BASE_URL}/evaluations", json=payload)
    print(f"Status: {res.status_code}")
    print(res.json())
    assert res.status_code == 200

if __name__ == "__main__":
    test_dataset_upload_and_list()
