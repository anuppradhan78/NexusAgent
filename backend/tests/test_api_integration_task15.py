"""
API Integration Test for Task 15

Tests the complete flow from API endpoint to alert/report generation.

Requirements: 5.1, 6.1, 12.1
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from main import app
from agent_orchestrator import (
    ResearchResult,
    ResearchSynthesis,
    QueryIntent,
    APIResult,
    RefinedQuery
)
from alert_engine import Alert
from report_generator import ReportPath
from mcp_client import APIEndpoint


@pytest.fixture
def mock_agent_orchestrator():
    """Create a mock agent orchestrator that returns a complete result"""
    orchestrator = Mock()
    
    # Create a complete research result with alert and report
    alert = Alert(
        severity="medium",
        title="Test Alert",
        message="This is a test alert",
        key_points=["Point 1", "Point 2"],
        sources=["api1"],
        timestamp=datetime.now(),
        query="test query"
    )
    
    report_path = ReportPath(
        filename="test_report.md",
        full_path="/reports/test_report.md",
        timestamp="2025-11-22_12-00-00",
        report_id="report_123"
    )
    
    result = ResearchResult(
        query_id="query_123",
        query="test query",
        intent=QueryIntent(
            original_query="test query",
            intent_type="test",
            key_topics=["test"],
            search_terms=["test"],
            context="test context"
        ),
        synthesis=ResearchSynthesis(
            summary="Test summary",
            detailed_analysis="Test detailed analysis",
            findings=["Finding 1", "Finding 2"],
            sources=["api1"],
            source_details=[
                APIEndpoint(
                    api_id="api1",
                    api_name="Test API",
                    endpoint="/test",
                    method="GET",
                    description="Test API",
                    verified=True,
                    priority_score=0.8
                )
            ],
            confidence_score=0.85,
            confidence_breakdown={"api1": 0.85}
        ),
        similar_queries=[],
        api_results=[
            APIResult(
                api_id="api1",
                api_name="Test API",
                endpoint="/test",
                data={"result": "test"},
                success=True,
                response_time_ms=100.0
            )
        ],
        processing_time_ms=500.0,
        memory_id="memory_123",
        refined_query=RefinedQuery(
            query="test query",
            refinements=["refinement 1"],
            confidence=0.7,
            prioritized_sources=["api1"]
        ),
        alert=alert,
        report_path=report_path
    )
    
    orchestrator.process_query = AsyncMock(return_value=result)
    
    return orchestrator


def test_api_response_includes_alert_status(mock_agent_orchestrator):
    """
    Test that API response includes alert_triggered status
    
    Requirements: 12.1 - Include alert status in API response
    """
    # Patch the global agent_orchestrator
    with patch('main.agent_orchestrator', mock_agent_orchestrator):
        client = TestClient(app)
        
        response = client.post(
            "/api/research/query",
            json={
                "query": "test query about something urgent",
                "max_sources": 3,
                "include_report": True,
                "alert_enabled": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify alert status is included
        assert "alert_triggered" in data
        assert data["alert_triggered"] is True


def test_api_response_includes_report_path(mock_agent_orchestrator):
    """
    Test that API response includes report_path
    
    Requirements: 12.1 - Include report path in API response
    """
    with patch('main.agent_orchestrator', mock_agent_orchestrator):
        client = TestClient(app)
        
        response = client.post(
            "/api/research/query",
            json={
                "query": "test query",
                "max_sources": 3,
                "include_report": True,
                "alert_enabled": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify report path is included
        assert "report_path" in data
        assert data["report_path"] == "/reports/test_report.md"


def test_api_passes_alert_enabled_parameter(mock_agent_orchestrator):
    """
    Test that API passes alert_enabled parameter to orchestrator
    """
    with patch('main.agent_orchestrator', mock_agent_orchestrator):
        client = TestClient(app)
        
        response = client.post(
            "/api/research/query",
            json={
                "query": "test query",
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": True
            }
        )
        
        assert response.status_code == 200
        
        # Verify orchestrator was called with correct parameters
        mock_agent_orchestrator.process_query.assert_called_once()
        call_kwargs = mock_agent_orchestrator.process_query.call_args[1]
        assert call_kwargs["alert_enabled"] is True


def test_api_passes_include_report_parameter(mock_agent_orchestrator):
    """
    Test that API passes include_report parameter to orchestrator
    """
    with patch('main.agent_orchestrator', mock_agent_orchestrator):
        client = TestClient(app)
        
        response = client.post(
            "/api/research/query",
            json={
                "query": "test query",
                "max_sources": 3,
                "include_report": True,
                "alert_enabled": False
            }
        )
        
        assert response.status_code == 200
        
        # Verify orchestrator was called with correct parameters
        mock_agent_orchestrator.process_query.assert_called_once()
        call_kwargs = mock_agent_orchestrator.process_query.call_args[1]
        assert call_kwargs["include_report"] is True


def test_api_handles_no_alert_triggered():
    """
    Test that API correctly handles when no alert is triggered
    """
    # Create orchestrator that returns result without alert
    orchestrator = Mock()
    result = ResearchResult(
        query_id="query_123",
        query="test query",
        intent=QueryIntent(
            original_query="test query",
            intent_type="test",
            key_topics=["test"],
            search_terms=["test"],
            context="test context"
        ),
        synthesis=ResearchSynthesis(
            summary="Test summary",
            detailed_analysis="Test analysis",
            findings=["Finding 1"],
            sources=[],
            source_details=[],
            confidence_score=0.5,
            confidence_breakdown={}
        ),
        similar_queries=[],
        api_results=[],
        processing_time_ms=500.0,
        memory_id="memory_123",
        refined_query=None,
        alert=None,  # No alert
        report_path=None
    )
    orchestrator.process_query = AsyncMock(return_value=result)
    
    with patch('main.agent_orchestrator', orchestrator):
        client = TestClient(app)
        
        response = client.post(
            "/api/research/query",
            json={
                "query": "test query",
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify alert_triggered is False when no alert
        assert data["alert_triggered"] is False
        assert data["report_path"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
