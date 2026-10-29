"""
Unit tests for Pydantic Schema Contracts.
"""

import pytest
from pydantic import ValidationError
from src.schema import FinalResearchResponse, SourceReference, ResearchPlan, PlanStep, ToolResult, ComparisonRow


def test_source_reference_validation():
    source = SourceReference(
        id=1,
        title="Qdrant Docs",
        url="https://qdrant.tech",
        snippet="Vector search engine in Rust.",
        reliability_score=0.95
    )
    assert source.id == 1
    assert source.reliability_score == 0.95

    # Should fail if score is out of [0, 1] bounds
    with pytest.raises(ValidationError):
        SourceReference(
            id=2,
            title="Invalid Score",
            url="https://example.com",
            snippet="Test",
            reliability_score=1.5
        )


def test_final_research_response_schema():
    resp = FinalResearchResponse(
        user_question="Compare vector databases",
        short_answer="Qdrant and Chroma are great options.",
        key_findings=["Rust performance", "Developer ease"],
        sources_used=[
            SourceReference(
                id=1,
                title="Qdrant Docs",
                url="https://qdrant.tech",
                snippet="Test snippet",
                reliability_score=0.9
            )
        ],
        confidence_level="High",
        confidence_score=0.92,
        limitations_or_assumptions=["Assumes small team"],
        suggested_next_steps=["Run local Docker container"]
    )
    assert resp.confidence_level == "High"
    assert len(resp.key_findings) == 2
    assert len(resp.sources_used) == 1
    assert resp.comparison_matrix is None


def test_final_research_response_empty_comparison_matrix():
    resp = FinalResearchResponse(
        user_question="Explain transformers",
        short_answer="Transformers use self-attention mechanisms.",
        key_findings=["Self attention", "Multi-head attention"],
        sources_used=[],
        confidence_level="Medium",
        confidence_score=0.8,
        limitations_or_assumptions=["Theoretical overview"],
        suggested_next_steps=["Read Attention Is All You Need paper"],
        comparison_matrix=[]
    )
    assert resp.comparison_matrix == []


def test_final_research_response_populated_comparison_matrix():
    row = ComparisonRow(
        entity="Qdrant",
        category_or_license="Apache 2.0 (Rust)",
        key_capabilities="Payload filtering, HNSW",
        tradeoff_or_positioning="Fast and lightweight",
        source_citation="[1]"
    )
    resp = FinalResearchResponse(
        user_question="Compare vector databases",
        short_answer="Summary of vector databases.",
        key_findings=["Finding 1"],
        sources_used=[],
        confidence_level="High",
        confidence_score=0.9,
        limitations_or_assumptions=[],
        suggested_next_steps=[],
        comparison_matrix=[row]
    )
    assert resp.comparison_matrix is not None
    assert len(resp.comparison_matrix) == 1
    assert resp.comparison_matrix[0].entity == "Qdrant"


def test_non_comparative_question_pipeline():
    from src.agent.orchestrator import ResearchAgent
    agent = ResearchAgent()
    trace = agent.run("Research the pros and cons of using a multi-agent architecture for customer support automation.")
    assert trace.final_response is not None
    assert trace.final_response.user_question is not None
    # Non-comparative query runs cleanly without crashing
    assert hasattr(trace.final_response, "comparison_matrix")


def test_plan_step_schema():
    step = PlanStep(
        step_id=1,
        description="Search tech docs",
        tool_needed="web_search",
        tool_input={"query": "qdrant benchmarks"},
        rationale="Retrieve authoritative latency numbers"
    )
    assert step.step_id == 1
    assert step.status == "pending"

