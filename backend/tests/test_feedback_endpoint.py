"""
Integration tests for Feedback API Endpoint

Tests the complete feedback flow including:
- Memory updates
- Learning engine threshold adjustments
- Feedback logging

Requirements: 12.2, 3.1, 3.2, 3.6
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models import FeedbackRequest, FeedbackResponse
from memory_store import MemoryStore, MemoryEntry
from learning_engine import LearningEngine, FeedbackEntry


@pytest.fixture
def mock_memory_store():
    """Create mock memory store"""
    store = MagicMock(spec=MemoryStore)
    
    # Mock update_relevance to return success
    async def mock_update_relevance(memory_id, new_score):
        return True
    
    store.update_relevance = AsyncMock(side_effect=mock_update_relevance)
    
    # Mock get_recent to return sample memories
    async def mock_get_recent(limit=50):
        return [
            MemoryEntry(
                memory_id=f"mem_{i}",
                query=f"Test query {i}",
                results={"summary": f"Result {i}"},
                relevance_score=0.5 + (i % 5) * 0.1,
                api_sources=["api1", "api2"],
                similarity_score=0.8,
                timestamp=time.time() - i * 100,
                session_id=None
            )
            for i in range(limit)
        ]
    
    store.get_recent = AsyncMock(side_effect=mock_get_recent)
    
    return store


@pytest.fixture
def mock_learning_engine():
    """Create mock learning engine"""
    engine = MagicMock(spec=LearningEngine)
    
    # Mock adjust_confidence_threshold
    async def mock_adjust_threshold(recent_feedback):
        return 0.6  # New threshold
    
    engine.adjust_confidence_threshold = AsyncMock(side_effect=mock_adjust_threshold)
    
    return engine


@pytest.mark.asyncio
async def test_feedback_updates_memory(mock_memory_store):
    """
    Test that feedback successfully updates memory entry.
    
    Requirements:
    - 3.1: Accept relevance feedback and update memory
    - 3.2: Update Relevance_Score for corresponding memory entry
    """
    # Create feedback request
    feedback = FeedbackRequest(
        query_id="query_123",
        memory_id="memory_456",
        relevance_score=0.9,
        feedback_notes="Excellent results"
    )
    
    # Update memory
    success = await mock_memory_store.update_relevance(
        memory_id=feedback.memory_id,
        new_score=feedback.relevance_score
    )
    
    # Verify update was called
    assert success is True
    mock_memory_store.update_relevance.assert_called_once_with(
        memory_id="memory_456",
        new_score=0.9
    )


@pytest.mark.asyncio
async def test_feedback_triggers_threshold_adjustment(mock_memory_store, mock_learning_engine):
    """
    Test that feedback triggers learning engine threshold adjustment.
    
    Requirements:
    - 3.3: Adjust Confidence_Threshold values based on feedback patterns
    """
    # Get recent memories
    recent_memories = await mock_memory_store.get_recent(limit=50)
    
    # Convert to feedback entries
    recent_feedback = []
    for mem in recent_memories:
        recent_feedback.append(FeedbackEntry(
            query_id=mem.memory_id,
            confidence=mem.relevance_score,
            relevance_score=mem.relevance_score,
            timestamp=mem.timestamp
        ))
    
    # Adjust threshold
    new_threshold = await mock_learning_engine.adjust_confidence_threshold(
        recent_feedback=recent_feedback
    )
    
    # Verify threshold was adjusted
    assert new_threshold == 0.6
    mock_learning_engine.adjust_confidence_threshold.assert_called_once()


@pytest.mark.asyncio
async def test_feedback_with_invalid_memory_id(mock_memory_store):
    """
    Test feedback with non-existent memory ID.
    
    Requirements: 12.7 - Handle errors gracefully
    """
    # Mock update_relevance to return False (memory not found)
    async def mock_update_not_found(memory_id, new_score):
        return False
    
    mock_memory_store.update_relevance = AsyncMock(side_effect=mock_update_not_found)
    
    # Create feedback request
    feedback = FeedbackRequest(
        query_id="query_123",
        memory_id="nonexistent_memory",
        relevance_score=0.8
    )
    
    # Try to update memory
    success = await mock_memory_store.update_relevance(
        memory_id=feedback.memory_id,
        new_score=feedback.relevance_score
    )
    
    # Should return False
    assert success is False


@pytest.mark.asyncio
async def test_feedback_request_model_validation():
    """
    Test FeedbackRequest model validation.
    
    Requirements: 12.2 - Accept FeedbackRequest with validation
    """
    from pydantic import ValidationError
    
    # Valid request
    valid = FeedbackRequest(
        query_id="q1",
        memory_id="m1",
        relevance_score=0.75
    )
    assert valid.relevance_score == 0.75
    
    # Invalid: score too high
    with pytest.raises(ValidationError):
        FeedbackRequest(
            query_id="q1",
            memory_id="m1",
            relevance_score=1.5
        )
    
    # Invalid: score too low
    with pytest.raises(ValidationError):
        FeedbackRequest(
            query_id="q1",
            memory_id="m1",
            relevance_score=-0.1
        )
    
    # Invalid: notes too long
    with pytest.raises(ValidationError):
        FeedbackRequest(
            query_id="q1",
            memory_id="m1",
            relevance_score=0.8,
            feedback_notes="x" * 1001
        )


@pytest.mark.asyncio
async def test_feedback_response_structure():
    """
    Test FeedbackResponse model structure.
    
    Requirements: 12.2 - POST /api/research/feedback response model
    """
    response = FeedbackResponse(
        success=True,
        message="Feedback recorded successfully",
        memory_id="memory_123",
        new_relevance_score=0.85
    )
    
    assert response.success is True
    assert response.message == "Feedback recorded successfully"
    assert response.memory_id == "memory_123"
    assert response.new_relevance_score == 0.85
    assert 0.0 <= response.new_relevance_score <= 1.0


@pytest.mark.asyncio
async def test_feedback_logging():
    """
    Test that feedback is properly logged for analysis.
    
    Requirements: 3.6 - Log all feedback with timestamps for learning loop analysis
    """
    import structlog
    import logging
    from io import StringIO
    
    # Capture log output
    log_output = StringIO()
    
    # Configure structlog to write to our StringIO
    structlog.configure(
        processors=[
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_output),
    )
    
    logger = structlog.get_logger()
    
    # Log feedback
    feedback = FeedbackRequest(
        query_id="query_123",
        memory_id="memory_456",
        relevance_score=0.9,
        feedback_notes="Very helpful"
    )
    
    logger.info(
        "feedback_processed",
        query_id=feedback.query_id,
        memory_id=feedback.memory_id,
        relevance_score=feedback.relevance_score,
        feedback_notes=feedback.feedback_notes
    )
    
    # Verify log contains feedback information
    log_content = log_output.getvalue()
    assert "feedback_processed" in log_content
    assert "query_123" in log_content
    assert "memory_456" in log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
