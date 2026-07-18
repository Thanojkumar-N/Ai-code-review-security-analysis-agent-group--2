from fastapi import APIRouter
from backend.app.config.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    """Verify that the FastAPI system status is active."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"  # database status check mock
    }

@router.get("/version")
def system_version():
    """Fetch current release metadata details."""
    return {
        "version": settings.VERSION,
        "project_name": settings.PROJECT_NAME
    }
