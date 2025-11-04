from pydantic import BaseModel
from typing import List


class MockResearchResponse(BaseModel):
    topic: str
    abstract: str
    introduction: str
    literature_review: str
    methodology: str
    analysis_and_findings: str
    discussion: str
    future_research: str
    conclusion: str
    sources: List[str]
    tools_used: List[str]


def test_build_paper_structure():
    """Test that we can build a basic paper structure without any external dependencies"""
    # Import here to avoid loading external dependencies
    from main_simple import build_paper_text
    
    rr = MockResearchResponse(
        topic="Test Topic",
        abstract="Short abstract.",
        introduction="Intro.",
        literature_review="Literature.",
        methodology="Methodology.",
        analysis_and_findings="Findings.",
        discussion="Discussion.",
        future_research="Future.",
        conclusion="Conclusion.",
        sources=["Source A", "Source B"],
        tools_used=["web_search", "wikipedia"],
    )

    paper = build_paper_text(rr)
    assert "ABSTRACT" in paper
    assert "INTRODUCTION" in paper
    assert "REFERENCES" in paper
    assert rr.topic.upper() in paper
