from fastapi import APIRouter, HTTPException
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.services.evaluation_service import evaluation_service

router = APIRouter()

@router.post("", response_model=EvaluationResponse)
def run_evaluation(request: EvaluationRequest):
    try:
        return evaluation_service.run_evaluation(
            request.router_ids,
            request.dataset_id,
            request.limit,
            request.hybrid_config,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{run_id}")
def get_evaluation_summary(run_id: str):
    try:
        return evaluation_service.get_summary(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{run_id}/metrics")
def get_evaluation_metrics(run_id: str):
    try:
        return evaluation_service.get_metrics(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Metrics not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{run_id}/errors")
def get_evaluation_errors(run_id: str):
    try:
        return evaluation_service.get_errors(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Errors not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{run_id}/analysis")
def get_evaluation_analysis(run_id: str):
    try:
        return evaluation_service.get_analysis(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Errors not found for analysis")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
