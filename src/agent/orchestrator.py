"""
Core Agent Orchestrator:
Executes the research lifecycle:
Accept Question -> Plan -> Tool Selection & Execution -> Error Recovery -> Synthesis -> Judge Audit
"""

import time
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.schema import (
    ResearchPlan,
    ToolResult,
    FinalResearchResponse,
    ExecutionTrace,
    JudgeEvaluation
)
from src.llm.provider import BaseLLM, get_llm_provider
from src.tools import get_default_tools, BaseTool
from src.agent.planner import ResearchPlanner
from src.agent.synthesizer import ResearchSynthesizer
from src.agent.judge import ResearchJudge
from src.config import settings

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Production-Oriented Research Agent with comprehensive observability and resilience."""

    def __init__(self, llm: Optional[BaseLLM] = None, tools: Optional[Dict[str, BaseTool]] = None):
        self.llm = llm or get_llm_provider()
        self.tools = tools or get_default_tools()
        self.planner = ResearchPlanner(self.llm)
        self.synthesizer = ResearchSynthesizer(self.llm)
        self.judge = ResearchJudge(self.llm)

    def run(self, query: str) -> ExecutionTrace:
        """
        Executes an end-to-end research session with full telemetry tracking.
        """
        trace_id = str(uuid.uuid4())[:8]
        start_time_iso = datetime.now().isoformat()
        start_perf = time.perf_counter()

        trace = ExecutionTrace(
            trace_id=trace_id,
            user_query=query,
            start_time=start_time_iso
        )

        logger.info(f"[Trace {trace_id}] Initiating research workflow for: '{query}'")

        try:
            # Stage 1: Planning
            plan: ResearchPlan = self.planner.create_plan(query)
            trace.plan = plan
            logger.info(f"[Trace {trace_id}] Formulated plan with {len(plan.decomposed_steps)} steps.")

            # Stage 2: Tool Execution with Failure Handling
            tool_results: List[ToolResult] = []
            for step in plan.decomposed_steps:
                tool_name = step.tool_needed
                tool = self.tools.get(tool_name)

                step.status = "in_progress"
                if not tool:
                    # Attempt tool fallback if requested tool doesn't exist
                    logger.warning(f"[Trace {trace_id}] Unknown tool '{tool_name}'. Falling back to web_search.")
                    tool = self.tools.get("web_search")
                    tool_name = "web_search"
                    trace.warnings.append(f"Tool '{step.tool_needed}' not found. Re-routed to 'web_search'.")

                # Execute tool under safe boundary
                try:
                    result: ToolResult = tool.execute(**step.tool_input)
                    tool_results.append(result)

                    if result.success:
                        step.status = "completed"
                    else:
                        step.status = "failed"
                        trace.warnings.append(f"Tool '{tool_name}' failed: {result.error}")
                        # Auto-recovery: If a primary tool fails, trigger fallback search
                        if tool_name != "web_search" and "web_search" in self.tools:
                            logger.info(f"[Trace {trace_id}] Attempting auto-recovery using web_search.")
                            recovery_result = self.tools["web_search"].execute(query=query)
                            tool_results.append(recovery_result)
                            trace.warnings.append("Auto-recovery activated: executed supplementary web_search.")

                    if result.sanitized:
                        trace.warnings.append(f"Security: Sanitized suspicious instruction in '{tool_name}' output.")

                except Exception as ex:
                    step.status = "failed"
                    error_msg = f"Unhandled exception during tool '{tool_name}' execution: {ex}"
                    logger.error(error_msg)
                    trace.errors.append(error_msg)

            trace.tool_executions = tool_results

            # Stage 3: Answer Synthesis & Citation Grounding
            final_response: FinalResearchResponse = self.synthesizer.synthesize(query, tool_results)
            
            # Enrich execution metadata
            duration_ms = round((time.perf_counter() - start_perf) * 1000, 2)
            final_response.execution_metadata = {
                "trace_id": trace_id,
                "duration_ms": duration_ms,
                "tool_calls_count": len(tool_results),
                "successful_tool_calls": sum(1 for tr in tool_results if tr.success),
                "llm_provider": self.llm.__class__.__name__
            }
            trace.final_response = final_response

            # Stage 4: Independent Judge Evaluation (Stretch Goal)
            if settings.ENABLE_JUDGE_STEP:
                judge_eval: JudgeEvaluation = self.judge.evaluate(final_response)
                trace.judge_evaluation = judge_eval
                
                # Guardrail: If hallucination risk is High or grounding is below threshold, adjust confidence
                if judge_eval.hallucination_risk == "High" or judge_eval.grounding_score < 0.60:
                    trace.warnings.append("Guardrail: High hallucination risk or low grounding flagged by Judge. Downgrading confidence.")
                    final_response.confidence_level = "Low"
                    final_response.confidence_score = min(final_response.confidence_score, 0.45)
                    final_response.limitations_or_assumptions.append(
                        "Independent judge audit flagged weak grounding in secondary assertions; verify before high-stakes decisions."
                    )

        except Exception as e:
            error_text = f"Critical pipeline failure: {e}"
            logger.critical(error_text, exc_info=True)
            trace.errors.append(error_text)
            # Guarantee deterministic return even on catastrophic crash
            trace.final_response = FinalResearchResponse(
                user_question=query,
                short_answer="The research agent encountered an unrecoverable system exception during execution.",
                key_findings=["Execution aborted due to pipeline error."],
                sources_used=[],
                confidence_level="Low",
                confidence_score=0.0,
                limitations_or_assumptions=[f"Pipeline error: {str(e)}"],
                suggested_next_steps=["Inspect system trace logs and retry with a narrower search query."]
            )

        end_perf = time.perf_counter()
        trace.end_time = datetime.now().isoformat()
        trace.duration_ms = round((end_perf - start_perf) * 1000, 2)

        logger.info(f"[Trace {trace_id}] Workflow completed in {trace.duration_ms}ms")
        return trace
