"""
Test for Task 15: Integration of alerts and reports into query processing

This test verifies that:
1. Agent orchestrator calls alert engine after synthesis
2. Agent orchestrator generates reports when requested
3. API response includes alert status and report path

Requirements: 5.1, 6.1, 12.1
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from agent_orchestrator import (
    AgentOrchestrator,
    ResearchResult,
    ResearchSynthesis,
    QueryIntent,
    APIResult
)
from alert_engine import Alert, AlertEngine
from report_generator import ReportGenerator, ReportPath
from memory_store import MemoryEntry


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client"""
    client = Mock()
    client.call_claude = AsyncMock(return_value='{"intent_type": "test", "key_topics": ["test"], "search_terms": ["test"], "context": "test"}')
    client.discover_apis = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_memory_store():
    """Create mock memory store"""
    store = Mock()
    store.find_similar = AsyncMock(return_value=[])
    store.store = AsyncMock(return_value="memory_123")
    return store


@pytest.fixture
def mock_alert_engine():
    """Create mock alert engine"""
    engine = Mock(spec=AlertEngine)
    engine.evaluate = AsyncMock(return_value=None)
    return engine


@pytest.fixture
def mock_report_generator():
    """Create mock report generator"""
    generator = Mock(spec=ReportGenerator)
    generator.generate = AsyncMock(return_value=ReportPath(
        filename="test_report.md",
        full_path="/reports/test_report.md",
        timestamp="2025-11-22_12-00-00",
        report_id="report_123"
    ))
    return generator


@pytest.fixture
def agent_orchestrator(mock_mcp_client, mock_memory_store, mock_alert_engine, mock_report_generator):
    """Create agent orchestrator with mocked dependencies"""
    return AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store,
        alert_engine=mock_alert_engine,
        report_generator=mock_report_generator
    )


@pytest.mark.asyncio
async def test_alert_engine_called_after_synthesis(agent_orchestrator, mock_alert_engine):
    """
    Test that alert engine is called after synthesis when alert_enabled=True
    
    Requirements: 5.1 - Analyze gathered information for urgency
    """
    # Mock the internal methods to avoid full processing
    agent_orchestrator._parse_intent = AsyncMock(return_value=QueryIntent(
        original_query="test query",
        intent_type="test",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    ))
    agent_orchestrator._get_embedding = AsyncMock(return_value=[0.0] * 1024)
    agent_orchestrator._discover_apis = AsyncMock(return_value=[])
    agent_orchestrator._gather_information = AsyncMock(return_value=[])
    agent_orchestrator._synthesize_results = AsyncMock(return_value=ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1"],
        sources=[],
        source_details=[],
        confidence_score=0.8,
        confidence_breakdown={}
    ))
    
    # Process query with alerts enabled
    result = await agent_orchestrator.process_query(
        query="test query",
        alert_enabled=True,
        include_report=False
    )
    
    # Verify alert engine was called
    mock_alert_engine.evaluate.assert_called_once()
    call_args = mock_alert_engine.evaluate.call_args
    assert call_args[1]["query"] == "test query"
    assert isinstance(call_args[1]["synthesis"], ResearchSynthesis)


@pytest.mark.asyncio
async def test_alert_engine_not_called_when_disabled(agent_orchestrator, mock_alert_engine):
    """
    Test that alert engine is NOT called when alert_enabled=False
    """
    # Mock the internal methods
    agent_orchestrator._parse_intent = AsyncMock(return_value=QueryIntent(
        original_query="test query",
        intent_type="test",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    ))
    agent_orchestrator._get_embedding = AsyncMock(return_value=[0.0] * 1024)
    agent_orchestrator._discover_apis = AsyncMock(return_value=[])
    agent_orchestrator._gather_information = AsyncMock(return_value=[])
    agent_orchestrator._synthesize_results = AsyncMock(return_value=ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1"],
        sources=[],
        source_details=[],
        confidence_score=0.8,
        confidence_breakdown={}
    ))
    
    # Process query with alerts disabled
    result = await agent_orchestrator.process_query(
        query="test query",
        alert_enabled=False,
        include_report=False
    )
    
    # Verify alert engine was NOT called
    mock_alert_engine.evaluate.assert_not_called()
    assert result.alert is None


@pytest.mark.asyncio
async def test_report_generator_called_when_requested(agent_orchestrator, mock_report_generator):
    """
    Test that report generator is called when include_report=True
    
    Requirements: 6.1 - Generate Research_Report documents
    """
    # Mock the internal methods
    agent_orchestrator._parse_intent = AsyncMock(return_value=QueryIntent(
        original_query="test query",
        intent_type="test",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    ))
    agent_orchestrator._get_embedding = AsyncMock(return_value=[0.0] * 1024)
    agent_orchestrator._discover_apis = AsyncMock(return_value=[])
    agent_orchestrator._gather_information = AsyncMock(return_value=[])
    agent_orchestrator._synthesize_results = AsyncMock(return_value=ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1"],
        sources=[],
        source_details=[],
        confidence_score=0.8,
        confidence_breakdown={}
    ))
    
    # Process query with report generation enabled
    result = await agent_orchestrator.process_query(
        query="test query",
        alert_enabled=False,
        include_report=True
    )
    
    # Verify report generator was called
    mock_report_generator.generate.assert_called_once()
    call_args = mock_report_generator.generate.call_args
    assert call_args[1]["query"] == "test query"
    assert isinstance(call_args[1]["synthesis"], ResearchSynthesis)
    
    # Verify result includes report path
    assert result.report_path is not None
    assert result.report_path.full_path == "/reports/test_report.md"


