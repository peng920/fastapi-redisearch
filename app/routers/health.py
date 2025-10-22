from fastapi import APIRouter
from datetime import datetime

from app.models.schemas import HealthResponse
from app.services.redis_client import vector_search
from app.services.embedding_service import embedding_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    redis_connected = vector_search.health_check()
    model_loaded = embedding_service.model is not None

    overall_status = "healthy" if redis_connected and model_loaded else "unhealthy"

    return HealthResponse(
        status=overall_status,
        redis_connected=redis_connected,
        model_loaded=model_loaded,
        timestamp=datetime.now()
    )