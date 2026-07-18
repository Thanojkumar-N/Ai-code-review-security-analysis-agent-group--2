import pytest
from backend.app.agents.orchestrator import get_review_workflow, get_conversation_workflow

def test_python_code_analysis_and_security_flow():
    """Verify that the full multi-agent StateGraph flow runs on Python code and returns state details."""
    unsafe_py_code = """
import os
import subprocess

def process_data(user_input):
    # SEC-001: Secret Key Leakage
    API_SECRET = "super_secret_jwt_key_12345"
    
    # SEC-002: SQL Injection
    db.execute(f"SELECT * FROM users WHERE username = '{user_input}'")
    
    # QLY-007: Magic Number
    multiplier = user_input * 42.5
    
    # QLY-008: Poor Naming (Short Variable)
    a = 10
    
    # SEC-003: Command Execution Injection
    os.system(f"echo {user_input}")
    
    return True
    
    # QLY-005: Dead Code
    print("This will not be executed")
"""
    
    # Run Orchestrator Workflow
    workflow = get_review_workflow()
    state_input = {
        "code": unsafe_py_code,
        "language": "python"
    }
    result = workflow.invoke(state_input)

    # 1. Verify Code Analysis Agent Node
    analysis = result.get("code_analysis")
    assert analysis is not None
    assert analysis["lines_count"] > 5
    assert analysis["functions_count"] == 1
    assert "summary" in analysis
    
    quality = analysis.get("quality_findings", [])
    assert len(quality) > 0
    q_ids = [q["id"] for q in quality]
    assert "QLY-003" in q_ids  # Unused local variable
    assert "QLY-005" in q_ids  # Dead code
    assert "QLY-007" in q_ids  # Magic numbers
    assert "QLY-008" in q_ids  # Poor Naming (Short Variable)

    # 2. Verify Security Agent Node (eval, Secrets, os.system should be flagged)
    security = result.get("security_analysis")
    assert security is not None
    vulns = security.get("vulnerabilities", [])
    assert len(vulns) >= 3
    vuln_ids = [v["id"] for v in vulns]
    assert "SEC-001" in vuln_ids  # Secrets
    assert "SEC-002" in vuln_ids  # SQL Injection
    assert "SEC-007" in vuln_ids  # os.system (Command Injection)

    for v in vulns:
        assert "cwe" in v
        assert "confidence" in v
        assert "classification" in v
        assert "snippet" in v

    # 3. Verify Remediation Agent Node
    remediations = result.get("remediations", [])
    assert len(remediations) == len(vulns)
    for remed in remediations:
        assert "explanation" in remed
        assert "corrected_code" in remed
        assert "recommendation" in remed
        assert "reference" in remed
        assert "code_comparison" in remed

    # 4. Verify PR Summary Agent Node
    pr = result.get("pr_summary")
    assert pr is not None
    assert "title" in pr
    assert "markdown_report" in pr
    assert "html_report" in pr
    assert "json_report" in pr

def test_java_code_analysis_and_security_flow():
    """Verify that the full multi-agent StateGraph flow runs on Java code and flags SQLi, Cmd Injection, Weak Crypto, and CSRF disable."""
    unsafe_java_code = """
public class Main {
    public static void main(String[] args) {
        // SEC-002: SQL Injection
        String query = "SELECT * FROM users WHERE user_id = '" + args[0] + "'";
        
        // SEC-007: Command Injection
        Runtime.getRuntime().exec(args[0]);
        
        // SEC-008: Weak Crypto
        MessageDigest md = MessageDigest.getInstance("MD5");
        
        // SEC-004: CSRF Disable
        http.csrf().disable();
    }
}
"""
    workflow = get_review_workflow()
    state_input = {
        "code": unsafe_java_code,
        "language": "java"
    }
    result = workflow.invoke(state_input)

    # Verify vulnerabilities are flagged
    security = result.get("security_analysis")
    vulns = security.get("vulnerabilities", [])
    vuln_ids = [v["id"] for v in vulns]
    assert "SEC-002" in vuln_ids  # Java SQL injection concat
    assert "SEC-007" in vuln_ids  # Command injection
    assert "SEC-008" in vuln_ids  # Weak Cryptography MD5
    assert "SEC-004" in vuln_ids  # CSRF disable

def test_conversation_agent_flow():
    """Verify that the Conversation Agent answers questions about code complexity and vulnerabilities."""
    workflow = get_conversation_workflow()
    
    # Pre-defined mock state matching state schema
    mock_state = {
        "code": "def hello():\n    pass",
        "language": "python",
        "code_analysis": {
            "lines_count": 2,
            "functions_count": 1,
            "classes_count": 0,
            "complexity_score": 1,
            "complexity_rating": "Low Complexity (Clean)"
        },
        "security_analysis": {
            "vulnerabilities": [
                {
                    "id": "SEC-001",
                    "line": 2,
                    "title": "Secrets leak",
                    "severity": "High",
                    "classification": "Secrets",
                    "description": "Secrets leak identified",
                    "snippet": "key = '123'"
                }
            ]
        },
        "chat_message": "Tell me about the vulnerabilities found",
        "conversation_history": []
    }

    result = workflow.invoke(mock_state)
    chat_response = result.get("chat_response")
    assert chat_response is not None
    assert "active security vulnerabilities" in chat_response.lower()

    # Query about complexity
    mock_state["chat_message"] = "What is the complexity?"
    result_complexity = workflow.invoke(mock_state)
    assert "complexity" in result_complexity.get("chat_response").lower()
