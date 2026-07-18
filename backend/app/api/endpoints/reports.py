from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.report import ReportResponse, ReportDetailResponse, ExportResponse, ExportCreate, FindingResponse
from backend.app.services.analysis_service import AnalysisService
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User
from backend.app.models.finding import ReviewFinding
from backend.app.models.report import AnalysisReport
from backend.app.models.submission import CodeSubmission

router = APIRouter()

@router.get("/project/{project_id}/findings", response_model=list[FindingResponse])
def list_project_findings(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all findings across all reports inside a project container."""
    return db.query(ReviewFinding)\
        .join(AnalysisReport, ReviewFinding.report_id == AnalysisReport.id)\
        .join(CodeSubmission, AnalysisReport.submission_id == CodeSubmission.id)\
        .filter(CodeSubmission.project_id == project_id)\
        .all()

@router.get("/project/{project_id}", response_model=list[ReportResponse])
def list_project_reports(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all reports associated with a specific project context."""
    return AnalysisService.get_project_reports(db, project_id)

@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report_details(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch report details, including individual security and style findings."""
    try:
        return AnalysisService.get_report_details(db, report_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/{report_id}/export", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
def export_report(
    report_id: str,
    export_in: ExportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export security report findings in CSV, JSON, or PDF configuration."""
    if export_in.report_id != report_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report ID mismatch"
        )
    try:
        return AnalysisService.generate_report_export(db, report_id, export_in.export_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

from backend.app.schemas.report import ReportChatRequest, ReportChatResponse
from backend.app.models.submission import CodeSubmission
import os

@router.post("/{report_id}/chat", response_model=ReportChatResponse)
def chat_with_report(
    report_id: str,
    chat_in: ReportChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Interact with the conversation agent regarding the report's security review findings."""
    report = AnalysisService.get_report_details(db, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        
    submission = db.query(CodeSubmission).filter(CodeSubmission.id == report.submission_id).first()
    if not submission or submission.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # 1. Recover source code context
    code = ""
    filename = "main.py"
    if submission.submission_type == "paste":
        code = submission.raw_code or ""
        if "public class " in code or "System.out" in code:
            filename = "Main.java"
    else:
        if submission.file_path and os.path.exists(submission.file_path):
            filename = os.path.basename(submission.file_path)
            try:
                with open(submission.file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
            except Exception:
                code = ""

    # 2. Reconstruct code analysis states
    code_analysis = {
        "lines_count": len(code.split("\n")),
        "functions_count": len([f for f in report.findings if "method" in f.title.lower() or "function" in f.title.lower()]),
        "classes_count": len([f for f in report.findings if "class" in f.title.lower()]),
        "complexity_rating": "Scanned Code Block",
        "complexity_score": 5
    }

    # 3. Reconstruct security vulnerability details
    vulnerabilities = []
    for f in report.findings:
        vulnerabilities.append({
            "id": f"SEC-{f.line_number}",
            "line": f.line_number,
            "title": f.title,
            "severity": f.severity,
            "classification": f.category,
            "description": f.description,
            "snippet": f.code_snippet
        })

    # 4. Map chat history list to matching formats
    history = [{"role": h.role, "content": h.content} for h in chat_in.conversation_history]

    # 5. Invoke the Conversation Agent Graph
    from backend.app.agents.orchestrator import get_conversation_workflow
    workflow = get_conversation_workflow()
    
    try:
        result = workflow.invoke({
            "code": code,
            "language": "java" if filename.lower().endswith(".java") else "python",
            "code_analysis": code_analysis,
            "security_analysis": {"vulnerabilities": vulnerabilities},
            "chat_message": chat_in.message,
            "conversation_history": history
        })
        chat_response = result.get("chat_response", "Sorry, I am unable to analyze that query.")
    except Exception as e:
        chat_response = f"Conversation engine error: {str(e)}"

    return ReportChatResponse(response=chat_response)
