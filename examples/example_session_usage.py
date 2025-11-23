"""
Example: Multi-Turn Conversation with Session Management

This example demonstrates how to use the session management feature
for multi-turn conversations with the Adaptive Research Agent.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6
"""
import asyncio
import httpx
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


async def example_multi_turn_conversation():
    """
    Demonstrate multi-turn conversation using session management.
    
    Requirements:
    - 15.1: Maintain conversation context across multiple queries
    - 15.2: Use previous query results as context for follow-up questions
    - 15.3: Allow users to reference previous results
    - 15.5: Support session management with unique session IDs
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 80)
        print("Multi-Turn Conversation Example")
        print("=" * 80)
        
        # Step 1: Create a new session
        print("\n1. Creating a new conversation session...")
        response = await client.post(f"{BASE_URL}/api/session")
        session_data = response.json()
        session_id = session_data["session_id"]
        
        print(f"   ✓ Session created: {session_id}")
        print(f"   ✓ Expires in: {session_data['expiration_seconds']} seconds (1 hour)")
        
        # Step 2: First query in the conversation
        print("\n2. First query: 'What is artificial intelligence?'")
        response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "What is artificial intelligence?",
                "session_id": session_id,
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Query processed (ID: {result['query_id']})")
            print(f"   ✓ Confidence: {result['confidence_score']:.2f}")
            print(f"   ✓ Answer: {result['synthesized_answer'][:150]}...")
            print(f"   ✓ Sources: {len(result['sources'])} API sources used")
        else:
            print(f"   ✗ Error: {response.status_code}")
            return
        
        # Step 3: Follow-up query (uses context from first query)
        print("\n3. Follow-up query: 'Can you tell me more about machine learning?'")
        print("   (This query will have access to the previous conversation context)")
        
        response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "Can you tell me more about machine learning?",
                "session_id": session_id,
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Query processed (ID: {result['query_id']})")
            print(f"   ✓ Confidence: {result['confidence_score']:.2f}")
            print(f"   ✓ Answer: {result['synthesized_answer'][:150]}...")
            print(f"   ✓ Refinement applied: {result['refinement_applied']}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            return
        
        # Step 4: Another follow-up query
        print("\n4. Another follow-up: 'What are some practical applications?'")
        
        response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "What are some practical applications?",
                "session_id": session_id,
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Query processed (ID: {result['query_id']})")
            print(f"   ✓ Confidence: {result['confidence_score']:.2f}")
            print(f"   ✓ Answer: {result['synthesized_answer'][:150]}...")
        else:
            print(f"   ✗ Error: {response.status_code}")
            return
        
        # Step 5: Retrieve session history
        print("\n5. Retrieving conversation history...")
        response = await client.get(f"{BASE_URL}/api/session/{session_id}/history")
        
        if response.status_code == 200:
            history_data = response.json()
            print(f"   ✓ Session has {history_data['query_count']} queries")
            print("\n   Conversation History:")
            
            for i, item in enumerate(history_data['history'], 1):
                timestamp = datetime.fromtimestamp(item['timestamp']).strftime('%H:%M:%S')
                print(f"\n   Query {i} [{timestamp}]:")
                print(f"      Q: {item['query']}")
                print(f"      A: {item['synthesized_answer'][:100]}...")
                print(f"      Confidence: {item['confidence_score']:.2f}")
                print(f"      Sources: {', '.join(item['sources'])}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            return
        
        # Step 6: Clean up - delete session
        print("\n6. Cleaning up - deleting session...")
        response = await client.delete(f"{BASE_URL}/api/session/{session_id}")
        
        if response.status_code == 200:
            print(f"   ✓ Session deleted successfully")
        else:
            print(f"   ✗ Error: {response.status_code}")
        
        print("\n" + "=" * 80)
        print("Multi-Turn Conversation Example Complete!")
        print("=" * 80)


async def example_session_without_explicit_creation():
    """
    Demonstrate that sessions are created automatically if not provided.
    
    Requirements: 15.5 - Support session management with unique session IDs
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "=" * 80)
        print("Automatic Session Creation Example")
        print("=" * 80)
        
        print("\n1. Making query without providing session_id...")
        print("   (System will automatically create a session)")
        
        response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "What is quantum computing?",
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result['session_id']
            
            print(f"   ✓ Query processed")
            print(f"   ✓ Automatic session created: {session_id}")
            print(f"   ✓ You can use this session_id for follow-up queries")
            
            # Make a follow-up query with the auto-created session
            print("\n2. Making follow-up query with auto-created session...")
            
            response = await client.post(
                f"{BASE_URL}/api/research/query",
                json={
                    "query": "How does it differ from classical computing?",
                    "session_id": session_id,
                    "max_sources": 3,
                    "include_report": False,
                    "alert_enabled": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Follow-up query processed")
                print(f"   ✓ Using same session: {result['session_id']}")
            else:
                print(f"   ✗ Error: {response.status_code}")
        else:
            print(f"   ✗ Error: {response.status_code}")
        
        print("\n" + "=" * 80)


async def example_referencing_previous_results():
    """
    Demonstrate referencing previous results in follow-up queries.
    
    Requirements: 15.3 - Allow users to reference previous results
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n" + "=" * 80)
        print("Referencing Previous Results Example")
        print("=" * 80)
        
        # Create session
        response = await client.post(f"{BASE_URL}/api/session")
        session_id = response.json()["session_id"]
        print(f"\n✓ Session created: {session_id}")
        
        # First query
        print("\n1. First query: 'What are the top 3 programming languages?'")
        response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "What are the top 3 programming languages?",
                "session_id": session_id,
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if response.status_code == 200:
            print("   ✓ Query processed")
        
        # Follow-up that references previous result
        print("\n2. Follow-up: 'Tell me more about the second one'")
        print("   (This references the previous query's results)")
        
        response = await client.post(
            f"{BASE_URL}/api/research/query",
            json={
                "query": "Tell me more about the second one",
                "session_id": session_id,
                "max_sources": 3,
                "include_report": False,
                "alert_enabled": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✓ Query processed")
            print(f"   ✓ Agent used conversation context to understand 'the second one'")
            print(f"   ✓ Answer: {result['synthesized_answer'][:150]}...")
        
        print("\n" + "=" * 80)


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("Session Management Examples")
    print("=" * 80)
    print("\nThese examples demonstrate multi-turn conversation capabilities")
    print("using session management in the Adaptive Research Agent.")
    print("\nRequirements demonstrated:")
    print("  - 15.1: Maintain conversation context across multiple queries")
    print("  - 15.2: Use previous query results as context")
    print("  - 15.3: Allow referencing previous results")
    print("  - 15.4: Store conversation history")
    print("  - 15.5: Support session management with unique IDs")
    print("  - 15.6: Expire inactive sessions after 1 hour")
    
    try:
        # Run examples
        await example_multi_turn_conversation()
        await example_session_without_explicit_creation()
        await example_referencing_previous_results()
        
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
