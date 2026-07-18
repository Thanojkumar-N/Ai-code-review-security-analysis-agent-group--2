from backend.app.agents.state import AgentState
from backend.app.agents.code_analysis_agent import code_analysis_agent_node
from backend.app.agents.security_agent import security_agent_node
from backend.app.agents.remediation_agent import remediation_agent_node
from backend.app.agents.pr_summary_agent import pr_summary_agent_node
from backend.app.agents.conversation_agent import conversation_agent_node

# Try importing LangGraph, fallback to custom StateGraph if not present
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    from backend.app.agents.fallback_graph import StateGraph, END

def get_review_workflow():
    """Build and compile the sequential code analysis, security, and PR summary agent workflow."""
    workflow = StateGraph(AgentState)
    
    # 1. Register Nodes
    workflow.add_node("code_analysis", code_analysis_agent_node)
    workflow.add_node("security_analysis", security_agent_node)
    workflow.add_node("remediation", remediation_agent_node)
    workflow.add_node("pr_summary", pr_summary_agent_node)
    
    # 2. Define Transitions (Edges)
    workflow.set_entry_point("code_analysis")
    workflow.add_edge("code_analysis", "security_analysis")
    workflow.add_edge("security_analysis", "remediation")
    workflow.add_edge("remediation", "pr_summary")
    workflow.add_edge("pr_summary", END)
    
    return workflow.compile()

def get_conversation_workflow():
    """Build and compile the conversation agent workflow for interactive Q&A."""
    workflow = StateGraph(AgentState)
    
    # Register Node
    workflow.add_node("conversation", conversation_agent_node)
    
    # Transitions
    workflow.set_entry_point("conversation")
    workflow.add_edge("conversation", END)
    
    return workflow.compile()
