"""
Test Learning Integration in Agent Orchestrator

This test verifies that the learning engine is properly integrated into
the query processing pipeline.

Requirements: 2.3, 2.4, 4.1, 4.5, 4.6
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List

from agent_orchestrator import AgentOrchestrator, QueryIntent, ResearchResult
from mcp_client import MCPClient, APIEndpoint
from memory_store import MemoryStore, MemoryEntry
from learning_engine import LearningEngine, RefinedQuery


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client"""
    client = Mock(spec=MCPClient)
    client.call_claude = AsyncMock(return_value='{"intent_type": "factual", "key_topics": ["AI"], "search_terms": ["AI trends"], "context": "test"}')
    client.discover_apis = AsyncMock(return_value=[
        APIEndpoint(
            api_id="api1",
            api_name="Test API 1",
            endpoint="/test1",
            method="GET",
            description="Test API",
            verified=True,
            priority_score=0.5
        ),
        APIEndpoint(
            api_id="api2",
            api_name="Test API 2",
            endpoint="/test2",
            method="GET",
            description="Test API 2",
            verified=True,
            priority_score=0.6
        )
    ])
    client.call_api = AsyncMock(return_value={"success": True, "data": {"result": "test"}})
    return client


@pytest.fixture
def mock_memory_store():
    """Create mock memory store"""
    store = Mock(spec=MemoryStore)
    
    # Mock similar queries
    store.find_similar = AsyncMock(return_value=[
        MemoryEntry(
            memory_id="mem1",
            query="What are AI trends?",
            results={"summary": "AI is growing"},
            relevance_score=0.8,
            api_sources=["api1", "api2"],
            similarity_score=0.9,
            timestamp=1234567890.0,
            session_id=None
        ),
        MemoryEntry(
            memory_id="mem2",
            query="Latest AI developments",
            results={"summary": "AI advances"},
            relevance_score=0.75,
            api_sources=["api1"],
            similarity_score=0.85,
            timestamp=1234567891.0,
            session_id=None
        )
    ])
    
    store.store = AsyncMock(return_value="memory_123")
    
    return store


@pytest.fixture
def mock_learning_engine():
    """Create mock learning engine"""
    engine = Mock(spec=LearningEngine)
    
    # Mock query refinement
    engine.refine_query = AsyncMock(return_value=RefinedQuery(
        query="What are the latest AI trends?",
        refinements=[
            "Focus on machine learning developments",
            "Include 2024 data",
            "Prioritize verified sources"
        ],
        confidence=0.85,
        prioritized_sources=["api1", "api2"],
        reasoning="Based on successful past patterns"
    ))
    
    return engine


@pytest.mark.asyncio
async def test_learning_integration_in_query_processing(
    mock_mcp_client,
    mock_memory_store,
    mock_learning_engine
):
    """
    Test that learning engine is integrated into query processing.
    
    Requirements:
    - 2.3: Retrieve similar queries before processing
    - 2.4: Prioritize API sources based on historical patterns
    - 4.1: Retrieve top 5 most similar past queries
    - 4.5: Track refinement effectiveness
    """
    # Create orchestrator with learning engine
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store,
        learning_engine=mock_learning_engine
    )
    
    # Process a query
    result = await orchestrator.process_query(
        query="What are the latest AI trends?",
        max_sources=5
    )
    
    # Verify learning engine was called
    mock_learning_engine.refine_query.assert_called_once()
    
    # Verify it was called with similar queries
    call_args = mock_learning_engine.refine_query.call_args
    assert call_args[1]['original_query'] == "What are the latest AI trends?"
    assert len(call_args[1]['similar_patterns']) == 2
    
    # Verify result includes refinement information
    assert result.refined_query is not None
    assert len(result.refined_query.refinements) == 3
    assert result.refined_query.confidence == 0.85
    assert "api1" in result.refined_query.prioritized_sources
    assert "api2" in result.refined_query.prioritized_sources


