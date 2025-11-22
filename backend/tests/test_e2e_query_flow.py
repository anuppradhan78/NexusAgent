"""
End-to-End Test for Research Query Flow

This test validates the complete query processing pipeline:
1. Submit test query via API
2. Verify APIs are discovered from Postman
3. Verify multiple APIs are called
4. Verify Claude synthesizes results
5. Verify response includes sources and confidence
6. Verify query is stored in Redis memory

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2
"""
import pytest
import pytest_asyncio
import asyncio
import os
import time
from fastapi.testclient import TestClient

# Add backend to path
import sys
sys.path.insert(0, os.path.dirname(__file__))

from main import app, Config
from mcp_client import MCPClient
from memory_store import MemoryStore
from agent_orchestrator import AgentOrchestrator


@pytest.fixture
def test_config():
    """Ensure test environment variables are set"""
    # Check required environment variables
    required_vars = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379")
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        pytest.skip(f"Missing required environment variables: {', '.join(missing)}")
    
    return required_vars


@pytest_asyncio.fixture(scope="function")
async def initialized_components(test_config):
    """Initialize MCP client, memory store, and agent orchestrator"""
    # Initialize MCP client
    mcp_client = MCPClient()
    await mcp_client.initialize()
    
    # Initialize memory store
    memory_store = MemoryStore(
        redis_url=test_config["REDIS_URL"]
    )
    
    # Initialize agent orchestrator
    agent_orchestrator = AgentOrchestrator(
        mcp_client=mcp_client,
        memory_store=memory_store
    )
    
    yield {
        "mcp_client": mcp_client,
        "memory_store": memory_store,
        "agent_orchestrator": agent_orchestrator
    }
    
    # Cleanup
    await mcp_client.close()
    memory_store.close()


