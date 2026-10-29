"""
Unit tests for Pydantic Schema Contracts.
"""

import pytest
from pydantic import ValidationError
from src.schema import FinalResearchResponse, SourceReference, ResearchPlan, PlanStep, ToolResult


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

