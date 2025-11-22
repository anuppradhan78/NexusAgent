"""
Tests for Research Query API Endpoint

Requirements: 12.1, 12.7, 1.1, 1.3, 1.4, 1.5
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from main import app
from agent_orchestrator import ResearchResult, QueryIntent, ResearchSynthesis, APIResult
from mcp_client import APIEndpoint
from memory_store import MemoryEntry


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_research_result():
    """Create mock research result"""
    return ResearchResult(
        query_id="test_query_123",
        query="What are the latest AI trends?",
        intent=QueryIntent(
            original_query="What are the latest AI trends?",
            intent_type="trend_analysis",
            key_topics=["AI", "trends", "2024"],
            search_terms=["AI trends", "machine learning"],
            context="User wants to know about AI trends"
        ),
        synthesis=ResearchSynthesis(
            summary="AI is rapidly evolving with focus on LLMs and multimodal models.",
            detailed_analysis="Detailed analysis of AI trends...",
            findings=[
                "Large Language Models are becoming more capable",
                "Multimodal AI is gaining traction",
                "AI safety is a growing concern"
            ],
            sources=["api1", "api2"],
            source_details=[
                APIEndpoint(
                    api_id="api1",
                    api_name="Tech News API",
                    endpoint="/v1/news",
                    method="GET",
                    description="Tech news",
                    verified=True,
                    priority_score=0.8
                ),
                APIEndpoint(
                    api_id="api2",
                    api_name="Research API",
                    endpoint="/v1/research",
                    method="GET",
                    description="Research papers",
                    verified=True,
                    priority_score=0.7
                )
            ],
            confidence_score=0.85,
            confidence_breakdown={"api1": 0.9, "api2": 0.8}
        ),
        similar_queries=[
            MemoryEntry(
                memory_id="mem1",
                query="AI developments",
                results={"summary": "Previous AI research"},
                relevance_score=0.8,
                api_sources=["api1"],
                similarity_score=0.75,
                timestamp=1234567890.0,
                session_id=None
            )
        ],
        api_results=[
            APIResult(
                api_id="api1",
                api_name="Tech News API",
                endpoint="/v1/news",
                data={"articles": []},
                success=True,
                error=None,
                response_time_ms=150.0
            ),
            APIResult(
                api_id="api2",
                api_name="Research API",
                endpoint="/v1/research",
                data={"papers": []},
                success=True,
                error=None,
                response_time_ms=200.0
            )
        ],
        processing_time_ms=2500.0,
        memory_id="memory_123"
    )


def test_research_query_endpoint_not_initialized(client):
    """
    Test research query endpoint when agent orchestrator is not initialized.
    
    Requirements: 12.7 - Handle errors gracefully with appropriate status codes
    """
    # The app starts without initialization in test mode
    response = client.post(
        "/api/research/query",
        json={
            "query": "What are the latest AI trends?",
            "max_sources": 3
        }
    )
    
    # Should return 503 Service Unavailable
    assert response.status_code == 503
    assert "not initialized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_research_query_validation():
    """
    Test request validation for research query endpoint.
    
    Requirements: 12.1 - Accept ResearchRequest with validation
    """
    from models import ResearchRequest
    from pydantic import ValidationError
    
    # Test valid request
    valid_request = ResearchRequest(
        query="What are the latest AI trends?",
        max_sources=3
    )
    assert valid_request.query == "What are the latest AI trends?"
    assert valid_request.max_sources == 3
    
    # Test query too short
    with pytest.raises(ValidationError) as exc_info:
        ResearchRequest(query="short")
    assert "at least 10 characters" in str(exc_info.value).lower()
    
    # Test query too long
    with pytest.raises(ValidationError) as exc_info:
        ResearchRequest(query="x" * 501)
    assert "at most 500 characters" in str(exc_info.value).lower()
    
    # Test max_sources out of range
    with pytest.raises(ValidationError) as exc_info:
        ResearchRequest(query="Valid query here", max_sources=15)
    assert "less than or equal to 10" in str(exc_info.value).lower()
    
    # Test empty/whitespace query
    with pytest.raises(ValidationError) as exc_info:
        ResearchRequest(query="          ")
    assert "empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_research_query_response_model():
    """
    Test response model structure for research query endpoint.
    
    Requirements: 1.4 - Include source citations with confidence scores
    """
    from models import ResearchResponse, APISource, MemoryEntry
    
    # Create response
    response = ResearchResponse(
        query_id="test_123",
        session_id="session_456",
        synthesized_answer="Test answer",
        detailed_analysis="Detailed analysis",
        findings=["Finding 1", "Finding 2"],
        sources=[
            APISource(
                api_id="api1",
                api_name="Test API",
                endpoint="/test",
                method="GET",
                verified=True,
                priority_score=0.8,
                response_time_ms=150.0
            )
        ],
        confidence_score=0.85,
        alert_triggered=False,
        report_path=None,
        processing_time_ms=2500.0,
        similar_past_queries=[],
        memory_id="mem_123"
    )
    
    # Verify structure
    assert response.query_id == "test_123"
    assert response.confidence_score == 0.85
    assert len(response.sources) == 1
    assert response.sources[0].api_id == "api1"
    assert response.sources[0].response_time_ms == 150.0


@pytest.mark.asyncio
async def test_feedback_request_validation():
    """
    Test request validation for feedback endpoint.
    
    Requirements: 12.2 - Accept FeedbackRequest with validation
    """
    from models import FeedbackRequest
    from pydantic import ValidationError
    
    # Test valid request
    valid_request = FeedbackRequest(
        query_id="query_123",
        memory_id="memory_456",
        relevance_score=0.8,
        feedback_notes="Very helpful information"
    )
    assert valid_request.query_id == "query_123"
    assert valid_request.memory_id == "memory_456"
    assert valid_request.relevance_score == 0.8
    
    # Test relevance score out of range (too high)
    with pytest.raises(ValidationError) as exc_info:
        FeedbackRequest(
            query_id="query_123",
            memory_id="memory_456",
            relevance_score=1.5
        )
    assert "less than or equal to 1" in str(exc_info.value).lower()
    
    # Test relevance score out of range (too low)
    with pytest.raises(ValidationError) as exc_info:
        FeedbackRequest(
            query_id="query_123",
            memory_id="memory_456",
            relevance_score=-0.1
        )
    assert "greater than or equal to 0" in str(exc_info.value).lower()
    
    # Test feedback notes too long
    with pytest.raises(ValidationError) as exc_info:
        FeedbackRequest(
            query_id="query_123",
            memory_id="memory_456",
            relevance_score=0.8,
            feedback_notes="x" * 1001
        )
    assert "at most 1000 characters" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_feedback_response_model():
    """
    Test response model structure for feedback endpoint.
    
    Requirements: 12.2 - POST /api/research/feedback response model
    """
    from models import FeedbackResponse
    
    # Create response
    response = FeedbackResponse(
        success=True,
        message="Feedback recorded successfully",
        memory_id="memory_456",
        new_relevance_score=0.9
    )
    
    # Verify structure
    assert response.success is True
    assert response.message == "Feedback recorded successfully"
    assert response.memory_id == "memory_456"
    assert response.new_relevance_score == 0.9


def test_feedback_endpoint_not_initialized(client):
    """
    Test feedback endpoint when memory store is not initialized.
    
    Requirements: 12.7 - Handle errors gracefully with appropriate status codes
    """
    response = client.post(
        "/api/research/feedback",
        json={
            "query_id": "query_123",
            "memory_id": "memory_456",
            "relevance_score": 0.8
        }
    )
    
    # Should return 503 Service Unavailable
    assert response.status_code == 503
    assert "not initialized" in response.json()["detail"].lower()


def test_models_import():
    """Test that all models can be imported successfully"""
    from models import (
        ResearchRequest,
        ResearchResponse,
        APISource,
        ResearchSynthesis,
        MemoryEntry,
        FeedbackRequest,
        FeedbackResponse,
        HistoryEntry,
        HistoryResponse,
        SourceMetrics,
        MetricsResponse,
        ReportMetadata,
        ReportsListResponse,
        ReportContent,
        ScheduleRequest,
        ScheduleResponse,
        HealthResponse,
        ErrorResponse
    )
    
    # All imports successful
    assert ResearchRequest is not None
    assert ResearchResponse is not None
    assert APISource is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
