from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.submission import SubmissionCreate, SubmissionResponse
from backend.app.schemas.project import ProjectCreate, ProjectResponse
from backend.app.services.submission_service import SubmissionService
from backend.app.services.analysis_service import AnalysisService
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User

router = APIRouter()

@router.get("/projects", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all projects belonging to the logged-in user."""
    return SubmissionService.get_user_projects(db, current_user.id)

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Create a new project container."""
    return SubmissionService.create_project(db, project_in.name, project_in.description, current_user.id)

@router.post("/paste-code", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def paste_code(
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit raw code contents via copy-paste. Automatically triggers security analysis."""
    if not submission_in.raw_code or not submission_in.raw_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pasted code content cannot be empty"
        )
    
    # Create database submission record
    submission = SubmissionService.create_paste_submission(
        db=db,
        project_id=submission_in.project_id,
        raw_code=submission_in.raw_code,
        user_id=current_user.id,
        language=submission_in.language or "python"
    )

    # Immediately trigger mock security analysis
    AnalysisService.trigger_mock_analysis(db=db, submission_id=submission.id)
    
    # Refresh to return updated record status
    db.refresh(submission)
    return submission

@router.post("/upload", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def upload_code(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit code files (zip, tar, or raw scripts) via file upload. Automatically triggers security analysis."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File upload payload must have a valid filename"
        )

    # Save file and write record
    submission = await SubmissionService.create_file_submission(
        db=db,
        project_id=project_id,
        file=file,
        user_id=current_user.id
    )

    # Immediately trigger mock security analysis
    AnalysisService.trigger_mock_analysis(db=db, submission_id=submission.id)

    db.refresh(submission)
    return submission
