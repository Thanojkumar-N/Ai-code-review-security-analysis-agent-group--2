import time
import logging
from datetime import datetime
from typing import TypedDict, List, Dict, Any, Optional

from backend.app.agents.state import AgentState
from backend.app.agents.code_analysis_agent import code_analysis_agent_node
from backend.app.agents.security_agent import security_agent_node
from backend.app.agents.remediation_agent import remediation_agent_node
from backend.app.agents.pr_summary_agent import pr_summary_agent_node
from backend.app.agents.conversation_agent import conversation_agent_node

# Try importing LangGraph, fallback to custom StateGraph if not present
try:
    from langgraph.graph import StateGraph, START, END
except ImportError:
    from backend.app.agents.fallback_graph import StateGraph, END
    START = "__start__"

logger = logging.getLogger(__name__)

# State schema for the parallel workflow
class ParallelOrchestratorState(TypedDict):
    """The central state schema passed between nodes in the parallel review workflow."""
    code: str
    language: str
    code_analysis: Optional[Dict[str, Any]]
    security_analysis: Optional[Dict[str, Any]]
    status_code_analysis: Optional[Dict[str, Any]]
    status_security_analysis: Optional[Dict[str, Any]]
    analysis_findings: Optional[List[Dict[str, Any]]]
    security_findings: Optional[List[Dict[str, Any]]]
    merged_findings: Optional[List[Dict[str, Any]]]
    summary: Optional[Dict[str, Any]]
    start_time: Optional[float]

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

# Nodes for Parallel Orchestrator

def run_code_analysis(state: ParallelOrchestratorState) -> Dict[str, Any]:
    """Node wrapper for running the Code Analysis Agent with retry logic, logging, and execution timing."""
    start_time = time.time()
    retries = 3
    delay = 1.0
    agent_status = {
        "status": "pending",
        "execution_time_ms": 0.0,
        "retries": 0,
        "error": None
    }
    
    for attempt in range(retries):
        try:
            logger.info(f"Running Code Analysis Agent (attempt {attempt + 1})")
            # Call underlying node code analysis logic
            result = code_analysis_agent_node(state)
            
            duration_ms = (time.time() - start_time) * 1000
            agent_status.update({
                "status": "success",
                "execution_time_ms": round(duration_ms, 2),
                "retries": attempt,
                "error": None
            })
            return {
                "code_analysis": result.get("code_analysis"),
                "status_code_analysis": agent_status
            }
        except Exception as e:
            logger.error(f"Error running Code Analysis Agent (attempt {attempt + 1}): {str(e)}", exc_info=True)
            agent_status["retries"] = attempt + 1
            agent_status["error"] = str(e)
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                agent_status["status"] = "failed"
                
    duration_ms = (time.time() - start_time) * 1000
    agent_status["execution_time_ms"] = round(duration_ms, 2)
    return {
        "code_analysis": {"quality_findings": []},
        "status_code_analysis": agent_status
    }

def run_security_analysis(state: ParallelOrchestratorState) -> Dict[str, Any]:
    """Node wrapper for running the Security Vulnerability Agent with retry logic, logging, and execution timing."""
    start_time = time.time()
    retries = 3
    delay = 1.0
    agent_status = {
        "status": "pending",
        "execution_time_ms": 0.0,
        "retries": 0,
        "error": None
    }
    
    for attempt in range(retries):
        try:
            logger.info(f"Running Security Vulnerability Agent (attempt {attempt + 1})")
            # Call underlying node security analysis logic
            result = security_agent_node(state)
            
            duration_ms = (time.time() - start_time) * 1000
            agent_status.update({
                "status": "success",
                "execution_time_ms": round(duration_ms, 2),
                "retries": attempt,
                "error": None
            })
            return {
                "security_analysis": result.get("security_analysis"),
                "status_security_analysis": agent_status
            }
        except Exception as e:
            logger.error(f"Error running Security Vulnerability Agent (attempt {attempt + 1}): {str(e)}", exc_info=True)
            agent_status["retries"] = attempt + 1
            agent_status["error"] = str(e)
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                agent_status["status"] = "failed"
                
    duration_ms = (time.time() - start_time) * 1000
    agent_status["execution_time_ms"] = round(duration_ms, 2)
    return {
        "security_analysis": {"vulnerabilities": []},
        "status_security_analysis": agent_status
    }

def run_merge_findings(state: ParallelOrchestratorState) -> Dict[str, Any]:
    """Node for merging findings from Code Analysis and Security agents, sorting by severity, and recording metrics."""
    start_time = state.get("start_time") or time.time()
    
    analysis_data = state.get("code_analysis") or {}
    security_data = state.get("security_analysis") or {}
    
    analysis_findings = analysis_data.get("quality_findings") or []
    security_findings = security_data.get("vulnerabilities") or []
    
    # Standardize & track source agent
    mapped_analysis = []
    for f in analysis_findings:
        item = dict(f)
        item["source_agent"] = "code_analysis"
        mapped_analysis.append(item)
        
    mapped_security = []
    for f in security_findings:
        item = dict(f)
        item["source_agent"] = "security_analysis"
        mapped_security.append(item)
        
    merged = mapped_analysis + mapped_security
    
    # Severity sorting: Critical > High > Medium > Low > Info > Unknown
    SEVERITY_ORDER = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "info": 4,
        "unknown": 5
    }
    
    def get_severity_rank(f):
        sev = f.get("severity") or f.get("Severity") or "unknown"
        return SEVERITY_ORDER.get(str(sev).lower(), 5)
        
    def get_line_number(f):
        return f.get("line_number") or f.get("line") or 0
        
    # Sort primarily by severity priority, secondarily by line number
    merged.sort(key=lambda x: (get_severity_rank(x), get_line_number(x)))
    
    total_time_ms = (time.time() - start_time) * 1000
    
    status_ca = state.get("status_code_analysis") or {}
    status_sec = state.get("status_security_analysis") or {}
    
    summary = {
        "total_execution_time_ms": round(total_time_ms, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_findings": len(merged),
        "analysis_findings_count": len(mapped_analysis),
        "security_findings_count": len(mapped_security),
        "agent_status": {
            "code_analysis": status_ca,
            "security_analysis": status_sec
        }
    }
    
    return {
        "analysis_findings": mapped_analysis,
        "security_findings": mapped_security,
        "merged_findings": merged,
        "summary": summary
    }

def get_parallel_review_workflow():
    """Build and compile the parallel code review workflow using LangGraph."""
    workflow = StateGraph(ParallelOrchestratorState)
    
    # 1. Register Nodes
    workflow.add_node("code_analysis", run_code_analysis)
    workflow.add_node("security_analysis", run_security_analysis)
    workflow.add_node("merge_findings", run_merge_findings)
    
    # 2. Define Transitions (Edges)
    workflow.add_edge(START, "code_analysis")
    workflow.add_edge(START, "security_analysis")
    workflow.add_edge("code_analysis", "merge_findings")
    workflow.add_edge("security_analysis", "merge_findings")
    workflow.add_edge("merge_findings", END)
    
    return workflow.compile()

