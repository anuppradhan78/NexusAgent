"""
Tests for Agent Orchestrator

Basic tests to verify agent orchestrator functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from agent_orchestrator import (
    AgentOrchestrator,
    QueryIntent,
    APIResult,
    ResearchSynthesis,
    ResearchResult
)
from mcp_client import MCPClient, APIEndpoint
from memory_store import MemoryStore, MemoryEntry


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client"""
    client = Mock(spec=MCPClient)
    client.call_claude = AsyncMock()
    client.discover_apis = AsyncMock()
    client.call_api = AsyncMock()
    return client


@pytest.fixture
def mock_memory_store():
    """Create a mock memory store"""
    store = Mock(spec=MemoryStore)
    store.find_similar = AsyncMock(return_value=[])
    store.store = AsyncMock(return_value="memory_123")
    return store


@pytest.fixture
def orchestrator(mock_mcp_client, mock_memory_store):
    """Create agent orchestrator with mocks"""
    return AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store
    )


@pytest.mark.asyncio
async def test_parse_intent_success(orchestrator, mock_mcp_client):
    """Test successful intent parsing"""
    # Mock Claude response
    mock_mcp_client.call_claude.return_value = '''
    {
        "intent_type": "factual",
        "key_topics": ["AI", "trends", "2024"],
        "search_terms": ["AI trends", "artificial intelligence 2024"],
        "context": "User wants to know about AI trends"
    }
    '''
    
    intent = await orchestrator._parse_intent("What are the latest AI trends?")
    
    assert intent.intent_type == "factual"
    assert len(intent.key_topics) == 3
    assert "AI" in intent.key_topics
    assert len(intent.search_terms) == 2


@pytest.mark.asyncio
async def test_parse_intent_fallback(orchestrator, mock_mcp_client):
    """Test intent parsing fallback on error"""
    # Mock Claude to return invalid JSON
    mock_mcp_client.call_claude.return_value = "Invalid JSON response"
    
    intent = await orchestrator._parse_intent("Test query")
    
    # Should fallback to basic intent
    assert intent.intent_type == "general"
    assert intent.original_query == "Test query"
    assert "Test query" in intent.search_terms


@pytest.mark.asyncio
async def test_get_embedding(orchestrator):
    """Test embedding generation"""
    embedding = await orchestrator._get_embedding("Test text")
    
    assert len(embedding) == 1024
    assert all(isinstance(x, float) for x in embedding)
    assert all(-1.0 <= x <= 1.0 for x in embedding)
    
    # Same text should produce same embedding
    embedding2 = await orchestrator._get_embedding("Test text")
    assert embedding == embedding2


@pytest.mark.asyncio
async def test_discover_apis(orchestrator, mock_mcp_client):
    """Test API discovery"""
    # Mock API discovery
    mock_apis = [
        APIEndpoint(
            api_id="api1",
            api_name="Test API 1",
            endpoint="/test1",
            method="GET",
            description="Test API",
            verified=True,
            priority_score=0.8
        ),
        APIEndpoint(
            api_id="api2",
            api_name="Test API 2",
            endpoint="/test2",
            method="GET",
            description="Test API",
            verified=True,
            priority_score=0.6
        )
    ]
    mock_mcp_client.discover_apis.return_value = mock_apis
    
    intent = QueryIntent(
        original_query="test",
        intent_type="factual",
        key_topics=["test"],
        search_terms=["test query"],
        context="test"
    )
    
    apis = await orchestrator._discover_apis(intent, max_sources=5)
    
    assert len(apis) == 2
    assert apis[0].priority_score >= apis[1].priority_score  # Sorted by priority


@pytest.mark.asyncio
async def test_gather_information_parallel(orchestrator, mock_mcp_client):
    """Test parallel API information gathering"""
    # Mock API calls
    mock_mcp_client.call_api.return_value = {
        "success": True,
        "data": {"result": "test data"}
    }
    
    api_sources = [
        APIEndpoint(
            api_id=f"api{i}",
            api_name=f"Test API {i}",
            endpoint=f"/test{i}",
            method="GET",
            description="Test",
            verified=True,
            priority_score=0.5
        )
        for i in range(3)
    ]
    
    intent = QueryIntent(
        original_query="test",
        intent_type="factual",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    )
    
    results = await orchestrator._gather_information(api_sources, intent, timeout=10)
    
    assert len(results) == 3
    assert all(r.success for r in results)
    assert mock_mcp_client.call_api.call_count == 3