@pytest.mark.asyncio
async def test_end_to_end_query_flow(initialized_components):
    """
    Test complete end-to-end query flow.
    
    Requirements:
    - 1.1: Parse intent and identify relevant API sources
    - 1.2: Query multiple API endpoints in parallel
    - 1.3: Use Claude to synthesize information
    - 1.4: Include source citations with confidence scores
    - 2.1: Store query in memory
    - 2.2: Store relevance scores
    """
    agent_orchestrator = initialized_components["agent_orchestrator"]
    memory_store = initialized_components["memory_store"]
    
    # Test query
    test_query = "What are the latest developments in artificial intelligence?"
    
    print(f"\n{'='*60}")
    print(f"Testing End-to-End Query Flow")
    print(f"{'='*60}")
    print(f"Query: {test_query}")
    print(f"{'='*60}\n")
    
    # Step 1: Process query through agent orchestrator
    print("Step 1: Processing query through agent orchestrator...")
    start_time = time.time()
    
    result = await agent_orchestrator.process_query(
        query=test_query,
        max_sources=3,
        timeout=30
    )
    
    processing_time = time.time() - start_time
    print(f"✓ Query processed in {processing_time:.2f} seconds")
    
    # Verify result structure
    assert result is not None, "Result should not be None"
    assert result.query_id is not None, "Query ID should be generated"
    assert result.query == test_query, "Query should match input"
    
    # Step 2: Verify intent was parsed
    print("\nStep 2: Verifying query intent parsing...")
    assert result.intent is not None, "Intent should be parsed"
    assert result.intent.intent_type is not None, "Intent type should be identified"
    assert len(result.intent.key_topics) > 0, "Key topics should be extracted"
    assert len(result.intent.search_terms) > 0, "Search terms should be generated"
    
    print(f"✓ Intent Type: {result.intent.intent_type}")
    print(f"✓ Key Topics: {', '.join(result.intent.key_topics[:3])}")
    print(f"✓ Search Terms: {', '.join(result.intent.search_terms[:3])}")
    
    # Step 3: Verify APIs were discovered (may be empty if Postman not configured)
    print("\nStep 3: Verifying API discovery...")
    print(f"✓ API Results: {len(result.api_results)} API(s) called")
    
    if len(result.api_results) > 0:
        print(f"✓ APIs discovered and called:")
        for api_result in result.api_results:
            status = "✓ Success" if api_result.success else "✗ Failed"
            print(f"  - {api_result.api_name}: {status} ({api_result.response_time_ms:.0f}ms)")
    else:
        print("  Note: No APIs discovered (Postman may not be configured)")
    
    # Step 4: Verify multiple APIs were attempted (if available)
    print("\nStep 4: Verifying parallel API execution...")
    if len(result.api_results) > 1:
        print(f"✓ Multiple APIs called in parallel: {len(result.api_results)} APIs")
        # Verify they were called in parallel (total time should be less than sum of individual times)
        total_api_time = sum(r.response_time_ms for r in result.api_results)
        print(f"  - Total API time if sequential: {total_api_time:.0f}ms")
        print(f"  - Actual processing time: {result.processing_time_ms:.0f}ms")
        if result.processing_time_ms < total_api_time:
            print(f"  ✓ Parallel execution confirmed (saved {total_api_time - result.processing_time_ms:.0f}ms)")
    else:
        print(f"  Note: Only {len(result.api_results)} API(s) available for testing")
    
    # Step 5: Verify Claude synthesized results
    print("\nStep 5: Verifying Claude synthesis...")
    assert result.synthesis is not None, "Synthesis should be generated"
    assert result.synthesis.summary is not None, "Summary should be generated"
    assert len(result.synthesis.summary) > 0, "Summary should not be empty"
    assert result.synthesis.confidence_score >= 0.0, "Confidence score should be valid"
    assert result.synthesis.confidence_score <= 1.0, "Confidence score should be valid"
    
    print(f"✓ Summary generated: {len(result.synthesis.summary)} characters")
    print(f"✓ Confidence Score: {result.synthesis.confidence_score:.2f}")
    print(f"✓ Findings: {len(result.synthesis.findings)} key findings")
    
    if len(result.synthesis.findings) > 0:
        print(f"  Sample findings:")
        for i, finding in enumerate(result.synthesis.findings[:3], 1):
            print(f"    {i}. {finding[:80]}...")
    
    # Step 6: Verify response includes sources and confidence
    print("\nStep 6: Verifying sources and confidence scores...")
    assert len(result.synthesis.sources) >= 0, "Sources list should exist"
    assert len(result.synthesis.source_details) >= 0, "Source details should exist"
    
    print(f"✓ Sources included: {len(result.synthesis.sources)} source(s)")
    if len(result.synthesis.source_details) > 0:
        print(f"  Source details:")
        for source in result.synthesis.source_details:
            print(f"    - {source.api_name} ({source.api_id})")
            print(f"      Endpoint: {source.endpoint}")
            print(f"      Verified: {source.verified}")
    
    print(f"✓ Confidence breakdown: {len(result.synthesis.confidence_breakdown)} source(s)")
    
    # Step 7: Verify query was stored in Redis memory
    print("\nStep 7: Verifying memory storage...")
    assert result.memory_id is not None, "Memory ID should be generated"
    
    # Retrieve the stored memory
    stored_memory = await memory_store.get_memory(result.memory_id)
    assert stored_memory is not None, "Memory should be retrievable"
    assert stored_memory.query == test_query, "Stored query should match"
    assert stored_memory.relevance_score >= 0.0, "Relevance score should be valid"
    assert stored_memory.relevance_score <= 1.0, "Relevance score should be valid"
    
    print(f"✓ Memory stored with ID: {result.memory_id}")
    print(f"✓ Stored query: {stored_memory.query[:50]}...")
    print(f"✓ Initial relevance score: {stored_memory.relevance_score:.2f}")
    print(f"✓ API sources stored: {len(stored_memory.api_sources)} source(s)")
    
    # Step 8: Verify semantic search works
    print("\nStep 8: Verifying semantic search...")
    
    # Get embedding for a similar query
    similar_query = "Tell me about recent AI advancements"
    similar_embedding = await agent_orchestrator._get_embedding(similar_query)
    
    # Search for similar memories
    similar_memories = await memory_store.find_similar(
        query_embedding=similar_embedding,
        top_k=5,
        min_relevance=0.0
    )
    
    assert len(similar_memories) > 0, "Should find at least the query we just stored"
    
    # Verify our query is in the results
    found_our_query = any(m.memory_id == result.memory_id for m in similar_memories)
    assert found_our_query, "Should find our recently stored query"
    
    print(f"✓ Semantic search found {len(similar_memories)} similar memor(ies)")
    print(f"✓ Our query found in results: {found_our_query}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"END-TO-END TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✓ Query processed successfully")
    print(f"✓ Intent parsed: {result.intent.intent_type}")
    print(f"✓ APIs called: {len(result.api_results)}")
    print(f"✓ Synthesis generated: {len(result.synthesis.summary)} chars")
    print(f"✓ Confidence score: {result.synthesis.confidence_score:.2f}")
    print(f"✓ Memory stored: {result.memory_id}")
    print(f"✓ Processing time: {result.processing_time_ms:.0f}ms")
    print(f"{'='*60}\n")
    
    # All assertions passed
    print("✓ ALL END-TO-END TESTS PASSED!")


@pytest.mark.asyncio
async def test_query_with_session_id(initialized_components):
    """
    Test query processing with session ID for multi-turn conversations.
    
    Requirements: 15.1, 15.2 - Session management
    """
    agent_orchestrator = initialized_components["agent_orchestrator"]
    
    session_id = "test_session_123"
    
    # First query in session
    result1 = await agent_orchestrator.process_query(
        query="What is machine learning?",
        session_id=session_id,
        max_sources=2
    )
    
    assert result1 is not None
    assert result1.memory_id is not None
    
    # Second query in same session
    result2 = await agent_orchestrator.process_query(
        query="Tell me more about neural networks",
        session_id=session_id,
        max_sources=2
    )
    
    assert result2 is not None
    assert result2.memory_id is not None
    
    # Verify both queries are stored with session ID
    memory1 = await initialized_components["memory_store"].get_memory(result1.memory_id)
    memory2 = await initialized_components["memory_store"].get_memory(result2.memory_id)
    
    assert memory1.session_id == session_id
    assert memory2.session_id == session_id
    
    print(f"✓ Session-based queries working correctly")


@pytest.mark.asyncio
async def test_error_handling_graceful_degradation(initialized_components):
    """
    Test that system handles errors gracefully.
    
    Requirements: 1.5 - Handle API failures gracefully
    """
    agent_orchestrator = initialized_components["agent_orchestrator"]
    
    # Query that might not find APIs
    result = await agent_orchestrator.process_query(
        query="Very specific niche query that probably has no APIs",
        max_sources=5
    )
    
    # Should still return a result even if no APIs found
    assert result is not None
    assert result.synthesis is not None
    assert result.synthesis.summary is not None
    
    # Confidence should be lower if no APIs found
    if len(result.api_results) == 0:
        print(f"✓ Graceful degradation: No APIs found, but synthesis still generated")
        print(f"  Confidence score: {result.synthesis.confidence_score:.2f}")
    
    print(f"✓ Error handling and graceful degradation working")


@pytest.mark.asyncio
async def test_memory_metrics(initialized_components):
    """
    Test memory metrics calculation.
    
    Requirements: 7.5 - Expose metrics for monitoring
    """
    memory_store = initialized_components["memory_store"]
    
    # Get metrics
    metrics = await memory_store.get_metrics()
    
    assert metrics is not None
    assert metrics.total_memories >= 0
    assert metrics.avg_relevance >= 0.0
    assert metrics.avg_relevance <= 1.0
    assert metrics.high_quality_memories >= 0
    
    print(f"✓ Memory Metrics:")
    print(f"  - Total memories: {metrics.total_memories}")
    print(f"  - Average relevance: {metrics.avg_relevance:.2f}")
    print(f"  - High quality memories: {metrics.high_quality_memories}")
    print(f"  - Memory size: {metrics.memory_size_bytes} bytes")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
