"""
Pydantic schemas for the Production AI Research Agent.
Enforces deterministic structured contracts across planning, tool execution,
synthesis, and evaluation stages.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ToolCall(BaseModel):
    """Specification of an invoked tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


class ToolResult(BaseModel):
    """Structured response from a tool execution, including reliability signals."""
    tool_name: str
    query: str
    success: bool
    status_code: int = 200
    data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    cached: bool = False
    sanitized: bool = False
    warning: Optional[str] = None


class PlanStep(BaseModel):
    """A granular step in the agent's research plan."""
    step_id: int
    description: str
    tool_needed: str = Field(..., description="Tool name to use (e.g., 'web_search', 'content_fetcher', 'tech_kb')")
    tool_input: Dict[str, Any] = Field(default_factory=dict, description="Input arguments for the tool")
    rationale: str = Field("", description="Why this step is required to answer the user's question")
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"] = "pending"


class ResearchPlan(BaseModel):
    """Deterministic plan formulated by the Planner before tool execution."""
    user_query: str
    intent_analysis: str
    decomposed_steps: List[PlanStep]
    information_needs: List[str] = Field(default_factory=list)
    risk_assessment: Optional[str] = Field(default="Standard query execution")


class SourceReference(BaseModel):
    """A grounded, verified source citation."""
    id: int
    title: str
    url: str
    snippet: str
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    domain: Optional[str] = None


class FinalResearchResponse(BaseModel):
    """
    Strict final schema required by the assignment specification:
    - User question
    - Short answer
    - Key findings
    - Sources used
    - Confidence level
    - Limitations or assumptions
    - Suggested next steps
    """
    user_question: str
    short_answer: str
    key_findings: List[str]
    sources_used: List[SourceReference]
    confidence_level: Literal["High", "Medium", "Low"]
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Numerical confidence 0.0 - 1.0")
    limitations_or_assumptions: List[str]
    suggested_next_steps: List[str]
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)


class JudgeEvaluation(BaseModel):
    """Automated evaluation produced by the judge step for safety & quality assurance."""
    is_grounded: bool
    grounding_score: float = Field(..., ge=0.0, le=1.0)
    hallucination_risk: Literal["Low", "Medium", "High"]
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    schema_valid: bool = True
    audit_feedback: List[str] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    """Telemetry and trace log for observability and debugging."""
    trace_id: str
    user_query: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    plan: Optional[ResearchPlan] = None
    tool_executions: List[ToolResult] = Field(default_factory=list)
    final_response: Optional[FinalResearchResponse] = None
    judge_evaluation: Optional[JudgeEvaluation] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
