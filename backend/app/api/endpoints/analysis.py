from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User
from backend.app.agents.code_analysis_agent import analyze_python_ast, analyze_java_lexical
from backend.app.agents.security_agent import ScannerRegistry
from backend.app.utils.syntax_validator import validate_code_syntax

router = APIRouter()

class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., description="The source code contents to analyze.")
    language: str = Field(..., description="The language of the code ('python' or 'java').")

class CodeAnalysisFindingResponse(BaseModel):
    id: str
    title: str
    description: str
    language: str
    severity: str
    category: str
    line_number: int
    code_snippet: str
    explanation: str
    recommendation: str

class SecurityAnalysisRequest(BaseModel):
    code: str = Field(..., description="The source code contents to analyze.")
    language: str = Field(..., description="The language of the code ('python' or 'java').")
    filename: Optional[str] = Field(None, description="The name of the file being analyzed.")

class SecurityAnalysisFindingResponse(BaseModel):
    issue_name: str = Field(..., alias="Issue Name")
    owasp_category: str = Field(..., alias="OWASP Category")
    severity: str = Field(..., alias="Severity")
    description: str = Field(..., alias="Description")
    affected_file: str = Field(..., alias="Affected File")
    line_number: int = Field(..., alias="Line Number")
    code_snippet: str = Field(..., alias="Code Snippet")
    risk_explanation: str = Field(..., alias="Risk Explanation")
    recommended_fix: str = Field(..., alias="Recommended Fix")
    corrected_code_example: str = Field(..., alias="Corrected Code Example")

    issue_name_snake: str = Field(..., alias="issue_name")
    owasp_category_snake: str = Field(..., alias="owasp_category")
    severity_snake: str = Field(..., alias="severity")
    description_snake: str = Field(..., alias="description")
    affected_file_snake: str = Field(..., alias="affected_file")
    line_number_snake: int = Field(..., alias="line_number")
    code_snippet_snake: str = Field(..., alias="code_snippet")
    risk_explanation_snake: str = Field(..., alias="risk_explanation")
    recommended_fix_snake: str = Field(..., alias="recommended_fix")
    corrected_code_example_snake: str = Field(..., alias="corrected_code_example")

    model_config = {
        "populate_by_name": True
    }

@router.post("/code", response_model=List[CodeAnalysisFindingResponse], status_code=status.HTTP_200_OK)
def analyze_code_endpoint(
    request: CodeAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze the submitted Python or Java code and detect code quality/smells, complexity, design problems, and coding standards.
    """
    code = request.code
    language = request.language.lower()

    if not code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code content cannot be empty"
        )

    if language not in ["python", "java"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: '{language}'. Supported: 'python', 'java'"
        )

    # Validate syntax first (returns ValueError if invalid)
    filename = "main.py" if language == "python" else "Main.java"
    try:
        validate_code_syntax(filename, code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Run Static analysis
    if language == "python":
        findings = analyze_python_ast(code)
    else:
        findings = analyze_java_lexical(code)

    # Map to final finding response format
    results = []
    for f in findings:
        # Skip internal errors or map them
        if f.get("id") == "QLY-ERR":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f.get("description", "AST Parser error")
            )
            
        results.append(CodeAnalysisFindingResponse(
            id=f.get("id", "QLY-UNKNOWN"),
            title=f.get("title", "Code Quality Issue"),
            description=f.get("description", ""),
            language=language,
            severity=f.get("severity", "Medium"),
            category=f.get("category", "Code Smell"),
            line_number=f.get("line_number", f.get("line", 1)),
            code_snippet=f.get("code_snippet", f.get("snippet", "")),
            explanation=f.get("explanation", ""),
            recommendation=f.get("recommendation", "")
        ))

    return results

@router.post("/security", response_model=List[SecurityAnalysisFindingResponse], status_code=status.HTTP_200_OK)
def analyze_security_endpoint(
    request: SecurityAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze the submitted Python or Java code and detect security vulnerabilities using rule-based static scanning.
    """
    code = request.code
    language = request.language.lower()
    filename = request.filename

    if not code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code content cannot be empty"
        )

    if language not in ["python", "java"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: '{language}'. Supported: 'python', 'java'"
        )

    # Validate syntax first
    syntax_filename = filename if filename else ("main.py" if language == "python" else "Main.java")
    try:
        validate_code_syntax(syntax_filename, code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Run Static Security Analysis
    scanner = ScannerRegistry.get_scanner(language)
    if not scanner:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security scanner for '{language}' could not be loaded."
        )

    findings = scanner.scan_code(code, filename=syntax_filename)

    results = []
    for f in findings:
        results.append(SecurityAnalysisFindingResponse(
            **{
                "Issue Name": f.get("Issue Name"),
                "OWASP Category": f.get("OWASP Category"),
                "Severity": f.get("Severity"),
                "Description": f.get("Description"),
                "Affected File": f.get("Affected File"),
                "Line Number": f.get("Line Number"),
                "Code Snippet": f.get("Code Snippet"),
                "Risk Explanation": f.get("Risk Explanation"),
                "Recommended Fix": f.get("Recommended Fix"),
                "Corrected Code Example": f.get("Corrected Code Example"),
                
                "issue_name": f.get("issue_name"),
                "owasp_category": f.get("owasp_category"),
                "severity": f.get("severity"),
                "description": f.get("description"),
                "affected_file": f.get("affected_file"),
                "line_number": f.get("line_number"),
                "code_snippet": f.get("code_snippet"),
                "risk_explanation": f.get("risk_explanation"),
                "recommended_fix": f.get("recommended_fix"),
                "corrected_code_example": f.get("corrected_code_example")
            }
        ))

    return results

class ParallelAnalysisRequest(BaseModel):
    code: str = Field(..., description="The source code contents to analyze.")
    language: str = Field(..., description="The language of the code ('python' or 'java').")

class ParallelAnalysisResponse(BaseModel):
    analysis_findings: List[Dict[str, Any]] = Field(..., description="List of quality findings.")
    security_findings: List[Dict[str, Any]] = Field(..., description="List of security vulnerabilities.")
    merged_findings: List[Dict[str, Any]] = Field(..., description="Combined findings sorted by severity.")
    summary: Dict[str, Any] = Field(..., description="Metadata and execution statistics.")

@router.post("/run", response_model=ParallelAnalysisResponse, status_code=status.HTTP_200_OK)
def run_parallel_analysis_endpoint(
    request: ParallelAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze the submitted Python or Java code using a parallel multi-agent LangGraph workflow.
    Executes both code analysis and security vulnerability scanners concurrently.
    """
    code = request.code
    language = request.language.lower()

    if not code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code content cannot be empty"
        )

    if language not in ["python", "java"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: '{language}'. Supported: 'python', 'java'"
        )

    # Validate syntax first
    filename = "main.py" if language == "python" else "Main.java"
    try:
        validate_code_syntax(filename, code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    from backend.app.agents.orchestrator import get_parallel_review_workflow
    import time
    
    workflow = get_parallel_review_workflow()
    try:
        result = workflow.invoke({
            "code": code,
            "language": language,
            "start_time": time.time()
        })
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute parallel analysis graph: {str(e)}"
        )
