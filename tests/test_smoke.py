from main_simple import ResearchResponse, build_paper_text


def test_build_paper_text():
    rr = ResearchResponse(
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
