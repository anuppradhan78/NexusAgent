"""
Tests for Log Manager

Tests comprehensive logging functionality.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6
"""
import pytest
import time
from log_manager import LogManager, LogQuery, LogEntry


@pytest.fixture
def log_manager():
    """Create a log manager for testing (memory-only, no Redis)"""
    # Create manager without Redis to avoid cross-test contamination
    manager = LogManager(
        redis_url="redis://invalid:9999",  # Invalid URL to prevent Redis connection
        log_retention_days=7,
        max_memory_logs=100
    )
    # Clear memory buffer before each test
    manager.memory_logs.clear()
    yield manager
    manager.close()


def test_log_creation(log_manager):
    """
    Test creating log entries.
    
    Requirements: 14.1, 14.2 - Log all operations with structured JSON
    """
    # Log an event
    log_manager.log(
        level="info",
        message="Test log message",
        event="test_event",
        request_id="req_123",
        user_id="user_456",
        action="test_action"
    )
    
    # Verify log was stored in memory
    assert len(log_manager.memory_logs) == 1
    
    log_entry = log_manager.memory_logs[0]
    assert log_entry.level == "info"
    assert log_entry.message == "Test log message"
    assert log_entry.event == "test_event"
    assert log_entry.request_id == "req_123"
    assert log_entry.context["user_id"] == "user_456"
    assert log_entry.context["action"] == "test_action"


def test_multiple_logs(log_manager):
    """
    Test logging multiple events.
    
    Requirements: 14.1 - Log all operations
    """
    # Log multiple events
    for i in range(5):
        log_manager.log(
            level="info",
            message=f"Log message {i}",
            event=f"event_{i}",
            request_id=f"req_{i}"
        )
    
    assert len(log_manager.memory_logs) == 5


def test_query_logs_no_filters(log_manager):
    """
    Test querying logs without filters.
    
    Requirements: 14.5 - Expose logs with filtering
    """
    # Add some logs
    for i in range(3):
        log_manager.log(
            level="info",
            message=f"Message {i}",
            event=f"event_{i}"
        )
    
    # Query all logs
    query = LogQuery(limit=10)
    logs = log_manager.query_logs(query)
    
    assert len(logs) == 3


def test_query_logs_by_level(log_manager):
    """
    Test filtering logs by level.
    
    Requirements: 14.5 - Expose logs with filtering
    """
    # Add logs with different levels
    log_manager.log(level="info", message="Info message", event="info_event")
    log_manager.log(level="warning", message="Warning message", event="warning_event")
    log_manager.log(level="error", message="Error message", event="error_event")
    log_manager.log(level="info", message="Another info", event="info_event_2")
    
    # Query only info logs
    query = LogQuery(level="info", limit=10)
    logs = log_manager.query_logs(query)
    
    assert len(logs) == 2
    assert all(log.level == "info" for log in logs)


def test_query_logs_by_request_id(log_manager):
    """
    Test filtering logs by request ID.
    
    Requirements: 14.2 - Request ID tracing
    """
    # Add logs with different request IDs
    log_manager.log(level="info", message="Msg 1", event="event_1", request_id="req_123")
    log_manager.log(level="info", message="Msg 2", event="event_2", request_id="req_456")
    log_manager.log(level="info", message="Msg 3", event="event_3", request_id="req_123")
    
    # Query logs for specific request ID
    query = LogQuery(request_id="req_123", limit=10)
    logs = log_manager.query_logs(query)
    
    assert len(logs) == 2
    assert all(log.request_id == "req_123" for log in logs)


def test_query_logs_by_event(log_manager):
    """
    Test filtering logs by event name.
    
    Requirements: 14.5 - Expose logs with filtering
    """
    # Add logs with different events
    log_manager.log(level="info", message="Msg 1", event="query_processed")
    log_manager.log(level="info", message="Msg 2", event="api_called")
    log_manager.log(level="info", message="Msg 3", event="query_processed")
    
    # Query logs for specific event
    query = LogQuery(event="query_processed", limit=10)
    logs = log_manager.query_logs(query)
    
    assert len(logs) == 2
    assert all(log.event == "query_processed" for log in logs)


def test_query_logs_by_time_range(log_manager):
    """
    Test filtering logs by time range.
    
    Requirements: 14.5 - Expose logs with filtering
    """
    # Add logs at different times
    start_time = time.time()
    
    log_manager.log(level="info", message="Msg 1", event="event_1")
    time.sleep(0.1)
    
    middle_time = time.time()
    
    log_manager.log(level="info", message="Msg 2", event="event_2")
    time.sleep(0.1)
    
    end_time = time.time()
    
    log_manager.log(level="info", message="Msg 3", event="event_3")
    
    # Query logs in middle time range
    query = LogQuery(start_time=middle_time - 0.05, end_time=middle_time + 0.05, limit=10)
    logs = log_manager.query_logs(query)
    
    assert len(logs) == 1
    assert logs[0].message == "Msg 2"


