import requests
import json

def test_evaluation():
    url = "http://127.0.0.1:8000/api/v1/evaluations"
    payload = {
        "router_ids": ["rule_v0", "rule_v1", "rule_v2"]
    }
    
    print("Running evaluation (this may take a few seconds)...")
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        run_id = data.get("run_id")
        
        print(f"\n--- Fetching Summary for {run_id} ---")
        res_summary = requests.get(f"{url}/{run_id}")
        print(json.dumps(res_summary.json(), indent=2, ensure_ascii=False))
        
        print(f"\n--- Fetching Metrics for {run_id} ---")
        res_metrics = requests.get(f"{url}/{run_id}/metrics")
        print("Metrics fetched successfully")
        
        print(f"\n--- Fetching Errors for {run_id} ---")
        res_errors = requests.get(f"{url}/{run_id}/errors")
        print("Errors fetched successfully")
        
        print(f"\n--- Fetching Analysis for {run_id} ---")
        res_analysis = requests.get(f"{url}/{run_id}/analysis")
        if res_analysis.status_code == 200:
            print("Analysis fetched successfully:")
            analysis_data = res_analysis.json()
            print("Total errors by router:", analysis_data.get("total_errors_by_router"))
        else:
            print("Failed to fetch analysis:", res_analysis.text)
    else:
        print("Failed:", response.text)

if __name__ == "__main__":
    test_evaluation()
