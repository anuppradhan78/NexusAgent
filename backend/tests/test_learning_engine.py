"""
Tests for Learning Engine

Tests the core learning functionality including:
- Query refinement based on patterns
- Confidence threshold adjustment
- Source performance analysis
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import time

from learning_engine import (
    LearningEngine,
    RefinedQuery,
    SourceMetrics,
    FeedbackEntry
)
from memory_store import MemoryEntry
from mcp_client import MCPClient


@pytest.fixture
def mock_memory_store():
    """Create a mock memory store"""
    store = Mock()
    store.get_recent = AsyncMock(return_value=[])
    return store


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client"""
    client = Mock()
    client.call_claude = AsyncMock(return_value='{"refinements": ["add more context", "specify time range"], "reasoning": "test reasoning"}')
    return client


@pytest.fixture
def learning_engine(mock_memory_store, mock_mcp_client):
    """Create a learning engine instance"""
    return LearningEngine(
        memory_store=mock_memory_store,
        mcp_client=mock_mcp_client,
        initial_confidence_threshold=0.5,
        learning_rate=0.1
    )


@pytest.mark.asyncio
async def test_refine_query_no_patterns(learning_engine):
    """Test query refinement with no similar patterns"""
    result = await learning_engine.refine_query(
        original_query="test query",
        similar_patterns=[]
    )
    
    assert isinstance(result, RefinedQuery)
    assert result.query == "test query"
    assert len(result.refinements) == 0
    assert result.confidence == 0.5
    assert len(result.prioritized_sources) == 0


@pytest.mark.asyncio
async def test_refine_query_with_successful_patterns(learning_engine):
    """Test query refinement with successful patterns"""
    patterns = [
        MemoryEntry(
            memory_id="mem1",
            query="similar query 1",
            results={"answer": "test"},
            relevance_score=0.9,
            api_sources=["api1", "api2"],
            similarity_score=0.8,
            timestamp=time.time()
        ),
        MemoryEntry(
            memory_id="mem2",
            query="similar query 2",
            results={"answer": "test"},
            relevance_score=0.8,
            api_sources=["api1", "api3"],
            similarity_score=0.7,
            timestamp=time.time()
        )
    ]
    
    result = await learning_engine.refine_query(
        original_query="test query",
        similar_patterns=patterns
    )
    
    assert isinstance(result, RefinedQuery)
    assert result.query == "test query"
    assert len(result.refinements) > 0
    assert result.confidence > 0.5
    assert len(result.prioritized_sources) > 0
    assert "api1" in result.prioritized_sources  # Most common source


@pytest.mark.asyncio
async def test_refine_query_filters_low_relevance(learning_engine):
    """Test that query refinement filters out low-relevance patterns"""
    patterns = [
        MemoryEntry(
            memory_id="mem1",
            query="low relevance query",
            results={"answer": "test"},
            relevance_score=0.3,  # Low relevance
            api_sources=["api1"],
            similarity_score=0.9,
            timestamp=time.time()
        )
    ]
    
    result = await learning_engine.refine_query(
        original_query="test query",
        similar_patterns=patterns
    )
    
    # Should not use low-relevance patterns
    assert result.confidence == 0.5
    assert len(result.refinements) == 0


@pytest.mark.asyncio
async def test_adjust_confidence_threshold_high_fp_rate(learning_engine):
    """Test confidence threshold increases with high false positive rate"""
    # Create feedback with high false positive rate
    feedback = [
        FeedbackEntry(
            query_id=f"q{i}",
            confidence=0.8,  # High confidence
            relevance_score=0.3,  # But low relevance (false positive)
            timestamp=time.time()
        )
        for i in range(10)
    ]
    
    initial_threshold = learning_engine.confidence_threshold
    new_threshold = await learning_engine.adjust_confidence_threshold(feedback)
    
    # Threshold should increase to reduce false positives
    assert new_threshold > initial_threshold
    assert 0.3 <= new_threshold <= 0.9


@pytest.mark.asyncio
async def test_adjust_confidence_threshold_high_fn_rate(learning_engine):
    """Test confidence threshold decreases with high false negative rate"""
    # Create feedback with high false negative rate
    feedback = [
        FeedbackEntry(
            query_id=f"q{i}",
            confidence=0.3,  # Low confidence
            relevance_score=0.9,  # But high relevance (false negative)
            timestamp=time.time()
        )
        for i in range(10)
    ]
    
    initial_threshold = learning_engine.confidence_threshold
    new_threshold = await learning_engine.adjust_confidence_threshold(feedback)
    
    # Threshold should decrease to capture more results
    assert new_threshold < initial_threshold
    assert 0.3 <= new_threshold <= 0.9


@pytest.mark.asyncio
async def test_adjust_confidence_threshold_insufficient_data(learning_engine):
    """Test threshold doesn't change with insufficient feedback"""
    feedback = [
        FeedbackEntry(
            query_id="q1",
            confidence=0.5,
            relevance_score=0.5,
            timestamp=time.time()
        )
    ]  # Only 1 feedback entry
    
    initial_threshold = learning_engine.confidence_threshold
    new_threshold = await learning_engine.adjust_confidence_threshold(feedback)
    
    # Threshold should not change
    assert new_threshold == initial_threshold


