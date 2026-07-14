from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.routing import RouteRequest, RouteResponse, RouterInfo, CompareRequest
from app.services.routing_service import routing_service

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/compare")
def compare_routers(request: CompareRequest):
    try:
        results = routing_service.compare_routers(
            router_ids=request.router_ids,
            question=request.question,
            history=request.history
        )
        return {"comparisons": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
