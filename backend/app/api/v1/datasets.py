from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.schemas.dataset import DatasetUploadResponse, DatasetListItem
from app.services.dataset_service import dataset_service

router = APIRouter()

@router.get("", response_model=List[DatasetListItem])
def list_datasets():
    try:
        return dataset_service.list_datasets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    try:
        content = await file.read()
        MAX_SIZE = 10 * 1024 * 1024 # 10MB
        if len(content) > MAX_SIZE:
            return DatasetUploadResponse(
                filename=file.filename,
                format="unknown",
                total_samples=0,
                valid_samples=0,
                invalid_samples=0,
                status="invalid",
                message="File size exceeds 10MB limit"
            )
            
        res = dataset_service.validate_and_save(file.filename, content)
        if res.status == "invalid":
            # the user wants 400 or just the response?
            # returning 400 with the response is cleaner.
            raise HTTPException(status_code=400, detail=res.model_dump())
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
