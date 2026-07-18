from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ==========================================
# Review Findings Schemas
# ==========================================
class FindingBase(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    severity: str        # "Critical", "High", "Medium", "Low", "Info"
    category: str        # "Security", "Performance", "Style", "Bug"
    title: str
    description: str
    recommendation: Optional[str] = None
    code_snippet: Optional[str] = None

class FindingResponse(FindingBase):
    id: str
    report_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# Analysis Report Schemas
# ==========================================
class ReportBase(BaseModel):
    submission_id: str
    summary: Optional[str] = None
    score: int = 100

class ReportResponse(ReportBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReportDetailResponse(ReportResponse):
    findings: List[FindingResponse] = []

    class Config:
        from_attributes = True

# ==========================================
# Report Export Schemas
# ==========================================
class ExportBase(BaseModel):
    report_id: str
    export_type: str    # "PDF", "JSON", "CSV"

class ExportCreate(ExportBase):
    pass

class ExportResponse(ExportBase):
    id: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# Report Chat Schemas
# ==========================================
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ReportChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ReportChatResponse(BaseModel):
    response: str
