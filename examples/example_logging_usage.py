"""
Example: Comprehensive Logging Usage

This example demonstrates the comprehensive logging capabilities
of the Adaptive Research Agent.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6
"""
import asyncio
import httpx
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8000"


async def example_query_logs():
    """
    Demonstrate querying logs with various filters.
    
    Requirements: 14.5 - Expose logs via /api/logs endpoint with filtering
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 80)
        print("Logging Examples")
        print("=" * 80)
        
        # Example 1: Get all recent logs
        print("\n1. Getting all recent logs (last 10)...")
        response = await client.get(f"{BASE_URL}/api/logs?limit=10")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {data['total']} total logs")
            print(f"   ✓ Returned {data['returned']} logs")
            
            if data['logs']:
                print("\n   Recent logs:")
                for log in data['logs'][:3]:  # Show first 3
                    dt = datetime.fromisoformat(log['datetime'])
                    print(f"      [{dt.strftime('%H:%M:%S')}] {log['level'].upper()}: {log['message']}")
                    if log['request_id']:
                        print(f"         Request ID: {log['request_id']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            return
        
        # Example 2: Filter by log level
        print("\n2. Getting only ERROR logs...")
        response = await client.get(f"{BASE_URL}/api/logs?level=error&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {len(data['logs'])} error logs")
            
            for log in data['logs'][:3]:
                dt = datetime.fromisoformat(log['datetime'])
                print(f"      [{dt.strftime('%H:%M:%S')}] {log['message']}")
        
        # Example 3: Filter by event type
        print("\n3. Getting logs for 'query_processed' events...")
        response = await client.get(f"{BASE_URL}/api/logs?event=query_processed&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {len(data['logs'])} query_processed events")
            
            for log in data['logs'][:3]:
                dt = datetime.fromisoformat(log['datetime'])
                print(f"      [{dt.strftime('%H:%M:%S')}] {log['message']}")
                if 'query' in log['context']:
                    print(f"         Query: {log['context']['query']}")
        
        # Example 4: Filter by time range
        print("\n4. Getting logs from last 5 minutes...")
        five_minutes_ago = (datetime.now() - timedelta(minutes=5)).timestamp()
        response = await client.get(
            f"{BASE_URL}/api/logs?start_time={five_minutes_ago}&limit=10"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {len(data['logs'])} logs in last 5 minutes")
        
        # Example 5: Filter by request ID (trace a specific request)
        print("\n5. Tracing a specific request...")
        # First, make a query to get a request ID
        query_response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "What is machine learning?",
                "max_sources": 2,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if query_response.status_code == 200:
            # Get request ID from response headers
            request_id = query_response.headers.get("X-Request-ID")
            
            if request_id:
                print(f"   ✓ Query processed with request ID: {request_id}")
                
                # Query logs for this request
                response = await client.get(
                    f"{BASE_URL}/api/logs?request_id={request_id}&limit=50"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✓ Found {len(data['logs'])} logs for this request")
                    print("\n   Request trace:")
                    
                    for log in data['logs']:
                        dt = datetime.fromisoformat(log['datetime'])
                        print(f"      [{dt.strftime('%H:%M:%S.%f')[:-3]}] {log['event']}: {log['message']}")
        
        # Example 6: Get log statistics
        print("\n6. Getting log statistics...")
        response = await client.get(f"{BASE_URL}/api/logs?limit=1")
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            
            print(f"   ✓ Total logs in memory: {stats.get('memory_logs_count', 0)}")
            print(f"   ✓ Redis connected: {stats.get('redis_connected', False)}")
            print(f"   ✓ Retention period: {stats.get('retention_days', 0)} days")
            
            if 'level_counts' in stats:
                print("\n   Logs by level:")
                for level, count in stats['level_counts'].items():
                    print(f"      {level.upper()}: {count}")
        
        # Example 7: Pagination
        print("\n7. Demonstrating pagination...")
        # Get first page
        response = await client.get(f"{BASE_URL}/api/logs?limit=5&offset=0")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Page 1: {data['returned']} logs (offset 0)")
        
        # Get second page
        response = await client.get(f"{BASE_URL}/api/logs?limit=5&offset=5")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Page 2: {data['returned']} logs (offset 5)")
        
        # Example 8: Combined filters
        print("\n8. Using combined filters...")
        response = await client.get(
            f"{BASE_URL}/api/logs?level=info&event=query_processed&limit=5"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {len(data['logs'])} INFO logs for query_processed events")
            print(f"   ✓ Filters applied: {data['filters']}")
        
        print("\n" + "=" * 80)
        print("Logging Examples Complete!")
        print("=" * 80)


async def example_performance_metrics():
    """
    Demonstrate performance metrics logging.
    
    Requirements: 14.3 - Log performance metrics
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "=" * 80)
        print("Performance Metrics Logging Example")
        print("=" * 80)
        
        print("\n1. Making a query to generate performance logs...")
        response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "What are the benefits of AI?",
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Query processed in {result['processing_time_ms']:.0f}ms")
            
            # Get logs with performance context
            request_id = response.headers.get("X-Request-ID")
            if request_id:
                log_response = await client.get(
                    f"{BASE_URL}/api/logs?request_id={request_id}&limit=50"
                )
                
                if log_response.status_code == 200:
                    data = log_response.json()
                    
                    print("\n   Performance metrics from logs:")
                    for log in data['logs']:
                        if 'processing_time_ms' in log['context']:
                            print(f"      Processing time: {log['context']['processing_time_ms']}ms")
                        if 'confidence_score' in log['context']:
                            print(f"      Confidence score: {log['context']['confidence_score']}")
                        if 'sources_used' in log['context']:
                            print(f"      Sources used: {len(log['context']['sources_used'])}")
        
        print("\n" + "=" * 80)


