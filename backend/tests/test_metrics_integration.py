"""
Integration test for metrics endpoint

This test verifies the metrics endpoint works with real components
(but mocked external dependencies like MCP and Redis)

Requirements: 12.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import time

from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_metrics_endpoint_structure(client):
    """
    Test that metrics endpoint returns correct structure
    
    Requirements: 12.4 - GET /api/metrics endpoint structure
    """
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        # Setup minimal mocks
        mock_memory_store.get_recent = AsyncMock(return_value=[])
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.5)
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        required_fields = [
            "total_queries",
            "avg_relevance_score",
            "avg_confidence_score",
            "improvement_trend",
            "top_sources",
            "confidence_threshold",
            "memory_stats",
            "queries_last_hour",
            "queries_last_day"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check memory_stats structure
        memory_stats_fields = [
            "total_memories",
            "avg_relevance",
            "high_quality_memories",
            "memory_size_bytes"
        ]
        
        for field in memory_stats_fields:
            assert field in data["memory_stats"], f"Missing memory_stats field: {field}"
        
        # Check data types
        assert isinstance(data["total_queries"], int)
        assert isinstance(data["avg_relevance_score"], float)
        assert isinstance(data["avg_confidence_score"], float)
        assert isinstance(data["improvement_trend"], float)
        assert isinstance(data["top_sources"], list)
        assert isinstance(data["confidence_threshold"], float)
        assert isinstance(data["memory_stats"], dict)
        assert isinstance(data["queries_last_hour"], int)
        assert isinstance(data["queries_last_day"], int)


def test_metrics_endpoint_value_ranges(client):
    """
    Test that metrics values are within expected ranges
    
    Requirements: 7.1 - Metric value validation
    """
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        # Setup minimal mocks
        mock_memory_store.get_recent = AsyncMock(return_value=[])
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.5)
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check value ranges
        assert data["total_queries"] >= 0
        assert 0.0 <= data["avg_relevance_score"] <= 1.0
        assert 0.0 <= data["avg_confidence_score"] <= 1.0
        assert 0.0 <= data["confidence_threshold"] <= 1.0
        assert data["queries_last_hour"] >= 0
        assert data["queries_last_day"] >= 0
        assert data["queries_last_day"] >= data["queries_last_hour"]
        
        # Memory stats ranges
        assert data["memory_stats"]["total_memories"] >= 0
        assert 0.0 <= data["memory_stats"]["avg_relevance"] <= 1.0
        assert data["memory_stats"]["high_quality_memories"] >= 0
        assert data["memory_stats"]["memory_size_bytes"] >= 0


def test_metrics_endpoint_top_sources_structure(client):
    """
    Test that top_sources have correct structure
    
    Requirements: 7.2 - Top performing API sources
    """
    from memory_store import MemoryEntry
    from learning_engine import SourceMetrics
    
    current_time = time.time()
    
    # Create mock memories
    memories = [
        MemoryEntry(
            memory_id=f"memory:{i}",
            query=f"test query {i}",
            results={"answer": f"answer {i}"},
            relevance_score=0.8,
            api_sources=["api1", "api2"],
            similarity_score=0.9,
            timestamp=current_time - (i * 3600),
            session_id=None
        )
        for i in range(10)
    ]
    
    mock_source_metrics = {
        "api1": SourceMetrics(
            api_id="api1",
            api_name="Test API 1",
            total_uses=10,
            success_rate=0.9,
            avg_relevance=0.85,
            priority_score=0.87
        )
    }
    
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        mock_memory_store.get_recent = AsyncMock(return_value=memories)
        mock_memory_store.get_metrics = AsyncMock(return_value=MagicMock(
            total_memories=10,
            avg_relevance=0.8,
            high_quality_memories=8,
            memory_size_bytes=102400
        ))
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.analyze_source_performance = AsyncMock(return_value=mock_source_metrics)
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.5)
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check top_sources structure
        if len(data["top_sources"]) > 0:
            source = data["top_sources"][0]
            
            required_source_fields = [
                "api_id",
                "api_name",
                "total_uses",
                "success_rate",
                "avg_relevance",
                "avg_response_time_ms",
                "priority_score"
            ]
            
            for field in required_source_fields:
                assert field in source, f"Missing source field: {field}"
            
            # Check value ranges
            assert source["total_uses"] >= 0
            assert 0.0 <= source["success_rate"] <= 1.0
            assert 0.0 <= source["avg_relevance"] <= 1.0
            assert source["avg_response_time_ms"] >= 0.0
            assert 0.0 <= source["priority_score"] <= 1.0


def test_metrics_endpoint_error_handling(client):
    """
    Test that metrics endpoint handles errors gracefully
    
    Requirements: 12.7 - Error handling
    """
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        # Setup mocks to raise exception
        mock_memory_store.get_recent = AsyncMock(side_effect=Exception("Test error"))
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.5)
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Should return 500 error
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