@pytest.mark.asyncio
async def test_report_generator_not_called_when_disabled(agent_orchestrator, mock_report_generator):
    """
    Test that report generator is NOT called when include_report=False
    """
    # Mock the internal methods
    agent_orchestrator._parse_intent = AsyncMock(return_value=QueryIntent(
        original_query="test query",
        intent_type="test",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    ))
    agent_orchestrator._get_embedding = AsyncMock(return_value=[0.0] * 1024)
    agent_orchestrator._discover_apis = AsyncMock(return_value=[])
    agent_orchestrator._gather_information = AsyncMock(return_value=[])
    agent_orchestrator._synthesize_results = AsyncMock(return_value=ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1"],
        sources=[],
        source_details=[],
        confidence_score=0.8,
        confidence_breakdown={}
    ))
    
    # Process query with report generation disabled
    result = await agent_orchestrator.process_query(
        query="test query",
        alert_enabled=False,
        include_report=False
    )
    
    # Verify report generator was NOT called
    mock_report_generator.generate.assert_not_called()
    assert result.report_path is None


@pytest.mark.asyncio
async def test_alert_triggered_included_in_result(agent_orchestrator, mock_alert_engine):
    """
    Test that alert status is included in research result
    
    Requirements: 12.1 - Include alert status in API response
    """
    # Mock alert engine to return an alert
    mock_alert = Alert(
        severity="high",
        title="Test Alert",
        message="This is a test alert",
        key_points=["Point 1", "Point 2"],
        sources=["source1"],
        timestamp=datetime.now(),
        query="test query"
    )
    mock_alert_engine.evaluate = AsyncMock(return_value=mock_alert)
    
    # Mock the internal methods
    agent_orchestrator._parse_intent = AsyncMock(return_value=QueryIntent(
        original_query="test query",
        intent_type="test",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    ))
    agent_orchestrator._get_embedding = AsyncMock(return_value=[0.0] * 1024)
    agent_orchestrator._discover_apis = AsyncMock(return_value=[])
    agent_orchestrator._gather_information = AsyncMock(return_value=[])
    agent_orchestrator._synthesize_results = AsyncMock(return_value=ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1"],
        sources=[],
        source_details=[],
        confidence_score=0.8,
        confidence_breakdown={}
    ))
    
    # Process query
    result = await agent_orchestrator.process_query(
        query="test query",
        alert_enabled=True,
        include_report=False
    )
    
    # Verify alert is included in result
    assert result.alert is not None
    assert result.alert.severity == "high"
    assert result.alert.title == "Test Alert"


@pytest.mark.asyncio
async def test_report_generation_failure_does_not_crash(agent_orchestrator, mock_report_generator):
    """
    Test that report generation failure doesn't crash the query processing
    """
    # Mock report generator to raise an exception
    mock_report_generator.generate = AsyncMock(side_effect=Exception("Report generation failed"))
    
    # Mock the internal methods
    agent_orchestrator._parse_intent = AsyncMock(return_value=QueryIntent(
        original_query="test query",
        intent_type="test",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    ))
    agent_orchestrator._get_embedding = AsyncMock(return_value=[0.0] * 1024)
    agent_orchestrator._discover_apis = AsyncMock(return_value=[])
    agent_orchestrator._gather_information = AsyncMock(return_value=[])
    agent_orchestrator._synthesize_results = AsyncMock(return_value=ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1"],
        sources=[],
        source_details=[],
        confidence_score=0.8,
        confidence_breakdown={}
    ))
    
    # Process query - should not raise exception
    result = await agent_orchestrator.process_query(
        query="test query",
        alert_enabled=False,
        include_report=True
    )
    
    # Verify query completed successfully despite report failure
    assert result is not None
    assert result.report_path is None  # Report failed, so path should be None


@pytest.mark.asyncio
async def test_both_alert_and_report_can_be_generated(agent_orchestrator, mock_alert_engine, mock_report_generator):
    """
    Test that both alert and report can be generated in the same query
    
    Requirements: 5.1, 6.1, 12.1
    """
    # Mock alert engine to return an alert
    mock_alert = Alert(
        severity="medium",
        title="Test Alert",
        message="This is a test alert",
        key_points=["Point 1"],
        sources=["source1"],
        timestamp=datetime.now(),
        query="test query"
    )
    mock_alert_engine.evaluate = AsyncMock(return_value=mock_alert)
    
    # Mock the internal methods
    agent_orchestrator._parse_intent = AsyncMock(return_value=QueryIntent(
        original_query="test query",
        intent_type="test",
        key_topics=["test"],
        search_terms=["test"],
        context="test"
    ))
    agent_orchestrator._get_embedding = AsyncMock(return_value=[0.0] * 1024)
    agent_orchestrator._discover_apis = AsyncMock(return_value=[])
    agent_orchestrator._gather_information = AsyncMock(return_value=[])
    agent_orchestrator._synthesize_results = AsyncMock(return_value=ResearchSynthesis(
        summary="Test summary",
        detailed_analysis="Test analysis",
        findings=["Finding 1"],
        sources=[],
        source_details=[],
        confidence_score=0.8,
        confidence_breakdown={}
    ))
    
    # Process query with both enabled
    result = await agent_orchestrator.process_query(
        query="test query",
        alert_enabled=True,
        include_report=True
    )
    
    # Verify both alert and report are in result
    assert result.alert is not None
    assert result.alert.severity == "medium"
    assert result.report_path is not None
    assert result.report_path.full_path == "/reports/test_report.md"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
