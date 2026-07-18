import os
import json
from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.models.submission import CodeSubmission
from backend.app.models.report import AnalysisReport
from backend.app.models.finding import ReviewFinding
from backend.app.models.export import ReportExport
from backend.app.config.config import settings

class AnalysisService:
    @staticmethod
    def trigger_mock_analysis(db: Session, submission_id: str) -> AnalysisReport:
        """Trigger the multi-agent code analysis workflow and save security findings in PostgreSQL."""
        submission = db.query(CodeSubmission).filter(CodeSubmission.id == submission_id).first()
        if not submission:
            raise ValueError("Submission not found")

        # Mark submission as completed
        submission.status = "completed"
        submission.updated_at = datetime.utcnow()
        db.commit()

        # Check if report already exists for this submission
        existing_report = db.query(AnalysisReport).filter(AnalysisReport.submission_id == submission_id).first()
        if existing_report:
            return existing_report

        # 1. Read source code text
        code = ""
        filename = "main.py"
        if submission.submission_type == "paste":
            code = submission.raw_code or ""
            # Simple heuristic detection for fallback
            if "public class " in code or "System.out" in code:
                filename = "Main.java"
        else:
            if submission.file_path and os.path.exists(submission.file_path):
                filename = os.path.basename(submission.file_path)
                try:
                    with open(submission.file_path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                except Exception as e:
                    code = f"# Error reading file contents: {str(e)}"

        language = "java" if filename.lower().endswith(".java") else "python"

        # 2. Invoke the compiled LangGraph workflow pipeline
        from backend.app.agents.orchestrator import get_review_workflow
        workflow = get_review_workflow()
        try:
            agent_result = workflow.invoke({"code": code, "language": language})
        except Exception as e:
            agent_result = {
                "code_analysis": {
                    "lines_count": len(code.split("\n")),
                    "functions_count": 0,
                    "classes_count": 0,
                    "complexity_score": 1,
                    "complexity_rating": "Unknown",
                    "summary": f"Graph execution error: {str(e)}"
                },
                "security_analysis": {"vulnerabilities": []},
                "remediations": [],
                "pr_summary": {
                    "title": "Automated Review Failure",
                    "overview": f"Could not complete agent scan due to execution failure: {str(e)}",
                    "changes_bullets": []
                }
            }

        # 3. Calculate dynamic security audit score
        score = 100
        vulns = agent_result.get("security_analysis", {}).get("vulnerabilities", [])
        for v in vulns:
            sev = v.get("severity")
            if sev == "Critical":
                score -= 15
            elif sev == "High":
                score -= 10
            elif sev == "Medium":
                score -= 5
            elif sev == "Low":
                score -= 2

        # Deduct score based on code quality issues
        quality_findings = agent_result.get("code_analysis", {}).get("quality_findings", [])
        for q in quality_findings:
            sev = q.get("severity")
            if sev == "Critical":
                score -= 10
            elif sev == "High":
                score -= 5
            elif sev == "Medium":
                score -= 3
            elif sev == "Low":
                score -= 1
        score = max(0, min(100, score))

        summary_text = agent_result.get("pr_summary", {}).get("markdown_report", "Code review completed successfully.")

        # 4. Create and save the AnalysisReport record
        report = AnalysisReport(
            submission_id=submission_id,
            summary=summary_text,
            score=score
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # 5. Populate ReviewFinding records from vulnerabilities and remediations lists
        remediations = agent_result.get("remediations", [])
        for vuln in vulns:
            vuln_id = vuln.get("id")
            line_num = vuln.get("line", 1)
            
            # Find matching remediation fix from Remediation Agent
            remed = next((r for r in remediations if r.get("vulnerability_id") == vuln_id and r.get("line") == line_num), None)
            
            if remed:
                rec_text = (
                    f"### Explanation\n{remed.get('explanation', '')}\n\n"
                    f"### Secure Coding Recommendation\n{remed.get('recommendation', '')}\n\n"
                    f"### Reference\n- {remed.get('reference', '')}\n\n"
                    f"### Code Comparison\n"
                    f"**Insecure Code (Before)**:\n"
                    f"```\n{remed.get('code_comparison', {}).get('before', '')}\n```\n\n"
                    f"**Secure Correction (After)**:\n"
                    f"```\n{remed.get('corrected_code', '')}\n```"
                )
            else:
                rec_text = "Apply secure coding guidelines to prevent injection or access failures."

            # Reconstruct detailed explanation with CWE/OWASP mappings and confidence scores
            cwe = vuln.get("cwe", "N/A")
            owasp = vuln.get("classification", "Security")
            confidence = vuln.get("confidence", "Medium")
            desc_text = (
                f"{vuln.get('description', '')}\n\n"
                f"**Vulnerability Classifications**:\n"
                f"- **OWASP Category**: {owasp}\n"
                f"- **CWE Vulnerability Mapping**: {cwe}\n"
                f"- **Detection Confidence Score**: {confidence} Confidence"
            )

            finding = ReviewFinding(
                report_id=report.id,
                file_path=filename,
                line_number=line_num,
                severity=vuln.get("severity", "Medium"),
                category="Security",
                title=vuln.get("title", "Security Vulnerability Detected"),
                description=desc_text,
                recommendation=rec_text,
                code_snippet=vuln.get("snippet", "")
            )
            db.add(finding)

        # 6. Populate ReviewFinding records for code quality smells
        for qf in quality_findings:
            line_num = qf.get("line", 1)
            finding = ReviewFinding(
                report_id=report.id,
                file_path=filename,
                line_number=line_num,
                severity=qf.get("severity", "Medium"),
                category=qf.get("category", "Code Quality"),
                title=qf.get("title", "Code Quality Smell"),
                description=qf.get("description", "Potential code smell found by static quality agent."),
                recommendation="Refactor the code snippet to align with standard clean coding practices.",
                code_snippet=qf.get("snippet", "")
            )
            db.add(finding)
        
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_project_reports(db: Session, project_id: str):
        """Retrieve analysis reports associated with a specific project."""
        return db.query(AnalysisReport)\
            .join(CodeSubmission, AnalysisReport.submission_id == CodeSubmission.id)\
            .filter(CodeSubmission.project_id == project_id)\
            .order_by(AnalysisReport.created_at.desc())\
            .all()

    @staticmethod
    def get_report_details(db: Session, report_id: str) -> AnalysisReport:
        """Retrieve a specific report with all its findings (by report ID or submission ID)."""
        report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
        if not report:
            report = db.query(AnalysisReport).filter(AnalysisReport.submission_id == report_id).first()
        if not report:
            raise ValueError("Report not found")
        return report

    @staticmethod
    def generate_report_export(db: Session, report_id: str, export_type: str) -> ReportExport:
        """Create a highly formatted exported report document (PDF, HTML, Markdown, JSON) and save database record."""
        report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
        if not report:
            report = db.query(AnalysisReport).filter(AnalysisReport.submission_id == report_id).first()
        if not report:
            raise ValueError("Report not found")

        # Create exports directory if missing
        os.makedirs(settings.REPORT_DIR, exist_ok=True)
        
        export_type_upper = export_type.upper()
        filename = f"report_{report_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{export_type_upper.lower()}"
        file_path = os.path.join(settings.REPORT_DIR, filename)

        try:
            # 1. JSON Export
            if export_type_upper == "JSON":
                data = {
                    "report_id": report.id,
                    "score": report.score,
                    "executive_summary": report.summary,
                    "findings_count": len(report.findings),
                    "findings": [
                        {
                            "id": f.id,
                            "title": f.title,
                            "severity": f.severity,
                            "category": f.category,
                            "file_path": f.file_path,
                            "line_number": f.line_number,
                            "description": f.description,
                            "recommendation": f.recommendation
                        } for f in report.findings
                    ]
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

            # 2. Markdown Export
            elif export_type_upper == "MD" or export_type_upper == "MARKDOWN":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# AI Code Review & Security Analysis Report\n\n")
                    f.write(f"**Report ID**: `{report.id}`  \n")
                    f.write(f"**Overall Score**: `{report.score}/100`  \n")
                    f.write(f"**Generated At**: `{datetime.utcnow().isoformat()}`\n\n")
                    f.write(f"## Executive Summary\n")
                    f.write(f"{report.summary}\n\n")
                    f.write(f"## Findings Summary\n")
                    f.write(f"Total findings: **{len(report.findings)}**\n\n")
                    for finding in report.findings:
                        f.write(f"### [{finding.severity}] {finding.title}\n")
                        f.write(f"- **Location**: `{finding.file_path}:L{finding.line_number}`\n")
                        f.write(f"- **Category**: {finding.category}\n")
                        f.write(f"- **Description**: {finding.description}\n")
                        f.write(f"- **Remediation Guide**:\n\n{finding.recommendation}\n\n")

            # 3. HTML Export
            elif export_type_upper == "HTML":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("<!DOCTYPE html><html><head><meta charset='utf-8'>")
                    f.write("<title>AI Code Review Report</title>")
                    f.write("<style>")
                    f.write("body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 40px auto; padding: 0 20px; }")
                    f.write(".header { border-bottom: 2px solid #eaeaea; padding-bottom: 20px; margin-bottom: 30px; }")
                    f.write(".score-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; background: #f3f4f6; }")
                    f.write(".score-green { color: #16a34a; background: #dcfce7; }")
                    f.write(".score-red { color: #dc2626; background: #fee2e2; }")
                    f.write(".finding-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px; background: #fafafa; }")
                    f.write("pre { background: #1e293b; color: #f8fafc; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: monospace; }")
                    f.write("</style></head><body>")
                    f.write(f"<div class='header'>")
                    f.write(f"<h1>AI Code Review &amp; Security Report</h1>")
                    f.write(f"<p><strong>Report ID:</strong> {report.id}</p>")
                    color_cls = "score-green" if report.score >= 80 else "score-red"
                    f.write(f"<p><span class='score-badge {color_cls}'>Score: {report.score}/100</span></p>")
                    f.write(f"</div>")
                    f.write(f"<h2>Executive Summary</h2>")
                    f.write(f"<p>{report.summary}</p>")
                    f.write(f"<h2>Findings ({len(report.findings)})</h2>")
                    for finding in report.findings:
                        f.write(f"<div class='finding-card'>")
                        f.write(f"<h3>[{finding.severity}] {finding.title}</h3>")
                        f.write(f"<p><strong>Location:</strong> {finding.file_path} at line {finding.line_number}</p>")
                        f.write(f"<p><strong>Category:</strong> {finding.category}</p>")
                        f.write(f"<p><strong>Description:</strong> {finding.description}</p>")
                        f.write(f"<h4>Remediation Guide:</h4>")
                        f.write(f"<div style='white-space: pre-wrap; font-size: 0.9em; background: #fff; padding: 10px; border-left: 3px solid #16a34a; margin-top: 10px;'>{finding.recommendation}</div>")
                        f.write(f"</div>")
                    f.write("</body></html>")

            # 4. PDF Export (Generates PDF using reportlab if installed, else fallback to standard printable PDF document format)
            else:
                try:
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    
                    c = canvas.Canvas(file_path, pagesize=letter)
                    c.drawString(100, 750, "AI CODE REVIEW & SECURITY REPORT")
                    c.drawString(100, 730, f"Report ID: {report.id}")
                    c.drawString(100, 710, f"Overall Score: {report.score}/100")
                    c.drawString(100, 690, f"Generated At: {datetime.utcnow().isoformat()}")
                    c.drawString(100, 670, "Executive Summary:")
                    c.drawString(100, 650, report.summary[:80] + "...")
                    c.drawString(100, 620, f"Total Findings: {len(report.findings)}")
                    
                    y = 590
                    for idx, finding in enumerate(report.findings[:5]):
                        c.drawString(100, y, f"{idx+1}. [{finding.severity}] {finding.title}")
                        c.drawString(120, y-15, f"Location: {finding.file_path}:L{finding.line_number}")
                        y -= 40
                    c.save()
                except ImportError:
                    # Fallback text representation
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"=== AI CODE REVIEW & SECURITY PDF EXPORT ===\n")
                        f.write(f"Report ID: {report_id}\n")
                        f.write(f"Score: {report.score}/100\n")
                        f.write(f"Summary: {report.summary}\n")
                        for idx, finding in enumerate(report.findings):
                            f.write(f"{idx+1}. [{finding.severity}] {finding.title} in {finding.file_path}:L{finding.line_number}\n")

        except Exception as e:
            raise RuntimeError(f"Could not generate export file: {str(e)}")

        export = ReportExport(
            report_id=report_id,
            export_type=export_type_upper,
            file_path=file_path
        )
        db.add(export)
        db.commit()
        db.refresh(export)
        return export
