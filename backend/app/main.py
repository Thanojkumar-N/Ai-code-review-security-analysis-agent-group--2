import os
from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.config.config import settings
from backend.app.database.session import get_db, engine
from backend.app.database.session import Base
from backend.app.api.api import api_router

# Import endpoint logic to map directly to root routes
from typing import List
from backend.app.api.endpoints.submissions import paste_code, upload_code
from backend.app.api.endpoints.system import health_check, system_version
from backend.app.api.endpoints.analysis import CodeAnalysisRequest, CodeAnalysisFindingResponse, analyze_code_endpoint, SecurityAnalysisRequest, SecurityAnalysisFindingResponse, analyze_security_endpoint, ParallelAnalysisRequest, ParallelAnalysisResponse, run_parallel_analysis_endpoint
from backend.app.schemas.submission import SubmissionCreate, SubmissionResponse
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User

# Auto-create tables on startup (sqlite/dev fallback if migrations not run)
# In production, Alembic handles migrations.
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    import logging
    logging.warning(f"Database connection skipped during metadata tables mapping: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend service engine for automated AI Code Review & Security analysis.",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Direct root mapping requirements
@app.get("/health", tags=["Root Direct Endpoints"])
def root_health():
    """Direct root endpoint mapping to get health status."""
    return health_check()

@app.get("/version", tags=["Root Direct Endpoints"])
def root_version():
    """Direct root endpoint mapping to get version information."""
    return system_version()

@app.post("/paste-code", response_model=SubmissionResponse, status_code=201, tags=["Root Direct Endpoints"])
def root_paste_code(
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct root endpoint mapping to copy-paste code snippets for analysis."""
    return paste_code(submission_in=submission_in, db=db, current_user=current_user)

@app.post("/upload", response_model=SubmissionResponse, status_code=201, tags=["Root Direct Endpoints"])
async def root_upload_code(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct root endpoint mapping to upload code archive files for analysis."""
    return await upload_code(project_id=project_id, file=file, db=db, current_user=current_user)

@app.post("/analysis/code", response_model=List[CodeAnalysisFindingResponse], tags=["Root Direct Endpoints"])
def root_analyze_code(
    request: CodeAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Direct root endpoint mapping to analyze code quality and smells."""
    return analyze_code_endpoint(request=request, current_user=current_user)

@app.post("/analysis/security", response_model=List[SecurityAnalysisFindingResponse], tags=["Root Direct Endpoints"])
def root_analyze_security(
    request: SecurityAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Direct root endpoint mapping to analyze code security vulnerabilities."""
    return analyze_security_endpoint(request=request, current_user=current_user)

@app.post("/analysis/run", response_model=ParallelAnalysisResponse, tags=["Root Direct Endpoints"])
def root_analyze_parallel(
    request: ParallelAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Direct root endpoint mapping to run parallel code quality and security analyses."""
    return run_parallel_analysis_endpoint(request=request, current_user=current_user)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API Engine.",
        "docs_url": "/docs"
    }
