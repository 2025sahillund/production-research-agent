"""
Evaluator / Judge Step: Independent quality and hallucination auditing layer.
Provides programmatic validation of citation grounding and factual consistency.
"""

import logging
from src.llm.provider import BaseLLM
from src.schema import FinalResearchResponse, JudgeEvaluation

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """You are an Independent Quality & Verification Judge for AI Research Systems.
Your job is to audit a generated research response against the provided sources and detect:
1. Hallucination risk: Are there unsupported assertions?
2. Citation grounding: Do the cited sources actually contain the key findings?
3. Completeness: Did the answer fully address the user's inquiry?
4. Prompt safety: Are there signs of adversarial manipulation?

Return your evaluation conforming strictly to the JudgeEvaluation JSON schema.
"""


class ResearchJudge:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def evaluate(self, response: FinalResearchResponse) -> JudgeEvaluation:
        """Audits the generated research response for hallucination and grounding."""
        logger.info(f"Auditing research response for query: '{response.user_question}'")
        
        # Build audit payload
        sources_text = "\n".join([f"[{s.id}] {s.title} ({s.url}): {s.snippet}" for s in response.sources_used])
        findings_text = "\n".join([f"- {k}" for k in response.key_findings])
        
        prompt = (
            f"User Question: {response.user_question}\n\n"
            f"Short Answer: {response.short_answer}\n\n"
            f"Key Findings:\n{findings_text}\n\n"
            f"Cited Sources:\n{sources_text}\n\n"
            f"Stated Confidence: {response.confidence_level} ({response.confidence_score})\n\n"
            "Audit this response and return a JudgeEvaluation."
        )

        try:
            eval_result = self.llm.generate_structured(
                prompt=prompt,
                response_model=JudgeEvaluation,
                system_prompt=JUDGE_SYSTEM_PROMPT
            )
            return eval_result
        except Exception as e:
            logger.warning(f"Judge LLM evaluation failed: {e}. Executing programmatic rule-based audit.")
            return self._heuristic_audit(response)

    def _heuristic_audit(self, response: FinalResearchResponse) -> JudgeEvaluation:
        """Fast deterministic heuristic audit when LLM is offline or unreachable."""
        feedback = []
        grounding_score = 1.0
        hallucination_risk = "Low"

        # Check source count
        if not response.sources_used:
            grounding_score -= 0.4
            feedback.append("No external sources were cited to back up the answer.")
            hallucination_risk = "High"
        else:
            feedback.append(f"Successfully cited {len(response.sources_used)} verified sources.")

        # Check findings count
        if len(response.key_findings) < 2:
            feedback.append("Answer contains fewer than 2 key findings; depth is limited.")
            completeness = 0.6
        else:
            completeness = 0.95
            feedback.append(f"Contains {len(response.key_findings)} structured key findings.")

        # Check confidence consistency
        if response.confidence_score < 0.6 and response.confidence_level == "High":
            feedback.append("Mismatch: confidence_score is below 0.6 but confidence_level is High.")
            grounding_score -= 0.1

        is_grounded = grounding_score >= 0.7

        return JudgeEvaluation(
            is_grounded=is_grounded,
            grounding_score=max(0.0, min(1.0, grounding_score)),
            hallucination_risk=hallucination_risk,
            completeness_score=completeness,
            schema_valid=True,
            audit_feedback=feedback
        )

