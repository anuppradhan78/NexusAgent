"""
Integration Tests for Session Management with API Endpoints

Tests multi-turn conversation functionality through the API.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from session_manager import SessionManager


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_components():
    """Mock all external dependencies"""
    with patch('main.mcp_client') as mock_mcp, \
         patch('main.memory_store') as mock_memory, \
         patch('main.agent_orchestrator') as mock_orchestrator, \
         patch('main.session_manager') as mock_session:
        
        # Configure mocks
        mock_session.create_session.return_value = "session_test_123"
        mock_session.get_session_history.return_value = []
        mock_session.add_query_to_session.return_value = True
        mock_session.delete_session.return_value = True
        mock_session.session_expiration_seconds = 3600
        
        yield {
            'mcp_client': mock_mcp,
            'memory_store': mock_memory,
            'agent_orchestrator': mock_orchestrator,
            'session_manager': mock_session
        }


def test_create_session_endpoint(client, mock_components):
    """
    Test creating a session via API endpoint.
    
    Requirements: 15.5 - Support session management with unique session IDs
    """
    response = client.post("/api/session")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert data["session_id"] == "session_test_123"
    assert "created_at" in data
    assert "expiration_seconds" in data
    assert data["expiration_seconds"] == 3600


def test_get_session_history_endpoint(client, mock_components):
    """
    Test retrieving session history via API endpoint.
    
    Requirements:
    - 15.2: Use previous query results as context
    - 15.3: Allow users to reference previous results
    """
    # Mock session history
    from session_manager import QueryHistoryItem
    mock_history = [
        QueryHistoryItem(
            query_id="query_1",
            query="What is AI?",
            synthesized_answer="AI is artificial intelligence...",
            sources=["api_1", "api_2"],
            confidence_score=0.85,
            timestamp=1234567890.0,
            memory_id="memory_1"
        ),
        QueryHistoryItem(
            query_id="query_2",
            query="Tell me more",
            synthesized_answer="AI involves machine learning...",
            sources=["api_1"],
            confidence_score=0.90,
            timestamp=1234567900.0,
            memory_id="memory_2"
        )
    ]
    
    mock_components['session_manager'].get_session_history.return_value = mock_history
    
    response = client.get("/api/session/session_test_123/history")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["session_id"] == "session_test_123"
    assert data["query_count"] == 2
    assert len(data["history"]) == 2
    
    # Verify first query
    first_query = data["history"][0]
    assert first_query["query_id"] == "query_1"
    assert first_query["query"] == "What is AI?"
    assert first_query["confidence_score"] == 0.85
    
    # Verify second query
    second_query = data["history"][1]
    assert second_query["query_id"] == "query_2"
    assert second_query["query"] == "Tell me more"


def test_get_session_history_not_found(client, mock_components):
    """
    Test retrieving history for non-existent session.
    
    Requirements: 15.5 - Session management error handling
    """
    mock_components['session_manager'].get_session_history.return_value = None
    
    response = client.get("/api/session/session_nonexistent/history")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_session_endpoint(client, mock_components):
    """
    Test deleting a session via API endpoint.
    
    Requirements: 15.6 - Session management
    """
    response = client.delete("/api/session/session_test_123")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "deleted successfully" in data["message"].lower()


def test_delete_session_not_found(client, mock_components):
    """
    Test deleting a non-existent session.
    
    Requirements: 15.6 - Session management error handling
    """
    mock_components['session_manager'].delete_session.return_value = False
    
    response = client.delete("/api/session/session_nonexistent")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_research_query_with_session(client, mock_components):
    """
    Test research query with session context.
    
    Requirements:
    - 15.1: Maintain conversation context across multiple queries
    - 15.5: Support session management with unique session IDs
    """
    # Mock agent orchestrator response
    from agent_orchestrator import ResearchResult, QueryIntent, ResearchSynthesis
    from mcp_client import APIEndpoint
    
    mock_result = MagicMock()
    mock_result.query_id = "query_123"
    mock_result.query = "What is AI?"
    mock_result.intent = QueryIntent(
        original_query="What is AI?",
        intent_type="factual",
        key_topics=["AI"],
        search_terms=["artificial intelligence"],
        context="User wants to learn about AI"
    )
    mock_result.synthesis = ResearchSynthesis(
        summary="AI is artificial intelligence",
        detailed_analysis="Detailed analysis...",
        findings=["Finding 1", "Finding 2"],
        sources=["api_1"],
        source_details=[],
        confidence_score=0.85,
        confidence_breakdown={"api_1": 0.85}
    )
    mock_result.similar_queries = []
    mock_result.api_results = []
    mock_result.processing_time_ms = 1000.0
    mock_result.memory_id = "memory_123"
    mock_result.refined_query = None
    mock_result.alert = None
    mock_result.report_path = None
    
    mock_components['agent_orchestrator'].process_query = AsyncMock(return_value=mock_result)
    mock_components['session_manager'].get_session.return_value = MagicMock(session_id="session_test_123")
    
    # Make request with session_id
    response = client.post(
        "/api/research/query",
        json={
            "query": "What is AI?",
            "session_id": "session_test_123",
            "max_sources": 5,
            "include_report": False,
            "alert_enabled": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify session_id is in response
    assert data["session_id"] == "session_test_123"
    assert data["query_id"] == "query_123"
    
    # Verify add_query_to_session was called
    mock_components['session_manager'].add_query_to_session.assert_called_once()


def test_research_query_creates_session_if_none(client, mock_components):
    """
    Test that research query creates a session if none provided.
    
    Requirements: 15.5 - Support session management with unique session IDs
    """
    # Mock agent orchestrator response
    mock_result = MagicMock()
    mock_result.query_id = "query_123"
    mock_result.query = "What is AI?"
    mock_result.intent = MagicMock()
    mock_result.synthesis = MagicMock()
    mock_result.synthesis.summary = "AI is artificial intelligence"
    mock_result.synthesis.detailed_analysis = "Detailed analysis..."
    mock_result.synthesis.findings = []
    mock_result.synthesis.sources = []
    mock_result.synthesis.source_details = []
    mock_result.synthesis.confidence_score = 0.85
    mock_result.similar_queries = []
    mock_result.api_results = []
    mock_result.processing_time_ms = 1000.0
    mock_result.memory_id = "memory_123"
    mock_result.refined_query = None
    mock_result.alert = None
    mock_result.report_path = None
    
    mock_components['agent_orchestrator'].process_query = AsyncMock(return_value=mock_result)
    
    # Make request without session_id
    response = client.post(
        "/api/research/query",
        json={
            "query": "What is AI?",
            "max_sources": 5,
            "include_report": False,
            "alert_enabled": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify a session was created
    mock_components['session_manager'].create_session.assert_called()
    
    # Verify session_id is in response
    assert "session_id" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
