"""
Simple system test to verify the application works
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

async def test_components():
    """Test individual components"""
    print("=" * 60)
    print("SYSTEM TEST - Adaptive Research Agent")
    print("=" * 60)
    
    # Test 1: Environment variables
    print("\n1. Checking environment variables...")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    postman_key = os.getenv("POSTMAN_API_KEY")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    if not anthropic_key:
        print("   ❌ ANTHROPIC_API_KEY not set")
        return False
    else:
        print(f"   ✅ ANTHROPIC_API_KEY set ({anthropic_key[:10]}...)")
    
    if not postman_key:
        print("   ⚠️  POSTMAN_API_KEY not set (optional)")
    else:
        print(f"   ✅ POSTMAN_API_KEY set ({postman_key[:10]}...)")
    
    print(f"   ✅ REDIS_URL: {redis_url}")
    
    # Test 2: Redis connection
    print("\n2. Testing Redis connection...")
    try:
        import redis
        client = redis.from_url(redis_url)
        client.ping()
        print("   ✅ Redis connected")
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        print("   ⚠️  Application will run in degraded mode")
    
    # Test 3: MCP servers exist
    print("\n3. Checking MCP servers...")
    mcp_servers = [
        "mcp-servers/postman/dist/index.js",
        "mcp-servers/memory/dist/index.js",
        "mcp-servers/research-tools/dist/index.js"
    ]
    
    for server in mcp_servers:
        if os.path.exists(server):
            print(f"   ✅ {server}")
        else:
            print(f"   ❌ {server} not found")
            return False
    
    # Test 4: Python dependencies
    print("\n4. Checking Python dependencies...")
    try:
        import fastapi
        import anthropic
        import mcp
        import structlog
        print("   ✅ All dependencies installed")
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ SYSTEM TEST PASSED")
    print("=" * 60)
    print("\nYou can now start the server with:")
    print("  python backend/main.py")
    print("\nOr with uvicorn:")
    print("  uvicorn backend.main:app --reload")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_components())
    sys.exit(0 if result else 1)
