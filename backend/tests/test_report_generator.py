"""
Tests for Report Generator

This module tests the ReportGenerator class to ensure it creates
comprehensive markdown reports correctly.
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from report_generator import ReportGenerator, ReportPath, ReportGeneratorError
from agent_orchestrator import ResearchSynthesis, APIResult, QueryIntent
from memory_store import MemoryEntry
from mcp_client import APIEndpoint


@pytest.fixture
def temp_reports_dir():
    """Create temporary directory for test reports"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_query_intent():
    """Sample query intent for testing"""
    return QueryIntent(
        original_query="What are the latest AI trends?",
        intent_type="trend_analysis",
        key_topics=["artificial intelligence", "machine learning", "trends"],
        search_terms=["AI trends", "ML developments", "AI research"],
        context="User wants to understand current AI trends"
    )


@pytest.fixture
def sample_synthesis():
    """Sample synthesis for testing"""
    return ResearchSynthesis(
        summary="AI is rapidly evolving with focus on large language models and multimodal systems.",
        detailed_analysis="Detailed analysis paragraph 1.\n\nParagraph 2 with more details.\n\nParagraph 3 conclusion.",
        findings=[
            "Large language models are becoming more capable",
            "Multimodal AI is gaining traction",
            "AI safety research is increasing"
        ],
        sources=["api_1", "api_2"],
        source_details=[
            APIEndpoint(
                api_id="api_1",
                api_name="Tech News API",
                endpoint="/v1/news",
                method="GET",
                description="Tech news",
                verified=True,
                priority_score=0.8
            ),
            APIEndpoint(
                api_id="api_2",
                api_name="Research Papers API",
                endpoint="/v1/papers",
                method="GET",
                description="Research papers",
                verified=True,
                priority_score=0.7
            )
        ],
        confidence_score=0.85,
        confidence_breakdown={
            "api_1": 0.9,
            "api_2": 0.8
        }
    )


@pytest.fixture
def sample_api_results():
    """Sample API results for testing"""
    return [
        APIResult(
            api_id="api_1",
            api_name="Tech News API",
            endpoint="/v1/news",
            data={"articles": ["article1", "article2"]},
            success=True,
            response_time_ms=250.0
        ),
        APIResult(
            api_id="api_2",
            api_name="Research Papers API",
            endpoint="/v1/papers",
            data={"papers": ["paper1", "paper2"]},
            success=True,
            response_time_ms=300.0
        )
    ]


@pytest.fixture
def sample_similar_queries():
    """Sample similar queries for testing"""
    return [
        MemoryEntry(
            memory_id="mem_1",
            query="AI developments in 2024",
            results={"summary": "AI is advancing rapidly"},
            relevance_score=0.9,
            api_sources=["api_1"],
            similarity_score=0.85,
            timestamp=1700000000.0
        )
    ]


@pytest.mark.asyncio
async def test_report_generator_initialization(temp_reports_dir):
    """Test that ReportGenerator initializes correctly"""
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    assert generator.output_dir == Path(temp_reports_dir)
    assert generator.output_dir.exists()


@pytest.mark.asyncio
async def test_generate_report_creates_file(
    temp_reports_dir,
    sample_query_intent,
    sample_synthesis,
    sample_api_results,
    sample_similar_queries
):
    """Test that generate() creates a report file"""
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    metadata = {
        "processing_time_ms": 2500.0,
        "session_id": "session_123",
        "alert_triggered": False,
        "refinement_applied": True,
        "refinement_confidence": 0.75,
        "refinements": ["Added search term: AI research"]
    }
    
    report_path = await generator.generate(
        query="What are the latest AI trends?",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=sample_synthesis,
        api_results=sample_api_results,
        similar_queries=sample_similar_queries,
        metadata=metadata
    )
    
    # Verify report was created
    assert report_path.filename.startswith("research_report_")
    assert report_path.filename.endswith(".md")
    assert Path(report_path.full_path).exists()
    assert report_path.report_id.startswith("report_")


@pytest.mark.asyncio
async def test_report_contains_required_sections(
    temp_reports_dir,
    sample_query_intent,
    sample_synthesis,
    sample_api_results,
    sample_similar_queries
):
    """
    Test that generated report contains all required sections.
    
    Requirements: 6.1, 6.2, 6.3, 6.5
    """
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    metadata = {
        "processing_time_ms": 2500.0,
        "session_id": "session_123",
        "alert_triggered": False
    }
    
    report_path = await generator.generate(
        query="What are the latest AI trends?",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=sample_synthesis,
        api_results=sample_api_results,
        similar_queries=sample_similar_queries,
        metadata=metadata
    )
    
    # Read report content
    content = Path(report_path.full_path).read_text(encoding='utf-8')
    
    # Verify required sections exist
    # Requirements: 6.2 - Executive summary, findings, sources, confidence
    assert "# Research Report:" in content
    assert "## Executive Summary" in content
    assert "## Key Findings" in content
    assert "## Detailed Analysis" in content
    assert "## Sources" in content
    assert "## Confidence Assessment" in content
    assert "## Key Insights & Patterns" in content
    assert "## Related Research" in content
    assert "## Metadata" in content
    
    # Verify metadata is included
    # Requirements: 6.5 - Include metadata
    assert "**Generated:**" in content
    assert "**Report ID:**" in content
    assert "**Query ID:**" in content
    assert "**Confidence Score:**" in content
    assert "**Processing Time:**" in content


