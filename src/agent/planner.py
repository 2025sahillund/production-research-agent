"""
Agent Planner: Decomposes a research request into a structured, sequential plan.
Decides tool selection and input arguments before execution.
"""

import logging
from src.llm.provider import BaseLLM
from src.schema import ResearchPlan, PlanStep

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an Expert Research Planning Agent.
Your job is to decompose complex research questions into sequential, logical steps.

Available Tools:
1. 'tech_kb': Authoritative internal technical knowledge base for benchmarks, vector DBs, HR tech, and multi-agent systems.
2. 'web_search': Web search engine for latest articles, documentation, ecosystem news, and developer discussions.
3. 'content_fetcher': Fetches and scrapes clean text from a specific webpage URL.
4. 'fact_checker': Verifies factual consistency and cross-checks claims against gathered evidence.

Guidelines:
- Decompose the problem into 2 to 4 focused steps.
- Always prefer authoritative technical documentation ('tech_kb' or 'web_search').
- For comparative technical queries, plan an initial benchmark lookup followed by a verification or web search step.
- Return output strictly conforming to the ResearchPlan JSON schema.
"""


class ResearchPlanner:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def create_plan(self, query: str) -> ResearchPlan:
        """Formulates an actionable, structured execution plan for the query."""
        logger.info(f"Generating research plan for query: '{query}'")
        prompt = (
            f"User Research Query: \"{query}\"\n\n"
            "Analyze the intent and create an optimized, step-by-step research plan. "
            "Select the most appropriate tool for each step."
        )
        try:
            plan = self.llm.generate_structured(
                prompt=prompt,
                response_model=ResearchPlan,
                system_prompt=PLANNER_SYSTEM_PROMPT
            )
            return plan
        except Exception as e:
            logger.warning(f"Planner LLM structured generation failed ({e}). Using resilient fallback plan.")
            return self._build_fallback_plan(query)

    def _build_fallback_plan(self, query: str) -> ResearchPlan:
        """Safe fallback plan if the planner LLM fails."""
        steps = [
            PlanStep(
                step_id=1,
                description="Query technical knowledge base for authoritative specs and benchmarks.",
                tool_needed="tech_kb",
                tool_input={"topic": query[:50]},
                rationale="Retrieve verified reference data."
            ),
            PlanStep(
                step_id=2,
                description="Search web for broader context and ecosystem perspectives.",
                tool_needed="web_search",
                tool_input={"query": query},
                rationale="Gather supplementary and recent information."
            )
        ]
        return ResearchPlan(
            user_query=query,
            intent_analysis="Automated fallback decomposition for technical inquiry.",
            decomposed_steps=steps,
            information_needs=["Core architecture", "Key tradeoffs", "Practical recommendations"],
            risk_assessment="Planner LLM fallback activated due to parsing error."
        )
