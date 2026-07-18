from fastapi import APIRouter
from backend.app.api.endpoints.auth import router as auth_router
from backend.app.api.endpoints.submissions import router as submissions_router
from backend.app.api.endpoints.reports import router as reports_router
from backend.app.api.endpoints.system import router as system_router
from backend.app.api.endpoints.projects import router as projects_router

api_router = APIRouter()

# Grouping all routes under distinct resource spaces
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(submissions_router, prefix="/submissions", tags=["Code Submissions"])
api_router.include_router(projects_router, prefix="/projects", tags=["Project Containers"])
api_router.include_router(reports_router, prefix="/reports", tags=["Analysis Reports"])
api_router.include_router(system_router, prefix="/system", tags=["System Operational Info"])