@pytest.mark.asyncio
async def test_report_includes_source_citations(
    temp_reports_dir,
    sample_query_intent,
    sample_synthesis,
    sample_api_results,
    sample_similar_queries
):
    """
    Test that report includes proper source citations.
    
    Requirements: 6.2 - Include source citations
    """
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    metadata = {"processing_time_ms": 2500.0}
    
    report_path = await generator.generate(
        query="What are the latest AI trends?",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=sample_synthesis,
        api_results=sample_api_results,
        similar_queries=sample_similar_queries,
        metadata=metadata
    )
    
    content = Path(report_path.full_path).read_text(encoding='utf-8')
    
    # Verify sources are cited
    assert "Tech News API" in content
    assert "Research Papers API" in content
    assert "api_1" in content
    assert "api_2" in content
    assert "**Verified:**" in content
    assert "**Response Time:**" in content


@pytest.mark.asyncio
async def test_report_includes_confidence_assessment(
    temp_reports_dir,
    sample_query_intent,
    sample_synthesis,
    sample_api_results,
    sample_similar_queries
):
    """
    Test that report includes confidence assessment.
    
    Requirements: 6.2 - Include confidence assessments
    """
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    metadata = {"processing_time_ms": 2500.0}
    
    report_path = await generator.generate(
        query="What are the latest AI trends?",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=sample_synthesis,
        api_results=sample_api_results,
        similar_queries=sample_similar_queries,
        metadata=metadata
    )
    
    content = Path(report_path.full_path).read_text(encoding='utf-8')
    
    # Verify confidence information
    assert "**Overall Confidence:** 0.85" in content
    assert "Confidence by Source" in content
    assert "**Interpretation:**" in content


@pytest.mark.asyncio
async def test_report_uses_bullet_points(
    temp_reports_dir,
    sample_query_intent,
    sample_synthesis,
    sample_api_results,
    sample_similar_queries
):
    """
    Test that report uses bullet points for organization.
    
    Requirements: 6.3 - Use bullet points
    """
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    metadata = {"processing_time_ms": 2500.0}
    
    report_path = await generator.generate(
        query="What are the latest AI trends?",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=sample_synthesis,
        api_results=sample_api_results,
        similar_queries=sample_similar_queries,
        metadata=metadata
    )
    
    content = Path(report_path.full_path).read_text(encoding='utf-8')
    
    # Count bullet points (should have many)
    bullet_count = content.count("\n- ")
    assert bullet_count >= 10, f"Expected at least 10 bullet points, found {bullet_count}"


@pytest.mark.asyncio
async def test_report_with_empty_findings(
    temp_reports_dir,
    sample_query_intent,
    sample_api_results,
    sample_similar_queries
):
    """Test report generation with empty findings"""
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    # Create synthesis with no findings
    synthesis = ResearchSynthesis(
        summary="Summary",
        detailed_analysis="Analysis",
        findings=[],
        sources=[],
        source_details=[],
        confidence_score=0.5,
        confidence_breakdown={}
    )
    
    metadata = {"processing_time_ms": 1000.0}
    
    report_path = await generator.generate(
        query="Test query",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=synthesis,
        api_results=sample_api_results,
        similar_queries=sample_similar_queries,
        metadata=metadata
    )
    
    content = Path(report_path.full_path).read_text(encoding='utf-8')
    
    # Should handle empty findings gracefully
    assert "## Key Findings" in content
    assert "No specific findings identified" in content


@pytest.mark.asyncio
async def test_report_with_no_similar_queries(
    temp_reports_dir,
    sample_query_intent,
    sample_synthesis,
    sample_api_results
):
    """Test report generation with no similar queries"""
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    metadata = {"processing_time_ms": 1000.0}
    
    report_path = await generator.generate(
        query="Test query",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=sample_synthesis,
        api_results=sample_api_results,
        similar_queries=[],
        metadata=metadata
    )
    
    content = Path(report_path.full_path).read_text(encoding='utf-8')
    
    # Should handle no similar queries gracefully
    assert "## Related Research" in content
    assert "No similar past research found" in content


@pytest.mark.asyncio
async def test_report_with_failed_apis(
    temp_reports_dir,
    sample_query_intent,
    sample_synthesis,
    sample_similar_queries
):
    """Test report generation with failed API calls"""
    generator = ReportGenerator(output_dir=temp_reports_dir)
    
    # Create API results with failures
    api_results = [
        APIResult(
            api_id="api_1",
            api_name="Failed API",
            endpoint="/v1/test",
            data={},
            success=False,
            error="Connection timeout",
            response_time_ms=5000.0
        )
    ]
    
    metadata = {"processing_time_ms": 5000.0}
    
    report_path = await generator.generate(
        query="Test query",
        query_id="query_123",
        intent=sample_query_intent,
        synthesis=sample_synthesis,
        api_results=api_results,
        similar_queries=sample_similar_queries,
        metadata=metadata
    )
    
    content = Path(report_path.full_path).read_text(encoding='utf-8')
    
    # Should include error information
    assert "**Status:** Failed" in content
    assert "**Error:** Connection timeout" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
