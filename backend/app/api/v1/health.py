from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.services.routing_service import routing_service

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="ok",
        available_routers=routing_service.get_available_router_ids()
    )
