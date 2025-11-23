"""
Integration tests for Query Scheduler with FastAPI

Tests the scheduler endpoints through the FastAPI application.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

# Note: These are integration tests that would require the full app to be running
# For now, we'll create basic structure tests


@pytest.mark.asyncio
async def test_scheduler_endpoints_exist():
    """
    Test that scheduler endpoints are defined.
    
    This is a basic smoke test to ensure endpoints are registered.
    """
    from main import app
    
    # Get all routes
    routes = [route.path for route in app.routes]
    
    # Verify scheduler endpoints exist
    assert "/api/schedule" in routes
    assert "/api/schedule/{schedule_id}" in routes
    
    print("✓ All scheduler endpoints are registered")


@pytest.mark.asyncio
async def test_scheduler_models_validation():
    """
    Test that scheduler models validate correctly.
    
    Requirements: 13.1 - Validate request models
    """
    from models import ScheduleRequest, ScheduleUpdateRequest
    
    # Test valid ScheduleRequest
    valid_request = ScheduleRequest(
        query="Test query for validation",
        cron_expression="0 * * * *",
        enabled=True,
        alert_on_change=True,
        max_sources=5
    )
    
    assert valid_request.query == "Test query for validation"
    assert valid_request.cron_expression == "0 * * * *"
    assert valid_request.enabled is True
    
    # Test ScheduleUpdateRequest
    update_request = ScheduleUpdateRequest(
        enabled=False,
        cron_expression="0 0 * * *"
    )
    
    assert update_request.enabled is False
    assert update_request.cron_expression == "0 0 * * *"
    
    print("✓ Scheduler models validate correctly")


@pytest.mark.asyncio
async def test_scheduler_initialization():
    """
    Test that scheduler can be initialized with required components.
    
    Requirements: 13.2 - Initialize scheduler
    """
    from scheduler import QueryScheduler
    from unittest.mock import Mock
    
    # Create mock components
    mock_orchestrator = Mock()
    mock_memory_store = Mock()
    mock_memory_store.client = Mock()
    mock_memory_store.client.scan_iter = Mock(return_value=[])
    
    # Initialize scheduler
    scheduler = QueryScheduler(
        agent_orchestrator=mock_orchestrator,
        memory_store=mock_memory_store
    )
    
    assert scheduler is not None
    assert scheduler.agent_orchestrator == mock_orchestrator
    assert scheduler.memory_store == mock_memory_store
    
    print("✓ Scheduler initializes correctly")


def test_schedule_request_validation():
    """
    Test ScheduleRequest validation rules.
    
    Requirements: 13.1 - Validate cron expressions and query length
    """
    from models import ScheduleRequest
    from pydantic import ValidationError
    
    # Test query length validation
    try:
        ScheduleRequest(
            query="short",  # Too short (< 10 chars)
            cron_expression="0 * * * *"
        )
        assert False, "Should have raised ValidationError for short query"
    except ValidationError as e:
        assert "at least 10 characters" in str(e).lower()
    
    # Test max_sources validation
    try:
        ScheduleRequest(
            query="This is a valid query length",
            cron_expression="0 * * * *",
            max_sources=15  # Too high (> 10)
        )
        assert False, "Should have raised ValidationError for max_sources > 10"
    except ValidationError as e:
        assert "less than or equal to 10" in str(e).lower()
    
    # Test valid request
    valid = ScheduleRequest(
        query="This is a valid query length",
        cron_expression="0 * * * *",
        max_sources=5
    )
    assert valid.max_sources == 5
    
    print("✓ ScheduleRequest validation works correctly")


@pytest.mark.asyncio
async def test_scheduler_lifecycle():
    """
    Test scheduler start and stop lifecycle.
    
    Requirements: 13.2 - Background execution lifecycle
    """
    from scheduler import QueryScheduler
    from unittest.mock import Mock
    
    # Create mock components
    mock_orchestrator = Mock()
    mock_memory_store = Mock()
    mock_memory_store.client = Mock()
    mock_memory_store.client.scan_iter = Mock(return_value=[])
    
    # Initialize and start scheduler
    scheduler = QueryScheduler(
        agent_orchestrator=mock_orchestrator,
        memory_store=mock_memory_store
    )
    
    await scheduler.start()
    assert scheduler.scheduler.running is True
    
    # Stop scheduler
    await scheduler.stop()
    assert scheduler.scheduler.running is False
    
    print("✓ Scheduler lifecycle (start/stop) works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
