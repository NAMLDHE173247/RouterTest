import os
import json
from datetime import datetime
from uuid import uuid4
from typing import List, Tuple, Dict, Any
from app.schemas.dataset import DatasetSample, DatasetMetadata, DatasetErrorDetail, DatasetUploadResponse, DatasetListItem

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DEFAULT_DATASET_PATH = os.path.join(PROJECT_ROOT, "Rule_based_Router/rule_based_router_v2/router_experiment/data/test_router.jsonl")
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "data/uploaded_datasets")

class DatasetService:
    def __init__(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    def list_datasets(self) -> List[DatasetListItem]:
        items = []
        
        # Add default dataset
        default_count = 0
        if os.path.exists(DEFAULT_DATASET_PATH):
            with open(DEFAULT_DATASET_PATH, 'r', encoding='utf-8') as f:
                default_count = sum(1 for line in f if line.strip())
        
        items.append(DatasetListItem(
            dataset_id="default_v2_test_router",
            name="Default test_router.jsonl",
            format="jsonl",
            total_samples=default_count,
            source="default"
        ))

        # Add uploaded datasets
        for fname in os.listdir(UPLOAD_DIR):
            if fname.endswith(".meta.json"):
                with open(os.path.join(UPLOAD_DIR, fname), 'r', encoding='utf-8') as f:
                    try:
                        meta = json.load(f)
                        if meta.get("status") == "valid":
                            items.append(DatasetListItem(
                                dataset_id=meta.get("dataset_id"),
                                name=meta.get("original_filename"),
                                format=meta.get("format"),
                                total_samples=meta.get("valid_samples"),
                                source="uploaded"
                            ))
                    except Exception:
                        pass
        return items

    def get_dataset_path(self, dataset_id: str) -> str:
        if dataset_id == "default_v2_test_router" or not dataset_id:
            return DEFAULT_DATASET_PATH
        
        meta_path = os.path.join(UPLOAD_DIR, f"{dataset_id}.meta.json")
        if not os.path.exists(meta_path):
            raise FileNotFoundError("Dataset not found")
            
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            return os.path.join(UPLOAD_DIR, meta["stored_filename"])

    def validate_and_save(self, filename: str, content: bytes) -> DatasetUploadResponse:
        ext = filename.split(".")[-1].lower()
        if ext not in ["jsonl", "json"]:
            return DatasetUploadResponse(
                filename=filename,
                format=ext,
                total_samples=0,
                valid_samples=0,
                invalid_samples=0,
                status="invalid",
                message="Only .jsonl and .json formats are supported"
            )

        text_content = content.decode("utf-8")
        
        errors = []
        valid_count = 0
        invalid_count = 0
        total_count = 0
        
        parsed_items = []
        
        if ext == "jsonl":
            lines = text_content.splitlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                total_count += 1
                try:
                    data = json.loads(line)
                    DatasetSample(**data) # Validate
                    parsed_items.append(data)
                    valid_count += 1
                except json.JSONDecodeError as e:
                    invalid_count += 1
                    errors.append(DatasetErrorDetail(line=i+1, message=f"JSON Decode Error: {str(e)}"))
                except ValueError as e:
                    invalid_count += 1
                    errors.append(DatasetErrorDetail(line=i+1, message=str(e)))
        elif ext == "json":
            try:
                data = json.loads(text_content)
                if isinstance(data, dict):
                    if "items" in data:
                        data = data["items"]
                    elif "data" in data:
                        data = data["data"]
                    else:
                        raise ValueError("JSON object must contain 'items' or 'data' array")
                
                if not isinstance(data, list):
                    raise ValueError("Root must be a JSON array or contain 'items'/'data' array")
                    
                for i, item in enumerate(data):
                    total_count += 1
                    try:
                        DatasetSample(**item)
                        parsed_items.append(item)
                        valid_count += 1
                    except ValueError as e:
                        invalid_count += 1
                        errors.append(DatasetErrorDetail(line=i+1, message=str(e)))
            except Exception as e:
                return DatasetUploadResponse(
                    filename=filename, format=ext, total_samples=0, valid_samples=0,
                    invalid_samples=1, status="invalid", message=f"Failed to parse JSON: {str(e)}"
                )

        if invalid_count > 0:
            return DatasetUploadResponse(
                filename=filename,
                format=ext,
                total_samples=total_count,
                valid_samples=valid_count,
                invalid_samples=invalid_count,
                status="invalid",
                message="Dataset validation failed",
                errors=errors[:10] # Return top 10 errors
            )
            
        # If fully valid, save it
        dataset_id = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        stored_filename = f"{dataset_id}_{filename}"
        
        # Save dataset file
        file_path = os.path.join(UPLOAD_DIR, stored_filename)
        with open(file_path, "wb") as f:
            f.write(content)
            
        # Save metadata
        meta = DatasetMetadata(
            dataset_id=dataset_id,
            original_filename=filename,
            stored_filename=stored_filename,
            format=ext,
            total_samples=total_count,
            valid_samples=valid_count,
            invalid_samples=invalid_count,
            uploaded_at=datetime.now().isoformat(),
            status="valid"
        )
        
        meta_path = os.path.join(UPLOAD_DIR, f"{dataset_id}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta.model_dump(), f, indent=2, ensure_ascii=False)
            
        return DatasetUploadResponse(
            dataset_id=dataset_id,
            filename=filename,
            format=ext,
            total_samples=total_count,
            valid_samples=valid_count,
            invalid_samples=invalid_count,
            status="valid"
        )

dataset_service = DatasetService()
