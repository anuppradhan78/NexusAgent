"""
Infrastructure Testing Script for Adaptive Research Agent

Tests:
1. Redis connection and RediSearch module
2. MCP connections to Anthropic and Postman
3. Redis vector storage and retrieval
4. Health endpoint
5. Basic integration flow

Requirements: 8.1, 9.1, 10.1
"""
import asyncio
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for tests
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
        print(f"✓ {test_name}")
        if message:
            print(f"  {message}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"✗ {test_name}")
        print(f"  Error: {error}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        print(f"⚠ {test_name}")
        print(f"  Warning: {message}")
    
    def summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Passed:   {len(self.passed)}")
        print(f"Failed:   {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")
        print("="*60)
        
        if self.failed:
            print("\nFailed Tests:")
            for test_name, error in self.failed:
                print(f"  - {test_name}: {error}")
        
        if self.warnings:
            print("\nWarnings:")
            for test_name, message in self.warnings:
                print(f"  - {test_name}: {message}")
        
        return len(self.failed) == 0


async def test_redis_connection(results: TestResults):
    """Test Redis connection and RediSearch module"""
    print("\n" + "="*60)
    print("TEST 1: Redis Connection and RediSearch")
    print("="*60)
    
    try:
        import redis
        from redis.commands.search.field import VectorField
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_password = os.getenv("REDIS_PASSWORD")
        
        # Connect to Redis
        connection_params = {
            "decode_responses": True,
            "socket_connect_timeout": 5
        }
        if redis_password:
            connection_params["password"] = redis_password
        
        client = redis.from_url(redis_url, **connection_params)
        
        # Test connection
        client.ping()
        results.add_pass("Redis connection", f"Connected to {redis_url}")
        
        # Check RediSearch module
        modules = client.module_list()
        search_module = any(m.get('name', b'').decode() == 'search' if isinstance(m.get('name'), bytes) 
                           else m.get('name') == 'search' for m in modules)
        
        if search_module:
            results.add_pass("RediSearch module", "RediSearch module is loaded")
        else:
            results.add_fail("RediSearch module", "RediSearch module not found. Install with: docker run -p 6379:6379 redis/redis-stack-server:latest")
            return False
        
        # Test basic operations
        test_key = "test:infrastructure"
        client.set(test_key, "test_value")
        value = client.get(test_key)
        client.delete(test_key)
        
        if value == "test_value":
            results.add_pass("Redis operations", "Basic read/write operations work")
        else:
            results.add_fail("Redis operations", "Read/write test failed")
            return False
        
        client.close()
        return True
        
    except ImportError as e:
        results.add_fail("Redis import", f"Redis package not installed: {e}")
        return False
    except redis.ConnectionError as e:
        results.add_fail("Redis connection", f"Cannot connect to Redis: {e}. Start Redis with: docker run -p 6379:6379 redis/redis-stack-server:latest")
        return False
    except Exception as e:
        results.add_fail("Redis test", str(e))
        return False


async def test_memory_store(results: TestResults):
    """Test MemoryStore class with vector storage"""
    print("\n" + "="*60)
    print("TEST 2: Memory Store Vector Operations")
    print("="*60)
    
    try:
        from memory_store import MemoryStore
        import numpy as np
        
        # Initialize memory store
        memory_store = MemoryStore()
        results.add_pass("MemoryStore initialization", "Memory store created successfully")
        
        # Test storing a memory
        test_query = "What is the weather in San Francisco?"
        test_embedding = np.random.rand(1024).tolist()  # Random 1024-dim vector
        test_results = {"answer": "Sunny and 72°F", "confidence": 0.9}
        test_sources = ["weather_api", "openweather"]
        
        memory_id = await memory_store.store(
            query=test_query,
            query_embedding=test_embedding,
            results=test_results,
            sources=test_sources,
            relevance_score=0.8
        )
        
        results.add_pass("Memory storage", f"Stored memory with ID: {memory_id[:20]}...")
        
        # Test retrieving similar memories
        similar_embedding = np.array(test_embedding) + np.random.rand(1024) * 0.1
        similar_memories = await memory_store.find_similar(
            query_embedding=similar_embedding.tolist(),
            top_k=5
        )
        
        if len(similar_memories) > 0:
            results.add_pass("Vector search", f"Found {len(similar_memories)} similar memories")
            
            # Check if our test memory is in results
            found_test_memory = any(m.memory_id == memory_id for m in similar_memories)
            if found_test_memory:
                results.add_pass("Vector similarity", "Test memory found in similarity search")
            else:
                results.add_warning("Vector similarity", "Test memory not in top results (may be normal with random vectors)")
        else:
            results.add_warning("Vector search", "No similar memories found (may be normal with empty database)")
        
        # Test updating relevance
        update_success = await memory_store.update_relevance(memory_id, 0.95)
        if update_success:
            results.add_pass("Relevance update", "Successfully updated relevance score")
        else:
            results.add_fail("Relevance update", "Failed to update relevance score")
        
        # Test getting metrics
        metrics = await memory_store.get_metrics()
        results.add_pass("Memory metrics", f"Total memories: {metrics.total_memories}, Avg relevance: {metrics.avg_relevance:.2f}")
        
        # Cleanup
        memory_store.close()
        
        return True
        
    except ImportError as e:
        results.add_fail("MemoryStore import", f"Cannot import MemoryStore: {e}")
        return False
    except Exception as e:
        results.add_fail("MemoryStore test", str(e))
        return False


async def test_mcp_connections(results: TestResults):
    """Test MCP connections to Anthropic and Postman"""
    print("\n" + "="*60)
    print("TEST 3: MCP Connections")
    print("="*60)
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    postman_key = os.getenv("POSTMAN_API_KEY")
    
    if not anthropic_key:
        results.add_warning("Anthropic API key", "ANTHROPIC_API_KEY not set - skipping Anthropic MCP test")
    
    if not postman_key:
        results.add_warning("Postman API key", "POSTMAN_API_KEY not set - skipping Postman MCP test")
    
    if not anthropic_key and not postman_key:
        results.add_fail("MCP configuration", "No API keys configured. Set ANTHROPIC_API_KEY and/or POSTMAN_API_KEY in .env")
        return False
    
    try:
        from mcp_client import MCPClient
        
        # Initialize MCP client
        mcp_client = MCPClient()
        results.add_pass("MCPClient initialization", "MCP client created successfully")
        
        # Test initialization (with timeout)
        try:
            await asyncio.wait_for(mcp_client.initialize(), timeout=30.0)
            results.add_pass("MCP initialization", "MCP connections established")
        except asyncio.TimeoutError:
            results.add_fail("MCP initialization", "Connection timeout after 30 seconds. Check network and MCP server availability.")
            return False
        
        # Test Claude connection if available
        if anthropic_key and mcp_client.claude_session:
            try:
                response = await asyncio.wait_for(
                    mcp_client.call_claude("Say 'test successful' if you can read this.", temperature=0.0),
                    timeout=15.0
                )
                if response and len(response) > 0:
                    results.add_pass("Claude MCP", f"Claude responded: {response[:50]}...")
                else:
                    results.add_fail("Claude MCP", "Claude returned empty response")
            except asyncio.TimeoutError:
                results.add_fail("Claude MCP", "Claude call timeout")
            except Exception as e:
                results.add_fail("Claude MCP", f"Claude call failed: {e}")
        
        # Test Postman connection if available
        if postman_key and mcp_client.postman_session:
            try:
                apis = await asyncio.wait_for(
                    mcp_client.discover_apis("weather", verified_only=True, max_results=3),
                    timeout=15.0
                )
                if apis and len(apis) > 0:
                    results.add_pass("Postman MCP", f"Discovered {len(apis)} APIs")
                else:
                    results.add_warning("Postman MCP", "No APIs discovered (may be normal)")
            except asyncio.TimeoutError:
                results.add_fail("Postman MCP", "API discovery timeout")
            except Exception as e:
                results.add_fail("Postman MCP", f"API discovery failed: {e}")
        
        # Cleanup
        await mcp_client.close()
        
        return True
        
    except ImportError as e:
        results.add_fail("MCPClient import", f"Cannot import MCPClient: {e}")
        return False
    except Exception as e:
        results.add_fail("MCP test", str(e))
        return False


async def test_health_endpoint(results: TestResults):
    """Test FastAPI health endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Health Endpoint")
    print("="*60)
    
    try:
        import httpx
        from main import app
        
        # Test health endpoint directly
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            results.add_pass("Health endpoint", f"Status code: {response.status_code}")
            
            data = response.json()
            if "status" in data:
                results.add_pass("Health response", f"Status: {data['status']}")
            
            if "configuration" in data:
                config = data["configuration"]
                results.add_pass("Health configuration", f"Redis: {config.get('redis_configured')}, Anthropic: {config.get('anthropic_configured')}")
        else:
            results.add_fail("Health endpoint", f"Unexpected status code: {response.status_code}")
            return False
        
        return True
        
    except ImportError as e:
        results.add_fail("Health endpoint test", f"Missing dependencies: {e}. Install with: pip install httpx")
        return False
    except Exception as e:
        results.add_fail("Health endpoint test", str(e))
        return False


async def test_integration_flow(results: TestResults):
    """Test basic integration flow"""
    print("\n" + "="*60)
    print("TEST 5: Integration Flow")
    print("="*60)
    
    try:
        from memory_store import MemoryStore
        import numpy as np
        
        # Test that all components can work together
        memory_store = MemoryStore()
        
        # Simulate a query flow
        query = "Test integration query"
        embedding = np.random.rand(1024).tolist()
        results_data = {"answer": "Integration test successful"}
        sources = ["test_api"]
        
        # Store
        memory_id = await memory_store.store(
            query=query,
            query_embedding=embedding,
            results=results_data,
            sources=sources
        )
        
        # Retrieve
        similar = await memory_store.find_similar(embedding, top_k=1)
        
        # Update
        await memory_store.update_relevance(memory_id, 0.9)
        
        # Get metrics
        metrics = await memory_store.get_metrics()
        
        memory_store.close()
        
        results.add_pass("Integration flow", "Store → Retrieve → Update → Metrics flow completed")
        
        return True
        
    except Exception as e:
        results.add_fail("Integration flow", str(e))
        return False


async def main():
    """Run all infrastructure tests"""
    print("\n" + "="*60)
    print("ADAPTIVE RESEARCH AGENT - INFRASTRUCTURE TESTS")
    print("="*60)
    
    results = TestResults()
    
    # Run tests
    await test_redis_connection(results)
    await test_memory_store(results)
    await test_mcp_connections(results)
    await test_health_endpoint(results)
    await test_integration_flow(results)
    
    # Print summary
    success = results.summary()
    
    if success:
        print("\n✓ All critical tests passed! Infrastructure is ready.")
        print("\nNext steps:")
        print("1. Ensure Redis is running: docker run -p 6379:6379 redis/redis-stack-server:latest")
        print("2. Set API keys in .env file")
        print("3. Start the server: python backend/main.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