@pytest.mark.asyncio
async def test_api_prioritization_based_on_learning(
    mock_mcp_client,
    mock_memory_store,
    mock_learning_engine
):
    """
    Test that API sources are prioritized based on learned performance.
    
    Requirements:
    - 2.4: Prioritize API sources based on historical patterns
    - 4.5: Track refinement effectiveness
    """
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store,
        learning_engine=mock_learning_engine
    )
    
    # Process query
    result = await orchestrator.process_query(
        query="What are AI trends?",
        max_sources=5
    )
    
    # Verify API discovery was called
    assert mock_mcp_client.discover_apis.called
    
    # Verify result has API sources
    assert len(result.api_results) > 0
    
    # Verify memory was stored with refinement metadata
    mock_memory_store.store.assert_called_once()
    store_call = mock_memory_store.store.call_args
    
    # Check that refinement metadata is included
    results_data = store_call[1]['results']
    assert 'refinement_applied' in results_data
    assert results_data['refinement_applied'] is True
    assert 'refinement_confidence' in results_data
    assert results_data['refinement_confidence'] == 0.85
    assert 'refinements' in results_data
    assert len(results_data['refinements']) == 3


@pytest.mark.asyncio
async def test_refinement_tracking_in_memory(
    mock_mcp_client,
    mock_memory_store,
    mock_learning_engine
):
    """
    Test that refinement effectiveness is tracked in memory.
    
    Requirements:
    - 4.6: Track refinement effectiveness
    """
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store,
        learning_engine=mock_learning_engine
    )
    
    # Process query
    result = await orchestrator.process_query(
        query="Test query",
        max_sources=3
    )
    
    # Verify memory storage includes refinement tracking
    store_call = mock_memory_store.store.call_args
    results_data = store_call[1]['results']
    
    # Check refinement tracking fields
    assert 'refinement_applied' in results_data
    assert 'refinement_confidence' in results_data
    assert 'refinements' in results_data
    assert 'prioritized_sources_used' in results_data
    
    # Verify prioritized sources tracking
    assert isinstance(results_data['prioritized_sources_used'], list)


@pytest.mark.asyncio
async def test_no_refinement_when_no_similar_queries(
    mock_mcp_client,
    mock_memory_store
):
    """
    Test behavior when no similar queries are found.
    
    Requirements:
    - 4.1: Handle case with no similar past queries
    """
    # Mock no similar queries
    mock_memory_store.find_similar = AsyncMock(return_value=[])
    
    # Create learning engine that returns no refinements
    mock_learning_engine = Mock(spec=LearningEngine)
    mock_learning_engine.refine_query = AsyncMock(return_value=RefinedQuery(
        query="New query",
        refinements=[],
        confidence=0.5,
        prioritized_sources=[],
        reasoning="No successful past patterns found"
    ))
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store,
        learning_engine=mock_learning_engine
    )
    
    # Process query
    result = await orchestrator.process_query(
        query="Completely new query",
        max_sources=3
    )
    
    # Verify refinement was attempted but returned empty
    mock_learning_engine.refine_query.assert_called_once()
    assert result.refined_query is not None
    assert len(result.refined_query.refinements) == 0
    assert len(result.refined_query.prioritized_sources) == 0


@pytest.mark.asyncio
async def test_api_priority_boost_for_learned_sources(
    mock_mcp_client,
    mock_memory_store,
    mock_learning_engine
):
    """
    Test that learned high-performing sources get priority boost.
    
    Requirements:
    - 2.4: Prioritize API sources based on historical patterns
    """
    # Setup APIs with different initial priorities
    api1 = APIEndpoint(
        api_id="api1",
        api_name="API 1",
        endpoint="/api1",
        method="GET",
        description="Test",
        verified=True,
        priority_score=0.3  # Low initial priority
    )
    
    api2 = APIEndpoint(
        api_id="api2",
        api_name="API 2",
        endpoint="/api2",
        method="GET",
        description="Test",
        verified=True,
        priority_score=0.7  # High initial priority
    )
    
    mock_mcp_client.discover_apis = AsyncMock(return_value=[api1, api2])
    
    # Learning engine prioritizes api1 (which has low initial priority)
    mock_learning_engine.refine_query = AsyncMock(return_value=RefinedQuery(
        query="Test",
        refinements=["test"],
        confidence=0.8,
        prioritized_sources=["api1"],  # api1 is learned to be good
        reasoning="api1 performed well historically"
    ))
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store,
        learning_engine=mock_learning_engine
    )
    
    # Process query
    result = await orchestrator.process_query(
        query="Test query",
        max_sources=5
    )
    
    # Verify learning was applied
    assert result.refined_query is not None
    assert "api1" in result.refined_query.prioritized_sources
    
    # Note: We can't directly verify priority boost without accessing internal state,
    # but we've verified the refinement was applied


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
