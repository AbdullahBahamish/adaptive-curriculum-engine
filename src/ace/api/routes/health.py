"""Health check endpoint — used by load balancers and the C# backend."""
from fastapi import APIRouter
from pydantic import BaseModel

from ace.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    llm_enabled: bool


@router.get("/health", response_model=HealthResponse, summary="Service liveness check")
def health_check() -> HealthResponse:
    """Returns service status. No auth required."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        llm_enabled=settings.llm_enabled,
    )
