"""
End-to-End Test for Research Query Flow (Mock Version)

This test validates the complete query processing pipeline using mocks
to avoid MCP connection issues during testing:
1. Submit test query via API
2. Verify APIs are discovered from Postman (mocked)
3. Verify multiple APIs are called (mocked)
4. Verify Claude synthesizes results (mocked)
5. Verify response includes sources and confidence
6. Verify query is stored in Redis memory

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2
"""
import pytest
import pytest_asyncio
import asyncio
import os
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Add backend to path
import sys
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from agent_orchestrator import (
    AgentOrchestrator, QueryIntent, ResearchSynthesis, 
    APIResult, ResearchResult
)
from mcp_client import MCPClient, APIEndpoint
from memory_store import MemoryStore, MemoryEntry


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client"""
    client = AsyncMock(spec=MCPClient)
    
    # Mock call_claude for intent parsing
    async def mock_call_claude(prompt, system="", temperature=0.7, max_tokens=4096):
        if "Analyze this research query" in prompt:
            # Intent parsing response
            return json.dumps({
                "intent_type": "trend_analysis",
                "key_topics": ["AI", "artificial intelligence", "trends"],
                "search_terms": ["AI trends", "machine learning", "AI developments"],
                "context": "User wants to know about AI trends"
            })
        elif "Synthesize research findings" in prompt:
            # Synthesis response
            return json.dumps({
                "summary": "AI is rapidly evolving with focus on LLMs and multimodal models.",
                "detailed_analysis": "The field of artificial intelligence is experiencing rapid growth. Large Language Models (LLMs) have become increasingly sophisticated, enabling more natural human-computer interactions. Multimodal AI systems that can process text, images, and audio are gaining traction. There is also growing emphasis on AI safety and responsible AI development.",
                "findings": [
                    "Large Language Models are becoming more capable and efficient",
                    "Multimodal AI systems are gaining widespread adoption",
                    "AI safety and ethics are receiving increased attention",
                    "Open-source AI models are democratizing access to AI technology"
                ],
                "confidence_assessment": {
                    "tech_api": 0.85,
                    "research_api": 0.80
                },
                "overall_confidence": 0.82
            })
        return "Mock response"
    
    client.call_claude = mock_call_claude
    
    # Mock discover_apis
    async def mock_discover_apis(query, verified_only=True, max_results=10):
        return [
            APIEndpoint(
                api_id="tech_api_1",
                api_name="Tech News API",
                endpoint="/v1/news",
                method="GET",
                description="Latest technology news",
                verified=True,
                priority_score=0.85
            ),
            APIEndpoint(
                api_id="research_api_1",
                api_name="Research Papers API",
                endpoint="/v1/papers",
                method="GET",
                description="Academic research papers",
                verified=True,
                priority_score=0.80
            ),
            APIEndpoint(
                api_id="trends_api_1",
                api_name="Trends API",
                endpoint="/v1/trends",
                method="GET",
                description="Technology trends",
                verified=True,
                priority_score=0.75
            )
        ]
    
    client.discover_apis = mock_discover_apis
    
    # Mock call_api
    async def mock_call_api(api_id, endpoint, method="GET", params=None, headers=None, body=None, timeout=30):
        # Simulate API responses
        if "tech" in api_id:
            return {
                "success": True,
                "articles": [
                    {"title": "AI Breakthrough in 2024", "summary": "New developments in AI"},
                    {"title": "LLMs Reach New Milestone", "summary": "Language models improve"}
                ],
                "status_code": 200
            }
        elif "research" in api_id:
            return {
                "success": True,
                "papers": [
                    {"title": "Advances in Neural Networks", "abstract": "Research on neural architectures"},
                    {"title": "Multimodal Learning", "abstract": "Combining vision and language"}
                ],
                "status_code": 200
            }
        elif "trends" in api_id:
            return {
                "success": True,
                "trends": [
                    {"topic": "Generative AI", "growth": "high"},
                    {"topic": "AI Safety", "growth": "medium"}
                ],
                "status_code": 200
            }
        return {"success": False, "error": "Unknown API", "status_code": 404}
    
    client.call_api = mock_call_api
    
    return client


@pytest.fixture
def test_redis_url():
    """Get Redis URL for testing"""
    return os.getenv("REDIS_URL", "redis://localhost:6379")


@pytest_asyncio.fixture
async def memory_store(test_redis_url):
    """Create memory store for testing"""
    try:
        store = MemoryStore(redis_url=test_redis_url)
        yield store
        store.close()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest_asyncio.fixture
async def agent_orchestrator(mock_mcp_client, memory_store):
    """Create agent orchestrator with mocked MCP client"""
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=memory_store
    )
    return orchestrator


@pytest.mark.asyncio
async def test_end_to_end_query_flow_mock(agent_orchestrator, memory_store):
    """
    Test complete end-to-end query flow with mocked MCP.
    
    This test validates all requirements without needing actual MCP connections:
    - 1.1: Parse intent and identify relevant API sources
    - 1.2: Query multiple API endpoints in parallel
    - 1.3: Use Claude to synthesize information
    - 1.4: Include source citations with confidence scores
    - 2.1: Store query in memory
    - 2.2: Store relevance scores
    """
    test_query = "What are the latest developments in artificial intelligence?"
    
    print(f"\n{'='*60}")
    print(f"Testing End-to-End Query Flow (Mock)")
    print(f"{'='*60}")
    print(f"Query: {test_query}")
    print(f"{'='*60}\n")
    
    # Step 1: Process query
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
    print(f"✓ Query ID: {result.query_id}")
    
    # Step 2: Verify intent was parsed
    print("\nStep 2: Verifying query intent parsing...")
    assert result.intent is not None, "Intent should be parsed"
    assert result.intent.intent_type == "trend_analysis", "Intent type should be trend_analysis"
    assert len(result.intent.key_topics) > 0, "Key topics should be extracted"
    assert len(result.intent.search_terms) > 0, "Search terms should be generated"
    
    print(f"✓ Intent Type: {result.intent.intent_type}")
    print(f"✓ Key Topics: {', '.join(result.intent.key_topics)}")
    print(f"✓ Search Terms: {', '.join(result.intent.search_terms)}")
    
    # Step 3: Verify APIs were discovered
    print("\nStep 3: Verifying API discovery...")
    assert len(result.api_results) > 0, "APIs should be discovered"
    print(f"✓ APIs discovered: {len(result.api_results)}")
    
    for api_result in result.api_results:
        status = "✓ Success" if api_result.success else "✗ Failed"
        print(f"  - {api_result.api_name}: {status}")
    
    # Step 4: Verify multiple APIs were called in parallel
    print("\nStep 4: Verifying parallel API execution...")
    assert len(result.api_results) >= 2, "Multiple APIs should be called"
    successful_apis = [r for r in result.api_results if r.success]
    assert len(successful_apis) >= 2, "At least 2 APIs should succeed"
    print(f"✓ Multiple APIs called: {len(result.api_results)} total, {len(successful_apis)} successful")
    
    # Step 5: Verify Claude synthesized results
    print("\nStep 5: Verifying Claude synthesis...")
    assert result.synthesis is not None, "Synthesis should be generated"
    assert result.synthesis.summary is not None, "Summary should be generated"
    assert len(result.synthesis.summary) > 0, "Summary should not be empty"
    assert 0.0 <= result.synthesis.confidence_score <= 1.0, "Confidence score should be valid"
    
    print(f"✓ Summary: {result.synthesis.summary[:100]}...")
    print(f"✓ Confidence Score: {result.synthesis.confidence_score:.2f}")
    print(f"✓ Findings: {len(result.synthesis.findings)} key findings")
    
    # Step 6: Verify response includes sources and confidence
    print("\nStep 6: Verifying sources and confidence scores...")
    assert len(result.synthesis.sources) > 0, "Sources should be included"
    assert len(result.synthesis.source_details) > 0, "Source details should be included"
    
    print(f"✓ Sources: {len(result.synthesis.sources)}")
    for source in result.synthesis.source_details:
        print(f"  - {source.api_name} (verified: {source.verified})")
    
    # Step 7: Verify query was stored in Redis memory
    print("\nStep 7: Verifying memory storage...")
    assert result.memory_id is not None, "Memory ID should be generated"
    
    # Retrieve the stored memory
    stored_memory = await memory_store.get_memory(result.memory_id)
    assert stored_memory is not None, "Memory should be retrievable"
    assert stored_memory.query == test_query, "Stored query should match"
    assert 0.0 <= stored_memory.relevance_score <= 1.0, "Relevance score should be valid"
    
    print(f"✓ Memory stored with ID: {result.memory_id}")
    print(f"✓ Stored query: {stored_memory.query[:50]}...")
    print(f"✓ Initial relevance score: {stored_memory.relevance_score:.2f}")
    
    # Step 8: Verify semantic search works
    print("\nStep 8: Verifying semantic search...")
    similar_embedding = await agent_orchestrator._get_embedding("Tell me about AI advancements")
    similar_memories = await memory_store.find_similar(
        query_embedding=similar_embedding,
        top_k=5,
        min_relevance=0.0
    )
    
    assert len(similar_memories) > 0, "Should find similar memories"
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
    
    print("✓ ALL END-TO-END TESTS PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])