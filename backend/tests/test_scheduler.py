"""
Tests for Query Scheduler

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""
import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from scheduler import QueryScheduler, ScheduledQuery, SchedulerError
from agent_orchestrator import AgentOrchestrator, ResearchResult, ResearchSynthesis, QueryIntent
from memory_store import MemoryStore


@pytest.fixture
def mock_memory_store():
    """Create mock memory store"""
    store = Mock(spec=MemoryStore)
    store.client = Mock()
    store.client.set = Mock()
    store.client.get = Mock(return_value=None)
    store.client.delete = Mock()
    store.client.scan_iter = Mock(return_value=[])
    return store


@pytest.fixture
def mock_agent_orchestrator():
    """Create mock agent orchestrator"""
    orchestrator = Mock(spec=AgentOrchestrator)
    
    # Create a mock result
    mock_synthesis = ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1", "Finding 2"],
        sources=["api1", "api2"],
        source_details=[],
        confidence_score=0.85,
        confidence_breakdown={}
    )
    
    mock_intent = QueryIntent(
        original_query="test query",
        intent_type="factual",
        key_topics=["test"],
        search_terms=["test"],
        context="test context"
    )
    
    mock_result = ResearchResult(
        query_id="test_query_id",
        query="test query",
        intent=mock_intent,
        synthesis=mock_synthesis,
        similar_queries=[],
        api_results=[],
        processing_time_ms=1000.0,
        memory_id="test_memory_id",
        refined_query=None,
        alert=None,
        report_path=None
    )
    
    orchestrator.process_query = AsyncMock(return_value=mock_result)
    
    return orchestrator


@pytest_asyncio.fixture
async def scheduler(mock_agent_orchestrator, mock_memory_store):
    """Create scheduler instance"""
    scheduler = QueryScheduler(
        agent_orchestrator=mock_agent_orchestrator,
        memory_store=mock_memory_store
    )
    await scheduler.start()
    yield scheduler
    await scheduler.stop()


@pytest.mark.asyncio
async def test_create_schedule(scheduler):
    """
    Test creating a scheduled query.
    
    Requirements: 13.1 - Accept scheduled queries with cron-like expressions
    """
    # Create schedule
    schedule = await scheduler.create_schedule(
        query="What are the latest AI trends?",
        cron_expression="0 * * * *",  # Every hour
        enabled=True,
        alert_on_change=True,
        max_sources=5
    )
    
    # Verify schedule was created
    assert schedule.schedule_id is not None
    assert schedule.query == "What are the latest AI trends?"
    assert schedule.cron_expression == "0 * * * *"
    assert schedule.enabled is True
    assert schedule.alert_on_change is True
    assert schedule.max_sources == 5
    assert schedule.execution_count == 0


@pytest.mark.asyncio
async def test_create_schedule_invalid_cron(scheduler):
    """
    Test creating schedule with invalid cron expression.
    
    Requirements: 13.1 - Validate cron expressions
    """
    # Try to create schedule with invalid cron
    with pytest.raises(SchedulerError) as exc_info:
        await scheduler.create_schedule(
            query="Test query",
            cron_expression="invalid cron",
            enabled=True
        )
    
    assert "Invalid cron expression" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_schedules(scheduler):
    """
    Test listing all schedules.
    
    Requirements: 13.6 - Allow users to view scheduled queries
    """
    # Create multiple schedules
    await scheduler.create_schedule(
        query="Query 1",
        cron_expression="0 * * * *",
        enabled=True
    )
    
    await scheduler.create_schedule(
        query="Query 2",
        cron_expression="0 0 * * *",
        enabled=False
    )
    
    # List schedules
    schedules = await scheduler.list_schedules()
    
    # Verify
    assert len(schedules) == 2
    assert any(s.query == "Query 1" for s in schedules)
    assert any(s.query == "Query 2" for s in schedules)


@pytest.mark.asyncio
async def test_get_schedule(scheduler):
    """
    Test getting a specific schedule.
    
    Requirements: 13.6 - Allow users to view scheduled queries
    """
    # Create schedule
    created = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",
        enabled=True
    )
    
    # Get schedule
    retrieved = await scheduler.get_schedule(created.schedule_id)
    
    # Verify
    assert retrieved is not None
    assert retrieved.schedule_id == created.schedule_id
    assert retrieved.query == created.query


@pytest.mark.asyncio
async def test_update_schedule(scheduler):
    """
    Test updating a scheduled query.
    
    Requirements: 13.6 - Allow users to enable/disable/modify scheduled queries
    """
    # Create schedule
    schedule = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",
        enabled=True,
        alert_on_change=True
    )
    
    # Update schedule
    updated = await scheduler.update_schedule(
        schedule_id=schedule.schedule_id,
        enabled=False,
        cron_expression="0 0 * * *",
        alert_on_change=False
    )
    
    # Verify
    assert updated.enabled is False
    assert updated.cron_expression == "0 0 * * *"
    assert updated.alert_on_change is False


@pytest.mark.asyncio
async def test_delete_schedule(scheduler):
    """
    Test deleting a scheduled query.
    
    Requirements: 13.6 - Allow users to delete scheduled queries
    """
    # Create schedule
    schedule = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",
        enabled=True
    )
    
    # Delete schedule
    success = await scheduler.delete_schedule(schedule.schedule_id)
    
    # Verify
    assert success is True
    
    # Verify schedule is gone
    retrieved = await scheduler.get_schedule(schedule.schedule_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_nonexistent_schedule(scheduler):
    """Test deleting a schedule that doesn't exist."""
    success = await scheduler.delete_schedule("nonexistent_id")
    assert success is False


