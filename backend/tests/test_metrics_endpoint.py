"""
Tests for the metrics endpoint

Requirements: 12.4, 7.1, 7.2, 7.3, 7.4, 7.5
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import time

from main import app
from memory_store import MemoryEntry, MemoryMetrics
from learning_engine import SourceMetrics


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_memory_entries():
    """Create mock memory entries for testing"""
    current_time = time.time()
    
    # Create 30 mock memories with varying relevance scores
    memories = []
    for i in range(30):
        # Recent 10 have higher relevance (improvement trend)
        if i < 10:
            relevance = 0.8 + (i * 0.01)
        else:
            relevance = 0.6 + (i * 0.005)
        
        memories.append(MemoryEntry(
            memory_id=f"memory:{i}",
            query=f"test query {i}",
            results={"answer": f"test answer {i}"},
            relevance_score=relevance,
            api_sources=["api1", "api2"],
            similarity_score=0.9,
            timestamp=current_time - (i * 3600),  # Spread over hours
            session_id=None
        ))
    
    return memories


@pytest.fixture
def mock_source_metrics():
    """Create mock source metrics"""
    return {
        "api1": SourceMetrics(
            api_id="api1",
            api_name="Test API 1",
            total_uses=20,
            success_rate=0.85,
            avg_relevance=0.82,
            priority_score=0.83
        ),
        "api2": SourceMetrics(
            api_id="api2",
            api_name="Test API 2",
            total_uses=15,
            success_rate=0.75,
            avg_relevance=0.73,
            priority_score=0.74
        )
    }


@pytest.mark.asyncio
async def test_metrics_endpoint_success(client, mock_memory_entries, mock_source_metrics):
    """
    Test that metrics endpoint returns correct data
    
    Requirements: 12.4, 7.1, 7.2, 7.3, 7.5
    """
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        # Setup mocks
        mock_memory_store.get_recent = AsyncMock(return_value=mock_memory_entries)
        mock_memory_store.get_metrics = AsyncMock(return_value=MemoryMetrics(
            total_memories=30,
            avg_relevance=0.75,
            high_quality_memories=20,
            memory_size_bytes=1024000
        ))
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.analyze_source_performance = AsyncMock(return_value=mock_source_metrics)
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.65)
        
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Requirement 7.1: Total queries, average relevance, average confidence
        assert data["total_queries"] == 30
        assert 0.0 <= data["avg_relevance_score"] <= 1.0
        assert 0.0 <= data["avg_confidence_score"] <= 1.0
        
        # Requirement 7.3: Improvement trend
        assert "improvement_trend" in data
        # Should be positive since recent queries have higher relevance
        assert data["improvement_trend"] > 0
        
        # Requirement 7.2: Top performing sources
        assert "top_sources" in data
        assert len(data["top_sources"]) > 0
        assert data["top_sources"][0]["api_id"] == "api1"
        assert data["top_sources"][0]["priority_score"] == 0.83
        
        # Current confidence threshold
        assert data["confidence_threshold"] == 0.65
        
        # Memory statistics
        assert "memory_stats" in data
        assert data["memory_stats"]["total_memories"] == 30
        assert data["memory_stats"]["avg_relevance"] == 0.75
        assert data["memory_stats"]["high_quality_memories"] == 20
        
        # Recent query counts
        assert "queries_last_hour" in data
        assert "queries_last_day" in data
        assert data["queries_last_hour"] >= 0
        assert data["queries_last_day"] >= data["queries_last_hour"]


@pytest.mark.asyncio
async def test_metrics_endpoint_no_data(client):
    """
    Test metrics endpoint with no data returns defaults
    
    Requirements: 12.4, 7.5
    """
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        # Setup mocks - no memories
        mock_memory_store.get_recent = AsyncMock(return_value=[])
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.5)
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Should return default values
        assert data["total_queries"] == 0
        assert data["avg_relevance_score"] == 0.0
        assert data["avg_confidence_score"] == 0.0
        assert data["improvement_trend"] == 0.0
        assert data["top_sources"] == []
        assert data["confidence_threshold"] == 0.5
        assert data["queries_last_hour"] == 0
        assert data["queries_last_day"] == 0


@pytest.mark.asyncio
async def test_metrics_endpoint_service_not_ready(client):
    """
    Test metrics endpoint when memory store not initialized
    
    Requirements: 12.7 - Error handling
    """
    with patch('main.memory_store', None):
        # Make request
        response = client.get("/api/metrics")
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        assert "not ready" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_metrics_improvement_trend_calculation(client):
    """
    Test that improvement trend is calculated correctly
    
    Requirements: 7.3, 7.4 - Detect improvement trends
    """
    current_time = time.time()
    
    # Create memories with clear improvement trend
    # Recent 10: avg 0.85, Older 10: avg 0.65
    memories = []
    for i in range(20):
        if i < 10:
            relevance = 0.85
        else:
            relevance = 0.65
        
        memories.append(MemoryEntry(
            memory_id=f"memory:{i}",
            query=f"test query {i}",
            results={"answer": f"test answer {i}"},
            relevance_score=relevance,
            api_sources=["api1"],
            similarity_score=0.9,
            timestamp=current_time - (i * 3600),
            session_id=None
        ))
    
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        mock_memory_store.get_recent = AsyncMock(return_value=memories)
        mock_memory_store.get_metrics = AsyncMock(return_value=MemoryMetrics(
            total_memories=20,
            avg_relevance=0.75,
            high_quality_memories=10,
            memory_size_bytes=512000
        ))
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.analyze_source_performance = AsyncMock(return_value={})
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.5)
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Improvement trend should be positive (0.85 - 0.65 = 0.20)
        assert data["improvement_trend"] > 0
        assert abs(data["improvement_trend"] - 0.20) < 0.01


@pytest.mark.asyncio
async def test_metrics_time_windows(client):
    """
    Test that time window calculations work correctly
    
    Requirements: 7.2 - Compute metrics over rolling windows
    """
    current_time = time.time()
    
    # Create memories at different times
    memories = []
    
    # 5 in last hour
    for i in range(5):
        memories.append(MemoryEntry(
            memory_id=f"memory:hour:{i}",
            query=f"recent query {i}",
            results={"answer": f"answer {i}"},
            relevance_score=0.8,
            api_sources=["api1"],
            similarity_score=0.9,
            timestamp=current_time - (i * 600),  # Last hour
            session_id=None
        ))
    
    # 10 more in last day (but not last hour)
    for i in range(10):
        memories.append(MemoryEntry(
            memory_id=f"memory:day:{i}",
            query=f"day query {i}",
            results={"answer": f"answer {i}"},
            relevance_score=0.7,
            api_sources=["api1"],
            similarity_score=0.9,
            timestamp=current_time - (7200 + i * 3600),  # 2-12 hours ago
            session_id=None
        ))
    
    # 5 more older than a day
    for i in range(5):
        memories.append(MemoryEntry(
            memory_id=f"memory:old:{i}",
            query=f"old query {i}",
            results={"answer": f"answer {i}"},
            relevance_score=0.6,
            api_sources=["api1"],
            similarity_score=0.9,
            timestamp=current_time - (86400 + i * 3600),  # Older than 1 day
            session_id=None
        ))
    
    with patch('main.memory_store') as mock_memory_store, \
         patch('main.agent_orchestrator') as mock_orchestrator:
        
        mock_memory_store.get_recent = AsyncMock(return_value=memories)
        mock_memory_store.get_metrics = AsyncMock(return_value=MemoryMetrics(
            total_memories=20,
            avg_relevance=0.7,
            high_quality_memories=15,
            memory_size_bytes=512000
        ))
        
        mock_learning_engine = MagicMock()
        mock_learning_engine.analyze_source_performance = AsyncMock(return_value={})
        mock_learning_engine.get_confidence_threshold = MagicMock(return_value=0.5)
        mock_orchestrator.learning_engine = mock_learning_engine
        
        # Make request
        response = client.get("/api/metrics")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Should have 5 queries in last hour
        assert data["queries_last_hour"] == 5
        
        # Should have 15 queries in last day (5 + 10)
        assert data["queries_last_day"] == 15
        
        # Total should be 20
        assert data["total_queries"] == 20