async def example_learning_decisions():
    """
    Demonstrate logging of learning decisions with reasoning.
    
    Requirements: 14.4 - Log learning loop decisions with reasoning
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "=" * 80)
        print("Learning Decisions Logging Example")
        print("=" * 80)
        
        print("\n1. Making queries to trigger learning...")
        
        # First query
        response1 = await client.post(
            f"{BASE_URL}/api/research/query",
            json={"query": "What is deep learning?", "max_sources": 2}
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            query_id1 = result1['query_id']
            memory_id1 = result1['memory_id']
            
            # Provide feedback
            await client.post(
                f"{BASE_URL}/api/research/feedback",
                json={
                    "query_id": query_id1,
                    "memory_id": memory_id1,
                    "relevance_score": 0.9,
                    "feedback_notes": "Very helpful"
                }
            )
            
            print("   ✓ Query 1 processed and feedback submitted")
        
        # Second similar query
        response2 = await client.post(
            f"{BASE_URL}/api/research/query",
            json={"query": "Tell me about neural networks", "max_sources": 2}
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            print("   ✓ Query 2 processed (should use learning from Query 1)")
            
            if result2['refinement_applied']:
                print(f"   ✓ Query refinement applied!")
                print(f"      Refinements: {result2['refinements']}")
                print(f"      Confidence: {result2['refinement_confidence']:.2f}")
        
        # Query logs for learning decisions
        print("\n2. Checking logs for learning decisions...")
        response = await client.get(
            f"{BASE_URL}/api/logs?event=query_refined&limit=10"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Found {len(data['logs'])} query refinement events")
            
            for log in data['logs'][:2]:
                if 'reasoning' in log['context']:
                    print(f"\n   Refinement reasoning:")
                    print(f"      {log['context']['reasoning']}")
        
        print("\n" + "=" * 80)


async def main():
    """Run all examples"""
    try:
        await example_query_logs()
        await example_performance_metrics()
        await example_learning_decisions()
        
    except httpx.ConnectError:
        print("\n" + "=" * 80)
        print("ERROR: Could not connect to the API server")
        print("=" * 80)
        print("\nPlease ensure the server is running:")
        print("  cd backend")
        print("  python main.py")
        print("\nOr:")
        print("  uvicorn main:app --reload")
        print("=" * 80)
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