@pytest.mark.asyncio
async def test_execute_scheduled_query(scheduler, mock_agent_orchestrator):
    """
    Test executing a scheduled query.
    
    Requirements:
    - 13.2: Execute scheduled queries in background
    - 13.5: Generate reports for scheduled queries
    """
    # Create schedule
    schedule = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",
        enabled=True,
        alert_on_change=True,
        max_sources=3
    )
    
    # Execute the scheduled query manually
    await scheduler._execute_scheduled_query(schedule.schedule_id)
    
    # Verify agent orchestrator was called
    mock_agent_orchestrator.process_query.assert_called_once()
    call_args = mock_agent_orchestrator.process_query.call_args
    
    assert call_args.kwargs["query"] == "Test query"
    assert call_args.kwargs["max_sources"] == 3
    assert call_args.kwargs["include_report"] is True
    assert call_args.kwargs["alert_enabled"] is True
    
    # Verify schedule metadata was updated
    updated_schedule = await scheduler.get_schedule(schedule.schedule_id)
    assert updated_schedule.execution_count == 1
    assert updated_schedule.last_run is not None
    assert updated_schedule.last_result_hash is not None


@pytest.mark.asyncio
async def test_change_detection(scheduler, mock_agent_orchestrator):
    """
    Test change detection between executions.
    
    Requirements: 13.3 - Compare new results with previous executions
    """
    # Create schedule
    schedule = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",
        enabled=True,
        alert_on_change=True
    )
    
    # Execute first time
    await scheduler._execute_scheduled_query(schedule.schedule_id)
    first_hash = (await scheduler.get_schedule(schedule.schedule_id)).last_result_hash
    
    # Execute second time (same result)
    await scheduler._execute_scheduled_query(schedule.schedule_id)
    second_hash = (await scheduler.get_schedule(schedule.schedule_id)).last_result_hash
    
    # Hashes should be the same since mock returns same result
    assert first_hash == second_hash
    
    # Verify execution count increased
    updated_schedule = await scheduler.get_schedule(schedule.schedule_id)
    assert updated_schedule.execution_count == 2


@pytest.mark.asyncio
async def test_get_next_run_time(scheduler):
    """
    Test getting next run time for a schedule.
    
    Requirements: 13.1 - Schedule queries with cron expressions
    """
    # Create enabled schedule
    schedule = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",  # Every hour
        enabled=True
    )
    
    # Get next run time
    next_run = scheduler.get_next_run_time(schedule.schedule_id)
    
    # Verify next run time exists
    assert next_run is not None
    
    # Create disabled schedule
    disabled_schedule = await scheduler.create_schedule(
        query="Disabled query",
        cron_expression="0 * * * *",
        enabled=False
    )
    
    # Get next run time for disabled schedule
    next_run_disabled = scheduler.get_next_run_time(disabled_schedule.schedule_id)
    
    # Should be None since schedule is disabled
    assert next_run_disabled is None


@pytest.mark.asyncio
async def test_scheduler_persistence(mock_agent_orchestrator, mock_memory_store):
    """
    Test that schedules are persisted to Redis.
    
    Requirements: 13.6 - Store scheduled queries
    """
    scheduler = QueryScheduler(
        agent_orchestrator=mock_agent_orchestrator,
        memory_store=mock_memory_store
    )
    await scheduler.start()
    
    # Create schedule
    schedule = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",
        enabled=True
    )
    
    # Verify Redis set was called
    mock_memory_store.client.set.assert_called()
    
    # Verify key format
    call_args = mock_memory_store.client.set.call_args
    key = call_args[0][0]
    assert key.startswith("schedule:")
    assert schedule.schedule_id in key
    
    await scheduler.stop()


@pytest.mark.asyncio
async def test_update_schedule_invalid_cron(scheduler):
    """Test updating schedule with invalid cron expression."""
    # Create schedule
    schedule = await scheduler.create_schedule(
        query="Test query",
        cron_expression="0 * * * *",
        enabled=True
    )
    
    # Try to update with invalid cron
    with pytest.raises(SchedulerError) as exc_info:
        await scheduler.update_schedule(
            schedule_id=schedule.schedule_id,
            cron_expression="invalid cron"
        )
    
    assert "Invalid cron expression" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_nonexistent_schedule(scheduler):
    """Test updating a schedule that doesn't exist."""
    with pytest.raises(SchedulerError) as exc_info:
        await scheduler.update_schedule(
            schedule_id="nonexistent_id",
            enabled=False
        )
    
    assert "not found" in str(exc_info.value).lower()