@pytest.mark.asyncio
async def test_analyze_source_performance(learning_engine, mock_memory_store):
    """Test source performance analysis"""
    # Mock recent memories with different sources
    memories = [
        MemoryEntry(
            memory_id=f"mem{i}",
            query=f"query {i}",
            results={"answer": "test"},
            relevance_score=0.9 if i % 2 == 0 else 0.5,
            api_sources=["api1"] if i < 5 else ["api2"],
            similarity_score=0.8,
            timestamp=time.time()
        )
        for i in range(10)
    ]
    mock_memory_store.get_recent.return_value = memories
    
    metrics = await learning_engine.analyze_source_performance(lookback_queries=10)
    
    assert isinstance(metrics, dict)
    assert "api1" in metrics
    assert "api2" in metrics
    
    # api1 should have higher priority (more high-relevance results)
    assert metrics["api1"].priority_score > metrics["api2"].priority_score
    assert metrics["api1"].total_uses == 5
    assert metrics["api2"].total_uses == 5


@pytest.mark.asyncio
async def test_analyze_source_performance_empty(learning_engine, mock_memory_store):
    """Test source performance analysis with no memories"""
    mock_memory_store.get_recent.return_value = []
    
    metrics = await learning_engine.analyze_source_performance()
    
    assert isinstance(metrics, dict)
    assert len(metrics) == 0


@pytest.mark.asyncio
async def test_calculate_priority():
    """Test priority calculation for API sources"""
    engine = LearningEngine(
        memory_store=Mock(),
        mcp_client=Mock(),
        initial_confidence_threshold=0.5,
        learning_rate=0.1
    )
    
    # High success rate, high avg score, good usage
    stats_high = {
        "total": 10,
        "high_relevance": 8,
        "scores": [0.9] * 8 + [0.6] * 2
    }
    priority_high = engine._calculate_priority(stats_high)
    
    # Low success rate, low avg score
    stats_low = {
        "total": 10,
        "high_relevance": 2,
        "scores": [0.8] * 2 + [0.4] * 8
    }
    priority_low = engine._calculate_priority(stats_low)
    
    assert priority_high > priority_low
    assert 0.0 <= priority_high <= 1.0
    assert 0.0 <= priority_low <= 1.0


@pytest.mark.asyncio
async def test_extract_top_sources():
    """Test extraction of top-performing sources"""
    engine = LearningEngine(
        memory_store=Mock(),
        mcp_client=Mock(),
        initial_confidence_threshold=0.5,
        learning_rate=0.1
    )
    
    patterns = [
        MemoryEntry(
            memory_id="mem1",
            query="query 1",
            results={},
            relevance_score=0.9,
            api_sources=["api1", "api2"],
            similarity_score=0.8,
            timestamp=time.time()
        ),
        MemoryEntry(
            memory_id="mem2",
            query="query 2",
            results={},
            relevance_score=0.8,
            api_sources=["api1", "api3"],
            similarity_score=0.7,
            timestamp=time.time()
        ),
        MemoryEntry(
            memory_id="mem3",
            query="query 3",
            results={},
            relevance_score=0.7,
            api_sources=["api2"],
            similarity_score=0.6,
            timestamp=time.time()
        )
    ]
    
    top_sources = engine._extract_top_sources(patterns)
    
    assert isinstance(top_sources, list)
    assert len(top_sources) > 0
    # api1 should be first (highest total relevance)
    assert top_sources[0] == "api1"


@pytest.mark.asyncio
async def test_get_learning_metrics(learning_engine, mock_memory_store):
    """Test getting learning metrics"""
    # Mock source performance data
    memories = [
        MemoryEntry(
            memory_id=f"mem{i}",
            query=f"query {i}",
            results={},
            relevance_score=0.8,
            api_sources=["api1"],
            similarity_score=0.8,
            timestamp=time.time()
        )
        for i in range(5)
    ]
    mock_memory_store.get_recent.return_value = memories
    
    metrics = await learning_engine.get_learning_metrics()
    
    assert isinstance(metrics, dict)
    assert "confidence_threshold" in metrics
    assert "learning_rate" in metrics
    assert "sources_tracked" in metrics
    assert "avg_source_priority" in metrics
    assert "top_sources" in metrics
    
    assert metrics["confidence_threshold"] == 0.5
    assert metrics["learning_rate"] == 0.1


def test_confidence_threshold_clamping():
    """Test that confidence threshold is clamped to valid range"""
    # Test lower bound
    engine_low = LearningEngine(
        memory_store=Mock(),
        mcp_client=Mock(),
        initial_confidence_threshold=0.1,  # Too low
        learning_rate=0.1
    )
    assert engine_low.confidence_threshold >= 0.3
    
    # Test upper bound
    engine_high = LearningEngine(
        memory_store=Mock(),
        mcp_client=Mock(),
        initial_confidence_threshold=0.95,  # Too high
        learning_rate=0.1
    )
    assert engine_high.confidence_threshold <= 0.9


def test_learning_rate_clamping():
    """Test that learning rate is clamped to valid range"""
    # Test lower bound
    engine_low = LearningEngine(
        memory_store=Mock(),
        mcp_client=Mock(),
        initial_confidence_threshold=0.5,
        learning_rate=0.001  # Too low
    )
    assert engine_low.learning_rate >= 0.01
    
    # Test upper bound
    engine_high = LearningEngine(
        memory_store=Mock(),
        mcp_client=Mock(),
        initial_confidence_threshold=0.5,
        learning_rate=0.8  # Too high
    )
    assert engine_high.learning_rate <= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