def test_query_logs_pagination(log_manager):
    """
    Test log pagination.
    
    Requirements: 14.5 - Expose logs with filtering
    """
    # Add many logs
    for i in range(10):
        log_manager.log(level="info", message=f"Message {i}", event=f"event_{i}")
    
    # Query first page
    query = LogQuery(limit=3, offset=0)
    page1 = log_manager.query_logs(query)
    assert len(page1) == 3
    
    # Query second page
    query = LogQuery(limit=3, offset=3)
    page2 = log_manager.query_logs(query)
    assert len(page2) == 3
    
    # Verify different logs
    assert page1[0].message != page2[0].message


def test_log_stats(log_manager):
    """
    Test getting log statistics.
    
    Requirements: 14.3 - Log performance metrics
    """
    # Add logs with different levels
    log_manager.log(level="info", message="Info 1", event="event_1")
    log_manager.log(level="info", message="Info 2", event="event_2")
    log_manager.log(level="warning", message="Warning 1", event="event_3")
    log_manager.log(level="error", message="Error 1", event="event_4")
    
    # Get stats
    stats = log_manager.get_log_stats()
    
    assert stats["memory_logs_count"] == 4
    assert stats["level_counts"]["info"] == 2
    assert stats["level_counts"]["warning"] == 1
    assert stats["level_counts"]["error"] == 1
    assert "oldest_log" in stats
    assert "newest_log" in stats


def test_log_context_data(log_manager):
    """
    Test logging with context data.
    
    Requirements: 14.1, 14.4 - Log with reasoning and context
    """
    # Log with rich context
    log_manager.log(
        level="info",
        message="Query processed",
        event="query_processed",
        request_id="req_123",
        query="What is AI?",
        processing_time_ms=1500,
        confidence_score=0.85,
        sources_used=["api_1", "api_2"],
        refinement_applied=True,
        reasoning="High confidence due to multiple consistent sources"
    )
    
    # Verify context was stored
    log_entry = log_manager.memory_logs[0]
    assert log_entry.context["query"] == "What is AI?"
    assert log_entry.context["processing_time_ms"] == 1500
    assert log_entry.context["confidence_score"] == 0.85
    assert log_entry.context["sources_used"] == ["api_1", "api_2"]
    assert log_entry.context["refinement_applied"] is True
    assert "reasoning" in log_entry.context


def test_log_levels(log_manager):
    """
    Test different log levels.
    
    Requirements: 14.1 - Log all operations
    """
    # Log at different levels
    log_manager.log(level="debug", message="Debug message", event="debug_event")
    log_manager.log(level="info", message="Info message", event="info_event")
    log_manager.log(level="warning", message="Warning message", event="warning_event")
    log_manager.log(level="error", message="Error message", event="error_event")
    log_manager.log(level="critical", message="Critical message", event="critical_event")
    
    assert len(log_manager.memory_logs) == 5
    
    # Verify levels are normalized to lowercase
    levels = [log.level for log in log_manager.memory_logs]
    assert "debug" in levels
    assert "info" in levels
    assert "warning" in levels
    assert "error" in levels
    assert "critical" in levels


def test_memory_buffer_limit(log_manager):
    """
    Test that memory buffer respects max size.
    
    Requirements: 14.3 - Performance considerations
    """
    # Create log manager with small buffer
    small_manager = LogManager(
        redis_url="redis://localhost:6379",
        max_memory_logs=5
    )
    
    # Add more logs than buffer size
    for i in range(10):
        small_manager.log(level="info", message=f"Message {i}", event=f"event_{i}")
    
    # Verify buffer size is limited
    assert len(small_manager.memory_logs) == 5
    
    # Verify oldest logs were removed (newest kept)
    messages = [log.message for log in small_manager.memory_logs]
    assert "Message 9" in messages
    assert "Message 0" not in messages
    
    small_manager.close()


def test_log_without_request_id(log_manager):
    """
    Test logging without request ID.
    
    Requirements: 14.2 - Request ID is optional
    """
    log_manager.log(
        level="info",
        message="Message without request ID",
        event="event_1"
    )
    
    log_entry = log_manager.memory_logs[0]
    assert log_entry.request_id is None


def test_combined_filters(log_manager):
    """
    Test combining multiple filters.
    
    Requirements: 14.5 - Expose logs with filtering
    """
    # Add various logs
    log_manager.log(level="info", message="Msg 1", event="query_processed", request_id="req_123")
    log_manager.log(level="warning", message="Msg 2", event="query_processed", request_id="req_123")
    log_manager.log(level="info", message="Msg 3", event="api_called", request_id="req_123")
    log_manager.log(level="info", message="Msg 4", event="query_processed", request_id="req_456")
    
    # Query with multiple filters
    query = LogQuery(
        level="info",
        event="query_processed",
        request_id="req_123",
        limit=10
    )
    logs = log_manager.query_logs(query)
    
    # Should only match first log
    assert len(logs) == 1
    assert logs[0].message == "Msg 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