@pytest.mark.asyncio
async def test_gather_information_handles_failures(orchestrator, mock_mcp_client):
    """Test that API failures are handled gracefully"""
    # Mock one success and one failure
    call_count = 0
    
    async def mock_call_api(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"success": True, "data": {"result": "success"}}
        else:
            return {"success": False, "error": "API failed"}
    
    mock_mcp_client.call_api = mock_call_api
    
    api_sources = [
        APIEndpoint(
            api_id=f"api{i}",
            api_name=f"Test API {i}",
            endpoint=f"/test{i}",
            method="GET",
            description="Test",
            verified=True,
            priority_score=0.5
        )
        for i in range(2)
    ]
    
    intent = QueryIntent(
        original_query="test",
        intent_type="factual",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    )
    
    results = await orchestrator._gather_information(api_sources, intent, timeout=10)
    
    assert len(results) == 2
    assert results[0].success is True
    assert results[1].success is False


@pytest.mark.asyncio
async def test_synthesize_results(orchestrator, mock_mcp_client):
    """Test result synthesis"""
    # Mock Claude synthesis response
    mock_mcp_client.call_claude.return_value = '''
    {
        "summary": "Test summary of findings",
        "detailed_analysis": "Detailed analysis paragraph",
        "findings": ["Finding 1", "Finding 2", "Finding 3"],
        "confidence_assessment": {"api1": 0.8, "api2": 0.7},
        "overall_confidence": 0.75
    }
    '''
    
    api_results = [
        APIResult(
            api_id="api1",
            api_name="Test API 1",
            endpoint="/test1",
            data={"result": "data1"},
            success=True,
            response_time_ms=100
        ),
        APIResult(
            api_id="api2",
            api_name="Test API 2",
            endpoint="/test2",
            data={"result": "data2"},
            success=True,
            response_time_ms=150
        )
    ]
    
    intent = QueryIntent(
        original_query="test query",
        intent_type="factual",
        key_topics=["test"],
        search_terms=["test"],
        context="test context"
    )
    
    synthesis = await orchestrator._synthesize_results(
        query="test query",
        intent=intent,
        api_results=api_results,
        similar_queries=[]
    )
    
    assert synthesis.summary == "Test summary of findings"
    assert len(synthesis.findings) == 3
    assert synthesis.confidence_score == 0.75
    assert len(synthesis.sources) == 2


@pytest.mark.asyncio
async def test_synthesize_results_fallback(orchestrator, mock_mcp_client):
    """Test synthesis fallback when Claude fails"""
    # Mock Claude to return invalid JSON
    mock_mcp_client.call_claude.return_value = "Invalid JSON"
    
    api_results = [
        APIResult(
            api_id="api1",
            api_name="Test API",
            endpoint="/test",
            data={"result": "data"},
            success=True,
            response_time_ms=100
        )
    ]
    
    intent = QueryIntent(
        original_query="test",
        intent_type="factual",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    )
    
    synthesis = await orchestrator._synthesize_results(
        query="test",
        intent=intent,
        api_results=api_results,
        similar_queries=[]
    )
    
    # Should create fallback synthesis
    assert synthesis.confidence_score < 0.5
    assert len(synthesis.sources) == 1


@pytest.mark.asyncio
async def test_process_query_end_to_end(orchestrator, mock_mcp_client, mock_memory_store):
    """Test complete query processing pipeline"""
    # Mock all dependencies
    mock_mcp_client.call_claude.side_effect = [
        # Intent parsing
        '''{"intent_type": "factual", "key_topics": ["test"], "search_terms": ["test"], "context": "test"}''',
        # Synthesis
        '''{"summary": "Test summary", "detailed_analysis": "Analysis", "findings": ["Finding 1"], "confidence_assessment": {"api1": 0.8}, "overall_confidence": 0.8}'''
    ]
    
    mock_mcp_client.discover_apis.return_value = [
        APIEndpoint(
            api_id="api1",
            api_name="Test API",
            endpoint="/test",
            method="GET",
            description="Test",
            verified=True,
            priority_score=0.8
        )
    ]
    
    mock_mcp_client.call_api.return_value = {
        "success": True,
        "data": {"result": "test data"}
    }
    
    mock_memory_store.find_similar.return_value = []
    mock_memory_store.store.return_value = "memory_123"
    
    # Process query
    result = await orchestrator.process_query(
        query="What is AI?",
        max_sources=5,
        timeout=30
    )
    
    assert result.query == "What is AI?"
    assert result.synthesis.confidence_score == 0.8
    assert len(result.api_results) == 1
    assert result.memory_id == "memory_123"
    assert result.processing_time_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
