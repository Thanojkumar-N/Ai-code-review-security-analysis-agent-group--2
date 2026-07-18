from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from backend.app.database.session import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User
from backend.app.models.project import Project
from backend.app.models.submission import CodeSubmission
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectPaginatedResponse
from backend.app.schemas.submission import SubmissionResponse, SubmissionPaginatedResponse

router = APIRouter()

@router.get("", response_model=ProjectPaginatedResponse)
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search query matching project title or description"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, name)"),
    sort_order: str = Query("desc", description="Sorting direction (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """Retrieve user projects list with search, sorting, and pagination filters."""
    query = db.query(Project).filter(Project.user_id == current_user.id)

    # 1. Search Query filter
    if search and search.strip():
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            (Project.name.ilike(search_filter)) | 
            (Project.description.ilike(search_filter))
        )

    # 2. Sort Logic
    sort_field = Project.created_at
    if sort_by.lower() == "name":
        sort_field = Project.name

    if sort_order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())

    # 3. Paginate
    total = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 0

    return ProjectPaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project container."""
    # Check duplicate names within user projects
    existing = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.name == project_in.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists in your workspace"
        )

    project = Project(
        name=project_in.name,
        description=project_in.description,
        user_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch metadata details for a specific project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your workspace"
        )
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify details (name, description) of a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your workspace"
        )

    if project_in.name is not None:
        # Prevent renaming to a duplicate project name
        existing = db.query(Project).filter(
            Project.user_id == current_user.id,
            Project.name == project_in.name,
            Project.id != project_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another project with this name already exists in your workspace"
            )
        project.name = project_in.name
    
    if project_in.description is not None:
        project.description = project_in.description

    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permanently delete a project container and all cascade-related items."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your workspace"
        )
    db.delete(project)
    db.commit()
    return None

@router.get("/{project_id}/submissions", response_model=SubmissionPaginatedResponse)
def list_project_submissions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    submission_type: Optional[str] = Query(None, description="Filter by paste or upload"),
    status: Optional[str] = Query(None, description="Filter by pending, completed, or failed status"),
    page: int = Query(1, ge=1),
    size: int = Query(5, ge=1, le=100)
):
    """Retrieve submissions associated with a project, with page/status/type filters."""
    # Ensure project owner verification
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your workspace"
        )

    query = db.query(CodeSubmission).filter(CodeSubmission.project_id == project_id)

    # 1. Type Filter
    if submission_type and submission_type.strip():
        query = query.filter(CodeSubmission.submission_type == submission_type.strip())

    # 2. Status Filter
    if status and status.strip():
        query = query.filter(CodeSubmission.status == status.strip())

    # Sort by created_at desc
    query = query.order_by(CodeSubmission.created_at.desc())

    # 3. Paginate
    total = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    pages = math.ceil(total / size) if total > 0 else 0

    return SubmissionPaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )
