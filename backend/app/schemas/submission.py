from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubmissionBase(BaseModel):
    project_id: str
    submission_type: str  # "upload" or "paste"

class SubmissionCreate(SubmissionBase):
    raw_code: Optional[str] = None
    language: Optional[str] = "python"  # "python" or "java"

class SubmissionResponse(SubmissionBase):
    id: str
    user_id: str
    file_path: Optional[str] = None
    raw_code: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from typing import List

class SubmissionPaginatedResponse(BaseModel):
    items: List[SubmissionResponse]
    total: int
    page: int
    size: int
    pages: int
