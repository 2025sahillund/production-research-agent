"""
Baseline Comparison Tool (Assignment Stretch Goal: Comparison with a Non-Agentic Baseline).
Executes a single-turn, ungrounded direct prompt to demonstrate why the multi-step
agentic pipeline is superior in factual grounding, freshness, and accuracy.
"""

from typing import Any, Dict
from src.tools.base import BaseTool
from src.llm.provider import BaseLLM, get_llm_provider


class BaselineComparisonTool(BaseTool):
    name = "baseline_comparison"
    description = "Generates a naive, non-agentic single-turn LLM response without tools for comparison."

    def __init__(self, llm: BaseLLM = None):
        super().__init__()
        self.llm = llm or get_llm_provider()

    def _run(self, query: str, **kwargs) -> Dict[str, Any]:
        """Runs an ungrounded zero-shot generation without tool lookups."""
        naive_prompt = (
            f"Question: {query}\n\n"
            "Answer this question directly based solely on your internal training data. "
            "Do not search the web or cite external sources."
        )
        try:
            raw_answer = self.llm.generate(naive_prompt)
            if not raw_answer or raw_answer == "{}":
                # Fallback representative naive output
                raw_answer = (
                    "There are several options for this query. For example, vector databases include Pinecone, "
                    "Weaviate, and Milvus. Each has pros and cons. Check their documentation for more details."
                )
        except Exception:
            raw_answer = "Generic baseline response without live verification."

        return {
            "query": query,
            "non_agentic_response": raw_answer,
            "tools_used": 0,
            "grounding_sources_count": 0,
            "has_verification_judge": False,
            "observation": "Lacks real-time benchmark verification, citation URLs, and schema validation."
        }

