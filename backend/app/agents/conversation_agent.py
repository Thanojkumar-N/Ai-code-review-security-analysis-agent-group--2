from backend.app.agents.state import AgentState

def conversation_agent_node(state: AgentState) -> dict:
    """Agent node that addresses user queries regarding code quality or security audit reports."""
    chat_message = state.get("chat_message", "").strip().lower()
    security_analysis = state.get("security_analysis", {}) or {}
    vulnerabilities = security_analysis.get("vulnerabilities", []) or []
    code_analysis = state.get("code_analysis", {}) or {}
    
    if not chat_message:
        return {"chat_response": "Hello! How can I assist you with your code analysis report today?"}

    response = ""

    # Contextual routing based on keyword matching
    if any(kwd in chat_message for kwd in ["vulnerability", "vulnerabilities", "security", "bug", "flaw", "issue"]):
        if vulnerabilities:
            response = (
                f"This code contains {len(vulnerabilities)} active security vulnerabilities:\n" +
                "\n".join([f"- Line {v['line']}: {v['title']} ({v['severity']} severity)" for v in vulnerabilities]) +
                "\n\nYou can inspect the remediations tab to see recommended secure replacements."
            )
        else:
            response = "Excellent news! Our scanners did not find any security vulnerabilities in this code block."
            
    elif any(kwd in chat_message for kwd in ["complexity", "complex", "lines", "classes", "functions"]):
        rating = code_analysis.get("complexity_rating", "Unknown")
        score = code_analysis.get("complexity_score", 0)
        response = (
            f"Here are the code quality metrics:\n"
            f"- Total Lines: {code_analysis.get('lines_count', 0)}\n"
            f"- Functions Count: {code_analysis.get('functions_count', 0)}\n"
            f"- Classes Count: {code_analysis.get('classes_count', 0)}\n"
            f"- Complexity Score: {score} ({rating})"
        )
        
    elif any(kwd in chat_message for kwd in ["eval", "exec", "system", "injection"]):
        eval_flagged = any(v["id"] == "SEC-002" for v in vulnerabilities)
        sql_flagged = any(v["id"] == "SEC-004" for v in vulnerabilities)
        if eval_flagged:
            response = "Yes, eval/exec execution is flagged as Critical. It compiles untrusted input strings dynamically, risking full remote execution."
        elif sql_flagged:
            response = "Yes, SQL query string concatenation was detected. This allows input parameters to escape query syntax blocks, enabling database leakage."
        else:
            response = "Injecting raw strings into interpreter engines (SQL/shell/eval) is dangerous. Although none were flagged here, always validate user inputs."
            
    else:
        response = (
            f"I analyzed this code block and found it has {code_analysis.get('lines_count', 0)} lines. "
            f"There are {len(vulnerabilities)} flagged security issues. "
            "Feel free to ask details about 'vulnerabilities', 'remediations', or 'complexity'."
        )

    # 2. Query matching context guidelines from RAG Vector Store
    from backend.app.rag.rag_service import RAGService
    # Seed knowledge documents if not already ingested
    RAGService.ingest_documents()
    rag_context = RAGService.retrieve_context(chat_message)
    if rag_context:
        response += f"\n\n**Retrieved Secure Coding Standards (RAG)**:\n{rag_context}"

    return {"chat_response": response}
