"""
Tests for Session Manager

Tests session management functionality for multi-turn conversations.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6
"""
import pytest
import time
from session_manager import SessionManager, SessionContext, QueryHistoryItem, SessionManagerError


@pytest.fixture
def session_manager():
    """Create a session manager for testing"""
    manager = SessionManager(
        redis_url="redis://localhost:6379",
        session_expiration_seconds=3600
    )
    yield manager
    manager.close()


def test_create_session(session_manager):
    """
    Test creating a new session.
    
    Requirements: 15.5 - Support session management with unique session IDs
    """
    # Create session
    session_id = session_manager.create_session(metadata={"test": "data"})
    
    # Verify session ID format
    assert session_id.startswith("session_")
    assert len(session_id) > 10
    
    # Verify session can be retrieved
    session_context = session_manager.get_session(session_id)
    assert session_context is not None
    assert session_context.session_id == session_id
    assert session_context.metadata == {"test": "data"}
    assert len(session_context.query_history) == 0


def test_get_nonexistent_session(session_manager):
    """
    Test retrieving a session that doesn't exist.
    
    Requirements: 15.5 - Session management
    """
    session_context = session_manager.get_session("session_nonexistent")
    assert session_context is None


def test_add_query_to_session(session_manager):
    """
    Test adding queries to a session.
    
    Requirements:
    - 15.1: Maintain conversation context across multiple queries
    - 15.4: Store conversation history in Agent_Memory
    """
    # Create session
    session_id = session_manager.create_session()
    
    # Add first query
    success = session_manager.add_query_to_session(
        session_id=session_id,
        query_id="query_1",
        query="What is AI?",
        synthesized_answer="AI is artificial intelligence...",
        sources=["api_1", "api_2"],
        confidence_score=0.85,
        memory_id="memory_1"
    )
    
    assert success is True
    
    # Add second query
    success = session_manager.add_query_to_session(
        session_id=session_id,
        query_id="query_2",
        query="Tell me more about machine learning",
        synthesized_answer="Machine learning is a subset of AI...",
        sources=["api_1", "api_3"],
        confidence_score=0.90,
        memory_id="memory_2"
    )
    
    assert success is True
    
    # Retrieve session and verify history
    session_context = session_manager.get_session(session_id)
    assert len(session_context.query_history) == 2
    
    # Verify first query
    first_query = session_context.query_history[0]
    assert first_query.query_id == "query_1"
    assert first_query.query == "What is AI?"
    assert first_query.confidence_score == 0.85
    assert first_query.sources == ["api_1", "api_2"]
    
    # Verify second query
    second_query = session_context.query_history[1]
    assert second_query.query_id == "query_2"
    assert second_query.query == "Tell me more about machine learning"
    assert second_query.confidence_score == 0.90


def test_get_session_history(session_manager):
    """
    Test retrieving session history.
    
    Requirements:
    - 15.2: Use previous query results as context for follow-up questions
    - 15.3: Allow users to reference previous results
    """
    # Create session and add queries
    session_id = session_manager.create_session()
    
    session_manager.add_query_to_session(
        session_id=session_id,
        query_id="query_1",
        query="First query",
        synthesized_answer="First answer",
        sources=["api_1"],
        confidence_score=0.8,
        memory_id="memory_1"
    )
    
    session_manager.add_query_to_session(
        session_id=session_id,
        query_id="query_2",
        query="Second query",
        synthesized_answer="Second answer",
        sources=["api_2"],
        confidence_score=0.9,
        memory_id="memory_2"
    )
    
    # Get history
    history = session_manager.get_session_history(session_id)
    
    assert len(history) == 2
    assert history[0].query == "First query"
    assert history[1].query == "Second query"


def test_get_previous_query(session_manager):
    """
    Test retrieving specific previous queries.
    
    Requirements: 15.3 - Allow users to reference previous results
    """
    # Create session and add queries
    session_id = session_manager.create_session()
    
    for i in range(3):
        session_manager.add_query_to_session(
            session_id=session_id,
            query_id=f"query_{i}",
            query=f"Query {i}",
            synthesized_answer=f"Answer {i}",
            sources=[f"api_{i}"],
            confidence_score=0.8,
            memory_id=f"memory_{i}"
        )
    
    # Get most recent query (index -1)
    recent = session_manager.get_previous_query(session_id, -1)
    assert recent is not None
    assert recent.query == "Query 2"
    
    # Get first query (index 0)
    first = session_manager.get_previous_query(session_id, 0)
    assert first is not None
    assert first.query == "Query 0"
    
    # Get second query (index 1)
    second = session_manager.get_previous_query(session_id, 1)
    assert second is not None
    assert second.query == "Query 1"
    
    # Get out of bounds query
    invalid = session_manager.get_previous_query(session_id, 10)
    assert invalid is None


def test_delete_session(session_manager):
    """
    Test deleting a session.
    
    Requirements: 15.6 - Session management
    """
    # Create session
    session_id = session_manager.create_session()
    
    # Verify it exists
    session_context = session_manager.get_session(session_id)
    assert session_context is not None
    
    # Delete session
    success = session_manager.delete_session(session_id)
    assert success is True
    
    # Verify it's gone
    session_context = session_manager.get_session(session_id)
    assert session_context is None
    
    # Try to delete again
    success = session_manager.delete_session(session_id)
    assert success is False


def test_session_expiration_tracking(session_manager):
    """
    Test that session tracks last activity time.
    
    Requirements: 15.6 - Expire inactive sessions after 1 hour
    """
    # Create session
    session_id = session_manager.create_session()
    
    # Get initial session
    session_context = session_manager.get_session(session_id)
    initial_activity = session_context.last_activity
    
    # Wait a moment
    time.sleep(0.1)
    
    # Add query (should update last_activity)
    session_manager.add_query_to_session(
        session_id=session_id,
        query_id="query_1",
        query="Test query",
        synthesized_answer="Test answer",
        sources=["api_1"],
        confidence_score=0.8,
        memory_id="memory_1"
    )
    
    # Get updated session
    session_context = session_manager.get_session(session_id)
    updated_activity = session_context.last_activity
    
    # Verify last_activity was updated
    assert updated_activity > initial_activity


def test_add_query_to_nonexistent_session(session_manager):
    """
    Test adding query to a session that doesn't exist.
    
    Requirements: 15.1 - Session management error handling
    """
    success = session_manager.add_query_to_session(
        session_id="session_nonexistent",
        query_id="query_1",
        query="Test query",
        synthesized_answer="Test answer",
        sources=["api_1"],
        confidence_score=0.8,
        memory_id="memory_1"
    )
    
    assert success is False


def test_session_metadata(session_manager):
    """
    Test session metadata storage.
    
    Requirements: 15.5 - Session management with metadata
    """
    # Create session with metadata
    metadata = {
        "user_id": "user_123",
        "context": "research",
        "tags": ["AI", "ML"]
    }
    
    session_id = session_manager.create_session(metadata=metadata)
    
    # Retrieve and verify metadata
    session_context = session_manager.get_session(session_id)
    assert session_context.metadata == metadata
    assert session_context.metadata["user_id"] == "user_123"
    assert "AI" in session_context.metadata["tags"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
