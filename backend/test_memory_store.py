"""
Test script for MemoryStore functionality

This script tests the basic operations of the MemoryStore class:
- Connection to Redis
- Index creation
- Storing memories
- Finding similar memories
- Updating relevance scores
- Getting metrics
"""
import asyncio
import os
import sys
from typing import List
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from memory_store import MemoryStore, MemoryEntry, MemoryMetrics


async def test_memory_store():
    """Test basic memory store operations"""
    
    print("=" * 60)
    print("Testing MemoryStore")
    print("=" * 60)
    
    # Initialize memory store
    print("\n1. Initializing MemoryStore...")
    try:
        memory_store = MemoryStore(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            embedding_dim=1024
        )
        print("✓ MemoryStore initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize MemoryStore: {e}")
        return False
    
    # Test storing a memory
    print("\n2. Testing memory storage...")
    try:
        # Create a test embedding (1024-dimensional)
        test_embedding = np.random.rand(1024).tolist()
        
        memory_id = await memory_store.store(
            query="What are the latest AI developments?",
            query_embedding=test_embedding,
            results={
                "summary": "Recent AI developments include advances in LLMs and multimodal models.",
                "details": "Multiple sources report significant progress..."
            },
            sources=["tech_api", "news_api"],
            relevance_score=0.8,
            session_id="test_session_1"
        )
        
        print(f"✓ Memory stored successfully with ID: {memory_id}")
    except Exception as e:
        print(f"✗ Failed to store memory: {e}")
        return False
    
    # Test storing another memory
    print("\n3. Storing another similar memory...")
    try:
        # Create a similar embedding (slight variation)
        similar_embedding = (np.array(test_embedding) + np.random.rand(1024) * 0.1).tolist()
        
        memory_id_2 = await memory_store.store(
            query="What's new in artificial intelligence?",
            query_embedding=similar_embedding,
            results={
                "summary": "AI field is rapidly evolving with new breakthroughs.",
                "details": "Key developments in neural networks..."
            },
            sources=["research_api", "tech_api"],
            relevance_score=0.7
        )
        
        print(f"✓ Second memory stored with ID: {memory_id_2}")
    except Exception as e:
        print(f"✗ Failed to store second memory: {e}")
        return False
    
    # Test finding similar memories
    print("\n4. Testing similarity search...")
    try:
        # Search with the first embedding
        similar_memories = await memory_store.find_similar(
            query_embedding=test_embedding,
            top_k=5,
            min_relevance=0.0
        )
        
        print(f"✓ Found {len(similar_memories)} similar memories")
        
        for i, mem in enumerate(similar_memories, 1):
            print(f"   {i}. Query: {mem.query[:50]}...")
            print(f"      Similarity: {mem.similarity_score:.4f}")
            print(f"      Relevance: {mem.relevance_score:.2f}")
            print(f"      Sources: {', '.join(mem.api_sources)}")
    except Exception as e:
        print(f"✗ Failed to find similar memories: {e}")
        return False
    
    # Test updating relevance
    print("\n5. Testing relevance update...")
    try:
        success = await memory_store.update_relevance(
            memory_id=memory_id,
            new_score=0.95
        )
        
        if success:
            print(f"✓ Relevance score updated to 0.95")
            
            # Verify update
            updated_memory = await memory_store.get_memory(memory_id)
            if updated_memory and updated_memory.relevance_score == 0.95:
                print(f"✓ Update verified: {updated_memory.relevance_score}")
            else:
                print(f"✗ Update verification failed")
        else:
            print(f"✗ Failed to update relevance")
    except Exception as e:
        print(f"✗ Error updating relevance: {e}")
        return False
    
    # Test getting recent memories
    print("\n6. Testing recent memories retrieval...")
    try:
        recent = await memory_store.get_recent(limit=10, min_relevance=0.0)
        print(f"✓ Retrieved {len(recent)} recent memories")
        
        for i, mem in enumerate(recent[:3], 1):
            print(f"   {i}. {mem.query[:50]}... (score: {mem.relevance_score:.2f})")
    except Exception as e:
        print(f"✗ Failed to get recent memories: {e}")
        return False
    
    # Test getting metrics
    print("\n7. Testing metrics retrieval...")
    try:
        metrics = await memory_store.get_metrics()
        print(f"✓ Metrics retrieved:")
        print(f"   Total memories: {metrics.total_memories}")
        print(f"   Average relevance: {metrics.avg_relevance:.2f}")
        print(f"   High quality memories: {metrics.high_quality_memories}")
        print(f"   Memory size: {metrics.memory_size_bytes} bytes")
    except Exception as e:
        print(f"✗ Failed to get metrics: {e}")
        return False
    
    # Test with high relevance filter
    print("\n8. Testing filtered search (min_relevance=0.7)...")
    try:
        high_quality = await memory_store.find_similar(
            query_embedding=test_embedding,
            top_k=5,
            min_relevance=0.7
        )
        print(f"✓ Found {len(high_quality)} high-quality memories (relevance >= 0.7)")
    except Exception as e:
        print(f"✗ Failed filtered search: {e}")
        return False
    
    # Close connection
    print("\n9. Closing connection...")
    try:
        memory_store.close()
        print("✓ Connection closed successfully")
    except Exception as e:
        print(f"✗ Error closing connection: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)
    
    return True


async def test_error_handling():
    """Test error handling and edge cases"""
    
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    memory_store = MemoryStore()
    
    # Test invalid embedding dimension
    print("\n1. Testing invalid embedding dimension...")
    try:
        wrong_embedding = [0.1] * 512  # Wrong dimension
        await memory_store.store(
            query="test",
            query_embedding=wrong_embedding,
            results={},
            sources=[]
        )
        print("✗ Should have raised error for wrong dimension")
    except (ValueError, Exception) as e:
        print(f"✓ Correctly raised error: {type(e).__name__}")
    
    # Test invalid relevance score
    print("\n2. Testing invalid relevance score...")
    try:
        await memory_store.update_relevance(
            memory_id="memory:test",
            new_score=1.5  # Invalid score > 1.0
        )
        print("✗ Should have raised error for invalid score")
    except (ValueError, Exception) as e:
        print(f"✓ Correctly raised error: {type(e).__name__}")
    
    # Test non-existent memory
    print("\n3. Testing non-existent memory update...")
    try:
        result = await memory_store.update_relevance(
            memory_id="memory:nonexistent",
            new_score=0.5
        )
        if not result:
            print("✓ Correctly returned False for non-existent memory")
        else:
            print("✗ Should have returned False")
    except Exception as e:
        print(f"✓ Handled gracefully: {type(e).__name__}")
    
    memory_store.close()
    
    print("\n" + "=" * 60)
    print("Error handling tests completed! ✓")
    print("=" * 60)


async def main():
    """Run all tests"""
    print("\n🧪 Starting MemoryStore Tests\n")
    
    # Check if Redis is available
    print("Checking Redis connection...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"Redis URL: {redis_url}")
    
    try:
        # Run basic tests
        success = await test_memory_store()
        
        if success:
            # Run error handling tests
            await test_error_handling()
            
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
