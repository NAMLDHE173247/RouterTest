from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.routing import RouteRequest, RouteResponse, RouterInfo, CompareRequest
from app.services.routing_service import routing_service
from app.openrouter_service_client import OpenRouterServiceError
from app.adapters.hybrid_v0_adapter import HybridRouterError

router = APIRouter()

@router.get("/routers", response_model=List[RouterInfo])
def get_routers():
    return routing_service.get_available_routers()

@router.post("/route", response_model=RouteResponse)
def route_question(request: RouteRequest):
    try:
        response = routing_service.route(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except OpenRouterServiceError as e:
        raise HTTPException(status_code=503, detail={"code": e.code, "message": str(e)})
    except HybridRouterError as e:
        raise HTTPException(status_code=503, detail={"code": e.code, "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/compare")
def compare_routers(request: CompareRequest):
    try:
        results = routing_service.compare_routers(
            router_ids=request.router_ids,
            question=request.question,
            history=request.history,
            hybrid_config=request.hybrid_config,
        )
        return {"comparisons": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
