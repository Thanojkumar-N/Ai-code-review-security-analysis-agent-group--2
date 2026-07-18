from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """The central state schema passed between nodes in the multi-agent workflow."""
    code: str
    language: str
    code_analysis: Optional[Dict[str, Any]]
    security_analysis: Optional[Dict[str, Any]]
    remediations: Optional[List[Dict[str, Any]]]
    pr_summary: Optional[Dict[str, Any]]
    chat_message: Optional[str]
    chat_response: Optional[str]
    conversation_history: Optional[List[Dict[str, str]]]
