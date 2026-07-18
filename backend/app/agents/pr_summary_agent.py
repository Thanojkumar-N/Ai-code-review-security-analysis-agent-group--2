import json
from backend.app.agents.state import AgentState

def pr_summary_agent_node(state: AgentState) -> dict:
    """Agent node that aggregates code quality and security findings into a GitHub-style review report.
    
    Generates Markdown, HTML, and JSON representations of the review.
    """
    code_analysis = state.get("code_analysis", {}) or {}
    quality_findings = code_analysis.get("quality_findings", []) or []
    
    security_analysis = state.get("security_analysis", {}) or {}
    vulnerabilities = security_analysis.get("vulnerabilities", []) or []
    
    language = state.get("language", "python").capitalize()
    lines_count = code_analysis.get("lines_count", 0)
    complexity_score = code_analysis.get("complexity_score", 1)
    complexity_rating = code_analysis.get("complexity_rating", "Low")
    
    # 1. Calculate overall score dynamically
    score = 100
    for v in vulnerabilities:
        sev = v.get("severity")
        if sev == "Critical": score -= 15
        elif sev == "High": score -= 10
        elif sev == "Medium": score -= 5
        elif sev == "Low": score -= 2

    for q in quality_findings:
        sev = q.get("severity")
        if sev == "Critical": score -= 10
        elif sev == "High": score -= 5
        elif sev == "Medium": score -= 3
        elif sev == "Low": score -= 1
        
    score = max(0, min(100, score))

    # 2. Group findings by severity
    findings_by_sev = {"Critical": [], "High": [], "Medium": [], "Low": [], "Info": []}
    for v in vulnerabilities:
        sev = v.get("severity", "Medium")
        findings_by_sev[sev].append({
            "type": "Security",
            "title": v.get("title"),
            "line": v.get("line"),
            "description": v.get("description"),
            "cwe": v.get("cwe", "N/A"),
            "owasp": v.get("classification", "N/A"),
            "snippet": v.get("snippet", "")
        })
        
    for q in quality_findings:
        sev = q.get("severity", "Medium")
        findings_by_sev[sev].append({
            "type": "Quality",
            "title": q.get("title"),
            "line": q.get("line"),
            "description": q.get("description"),
            "snippet": q.get("snippet", "")
        })

    # Count sizes
    total_security = len(vulnerabilities)
    total_quality = len(quality_findings)
    total_findings = total_security + total_quality

    # Determine status check label
    if score >= 90:
        status_check = "🟢 PASSED (Excellent Quality)"
    elif score >= 70:
        status_check = "🟡 PASSED WITH WARNINGS (Moderate Issues)"
    else:
        status_check = "🔴 FAILED (High Risk Vulnerabilities)"

    title = f"Review Summary: {status_check} - Score {score}/100"

    summary_narrative = (
        f"This GitHub-style review processed {lines_count} lines of {language} code. "
        f"We identified {total_security} security vulnerabilities and {total_quality} code quality issues. "
        f"The codebase cyclomatic complexity is score {complexity_score} ({complexity_rating}). "
        f"Overall review score is calculated as **{score}/100**."
    )

    # 3. Generate Markdown Format Report
    md = [
        f"# AI Code Review & Security Report",
        f"\n### Review Status: {status_check}",
        f"\n**Overall Score**: `{score}/100`  ",
        f"**Language**: `{language}` | **Complexity**: `{complexity_rating} (Score: {complexity_score})` | **Total Lines**: `{lines_count}`",
        f"\n## Summary",
        summary_narrative,
        f"\n## Findings Breakdown ({total_findings} total findings)"
    ]

    for category in ["Critical", "High", "Medium", "Low", "Info"]:
        items = findings_by_sev[category]
        if items:
            md.append(f"\n### ⚠️ {category} Severity Issues ({len(items)})")
            for item in items:
                md.append(f"- **Line {item['line']} [{item['type']}]**: {item['title']}")
                md.append(f"  - *Description*: {item['description']}")
                if item.get("cwe") and item["cwe"] != "N/A":
                    md.append(f"  - *Classification*: {item['owasp']} | {item['cwe']}")
                md.append(f"  - *Snippet*:\n    ```\n    {item['snippet']}\n    ```")

    # Add general improvement suggestions
    md.append("\n## Improvement Suggestions")
    if total_security > 0:
        md.append("- **Security Hardening**: Immediately migrate raw credentials and parameters out of code files to secure environment variables.")
    if total_quality > 0:
        md.append("- **Clean Code Refactoring**: Reduce complexity, clean unused variables, and extract nested control structures into separate helper functions.")
    if total_findings == 0:
        md.append("- **None**: Code conforms perfectly to clean coding guidelines.")

    markdown_report = "\n".join(md)

    # 4. Generate HTML Format Report
    html_lines = [
        "<h1>AI Code Review &amp; Security Report</h1>",
        f"<h3>Review Status: <strong style='font-size: 1.1em;'>{status_check}</strong></h3>",
        f"<p><strong>Overall Score:</strong> {score}/100</p>",
        f"<p><strong>Language:</strong> {language} | <strong>Complexity:</strong> {complexity_rating} (Score: {complexity_score}) | <strong>Lines:</strong> {lines_count}</p>",
        "<h2>Summary</h2>",
        f"<p>{summary_narrative}</p>",
        f"<h2>Findings Breakdown ({total_findings} total findings)</h2>"
    ]

    for category in ["Critical", "High", "Medium", "Low", "Info"]:
        items = findings_by_sev[category]
        if items:
            html_lines.append(f"<h3>{category} Severity Issues ({len(items)})</h3>")
            html_lines.append("<ul>")
            for item in items:
                html_lines.append(f"<li>")
                html_lines.append(f"<strong>Line {item['line']} [{item['type']}]</strong>: {item['title']}<br/>")
                html_lines.append(f"<em>Description:</em> {item['description']}<br/>")
                if item.get("cwe") and item["cwe"] != "N/A":
                    html_lines.append(f"<em>Classification:</em> {item['owasp']} | {item['cwe']}<br/>")
                html_lines.append(f"<pre><code>{item['snippet']}</code></pre>")
                html_lines.append(f"</li>")
            html_lines.append("</ul>")

    html_lines.append("<h2>Improvement Suggestions</h2>")
    html_lines.append("<ul>")
    if total_security > 0:
        html_lines.append("<li><strong>Security Hardening:</strong> Extract plaintext parameters and secure database strings to application configs.</li>")
    if total_quality > 0:
        html_lines.append("<li><strong>Clean Code Refactoring:</strong> Split long functions, remove unused arguments, and extract loops.</li>")
    if total_findings == 0:
        html_lines.append("<li>Code looks clean and conforms to style rules.</li>")
    html_lines.append("</ul>")

    html_report = "\n".join(html_lines)

    # 5. Generate JSON Format Report
    json_data = {
        "overall_score": score,
        "language": language,
        "lines_count": lines_count,
        "complexity": {
            "score": complexity_score,
            "rating": complexity_rating
        },
        "summary": summary_narrative,
        "findings": findings_by_sev,
        "suggestions": [
            "Extract plaintext credentials to configuration files" if total_security > 0 else "None",
            "Refactor high-complexity methods to follow SOLID principles" if total_quality > 0 else "None"
        ]
    }
    json_report = json.dumps(json_data, indent=2)

    return {
        "pr_summary": {
            "title": title,
            "summary": summary_narrative,
            "overall_score": score,
            "markdown_report": markdown_report,
            "html_report": html_report,
            "json_report": json_report
        }
    }
