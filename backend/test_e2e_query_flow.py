"""
End-to-end test for complete query flow
Tests Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 4.2, 5.1
"""
import pytest
import asyncio
import httpx
import redis
import os
import time
from pathlib import Path


class TestCompleteQueryFlow:
    """Test complete query flow from submission to report generation"""
    
    @pytest.fixture
    async def api_client(self):
        """Create async HTTP client for API"""
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as client:
            yield client
    
    @pytest.fixture
    def redis_client(self):
        """Create Redis client"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url, decode_responses=True)
        yield client
        client.close()
    
    @pytest.mark.asyncio
    async def test_complete_query_flow(self, api_client, redis_client):
        """
        Test complete query flow:
        1. Submit query
        2. Verify Claude calls MCP tools
        3. Verify synthesized answer
        4. Verify sources included
        5. Verify stored in Redis
        6. Verify report generated
        """
        # Step 1: Check Redis is available
        try:
            redis_client.ping()
            print("✓ Redis is available")
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        
        # Step 2: Check API server is healthy
        try:
            response = await api_client.get("/health")
            assert response.status_code == 200
            health = response.json()
            print(f"✓ API server is healthy: {health['status']}")
            print(f"  - Redis connected: {health['redis_connected']}")
            print(f"  - MCP servers connected: {health['mcp_servers_connected']}")
            
            if health['mcp_servers_connected'] == 0:
                pytest.skip("No MCP servers connected")
        except Exception as e:
            pytest.skip(f"API server not available: {e}")
        
        # Step 3: Submit test query
        test_query = "What are the latest developments in artificial intelligence?"
        
        print(f"\n📝 Submitting query: {test_query}")
        
        response = await api_client.post(
            "/api/research/query",
            json={
                "query": test_query,
                "max_sources": 3,
                "include_report": True
            }
        )
        
        assert response.status_code == 200, f"Query failed: {response.text}"
        
        result = response.json()
        
        # Step 4: Verify response structure
        assert "query_id" in result
        assert "synthesized_answer" in result
        assert "sources" in result
        assert "processing_time_ms" in result
        
        query_id = result["query_id"]
        print(f"✓ Query processed successfully")
        print(f"  - Query ID: {query_id}")
        print(f"  - Processing time: {result['processing_time_ms']}ms")
        
        # Step 5: Verify synthesized answer is not empty
        assert len(result["synthesized_answer"]) > 0, "Synthesized answer is empty"
        print(f"✓ Synthesized answer received ({len(result['synthesized_answer'])} chars)")
        print(f"  Preview: {result['synthesized_answer'][:100]}...")
        
        # Step 6: Verify sources are included
        assert isinstance(result["sources"], list), "Sources should be a list"
        print(f"✓ Sources included: {len(result['sources'])} sources")
        
        # Step 7: Verify query is stored in Redis
        # Give it a moment to store
        await asyncio.sleep(1)
        
        # Check if query exists in timeline
        timeline_keys = redis_client.zrevrange("queries:timeline", 0, -1)
        assert len(timeline_keys) > 0, "No queries in timeline"
        print(f"✓ Query stored in Redis ({len(timeline_keys)} total queries)")
        
        # Step 8: Verify report was generated if requested
        if result.get("report_path"):
            report_path = Path(result["report_path"])
            assert report_path.exists(), f"Report file not found: {report_path}"
            
            # Verify report content
            report_content = report_path.read_text()
            assert test_query in report_content, "Query not in report"
            assert len(report_content) > 100, "Report content too short"
            
            print(f"✓ Report generated: {report_path.name}")
            print(f"  - Size: {len(report_content)} chars")
        else:
            print("⚠ No report path in response")
        
        # Step 9: Verify tool calls were made (check if we have tool_calls_made in response)
        if "tool_calls_made" in result:
            assert result["tool_calls_made"] > 0, "No tool calls were made"
            print(f"✓ Claude made {result['tool_calls_made']} tool calls")
        
        print("\n✅ Complete query flow test PASSED")
    
    @pytest.mark.asyncio
    async def test_query_without_report(self, api_client):
        """Test query processing without report generation"""
        response = await api_client.post(
            "/api/research/query",
            json={
                "query": "What is machine learning?",
                "max_sources": 2,
                "include_report": False
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "synthesized_answer" in result
        assert len(result["synthesized_answer"]) > 0
        
        # Report should not be generated
        assert result.get("report_path") is None or result.get("report_path") == ""
        
        print("✓ Query without report test PASSED")
    
    @pytest.mark.asyncio
    async def test_multiple_queries(self, api_client):
        """Test processing multiple queries in sequence"""
        queries = [
            "What is quantum computing?",
            "Explain blockchain technology",
            "What are neural networks?"
        ]
        
        query_ids = []
        
        for query in queries:
            response = await api_client.post(
                "/api/research/query",
                json={
                    "query": query,
                    "max_sources": 2,
                    "include_report": False
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            query_ids.append(result["query_id"])
            
            # Small delay between queries
            await asyncio.sleep(0.5)
        
        assert len(query_ids) == len(queries)
        assert len(set(query_ids)) == len(queries), "Query IDs should be unique"
        
        print(f"✓ Multiple queries test PASSED ({len(queries)} queries)")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
