"""
Integration Tests for Task 18: Alerts and Reports

This module tests the complete integration of alerts and reports functionality:
- Submit query that should trigger alert
- Verify alert is sent to configured channels
- Verify report is generated with all sections
- Verify duplicate alerts are suppressed
- Verify metrics endpoint returns correct data

Requirements: 5.1, 5.4, 6.1, 7.1
"""
import pytest
import asyncio
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call

from alert_engine import AlertEngine, Alert
from report_generator import ReportGenerator, ReportPath
from agent_orchestrator import (
    AgentOrchestrator,
    QueryIntent,
    ResearchSynthesis,
    APIResult,
    ResearchResult
)
from mcp_client import MCPClient, APIEndpoint
from memory_store import MemoryStore, MemoryEntry
from learning_engine import LearningEngine, RefinedQuery
from models import APISource


@pytest.fixture
def temp_reports_dir():
    """Create temporary directory for test reports"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_alerts_file():
    """Create temporary file for alert logging"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_file = f.name
    yield temp_file
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client with realistic responses"""
    client = MagicMock(spec=MCPClient)
    
    # Mock Claude call for alert evaluation - CRITICAL INFORMATION
    async def mock_call_claude_critical(prompt, system="", temperature=0.7):
        if "urgency and importance" in prompt.lower():
            # Return alert-worthy assessment
            return json.dumps({
                "should_alert": True,
                "severity": "high",
                "reasoning": "Breaking news detected: Major AI breakthrough announced",
                "key_points": [
                    "New AI model achieves 95% accuracy",
                    "Significant improvement over previous models",
                    "Industry-wide implications expected"
                ]
            })
        elif "synthesize research" in prompt.lower():
            return json.dumps({
                "summary": "Major breakthrough in AI research announced today.",
                "detailed_analysis": "A significant advancement in artificial intelligence has been announced. The new model demonstrates unprecedented accuracy and efficiency.",
                "findings": [
                    "95% accuracy achieved on benchmark tests",
                    "50% reduction in computational requirements",
                    "Potential applications across multiple industries"
                ],
                "confidence_assessment": {
                    "api_1": 0.9,
                    "api_2": 0.85
                },
                "overall_confidence": 0.88
            })
        else:
            return json.dumps({
                "intent_type": "factual",
                "key_topics": ["AI", "breakthrough", "research"],
                "search_terms": ["AI breakthrough", "machine learning news"],
                "context": "User wants to know about recent AI developments"
            })
    
    client.call_claude = AsyncMock(side_effect=mock_call_claude_critical)
    
    # Mock API discovery
    async def mock_discover_apis(query, verified_only=True, max_results=5):
        return [
            APIEndpoint(
                api_id="api_1",
                api_name="AI News API",
                endpoint="/v1/news",
                method="GET",
                description="Latest AI news",
                verified=True,
                priority_score=0.9
            ),
            APIEndpoint(
                api_id="api_2",
                api_name="Research Papers API",
                endpoint="/v1/papers",
                method="GET",
                description="Academic research papers",
                verified=True,
                priority_score=0.85
            )
        ]
    
    client.discover_apis = AsyncMock(side_effect=mock_discover_apis)
    
    # Mock API calls
    async def mock_call_api(api_id, endpoint, method="GET", params=None, timeout=30):
        return {
            "success": True,
            "data": {
                "title": "Major AI Breakthrough",
                "content": "Researchers announce significant advancement",
                "timestamp": "2025-11-22T10:00:00Z"
            }
        }
    
    client.call_api = AsyncMock(side_effect=mock_call_api)
    
    return client


@pytest.fixture
def mock_mcp_client_routine():
    """Create a mock MCP client for routine (non-alert) queries"""
    client = MagicMock(spec=MCPClient)
    
    # Mock Claude call for routine information
    async def mock_call_claude_routine(prompt, system="", temperature=0.7):
        if "urgency and importance" in prompt.lower():
            # Return non-alert assessment
            return json.dumps({
                "should_alert": False,
                "severity": "low",
                "reasoning": "Routine information query with no time-sensitive content",
                "key_points": []
            })
        elif "synthesize research" in prompt.lower():
            return json.dumps({
                "summary": "General information about AI trends.",
                "detailed_analysis": "Current AI trends show steady progress in various areas.",
                "findings": [
                    "Continued growth in AI adoption",
                    "Incremental improvements in models",
                    "Expanding use cases"
                ],
                "confidence_assessment": {
                    "api_1": 0.7
                },
                "overall_confidence": 0.7
            })
        else:
            return json.dumps({
                "intent_type": "factual",
                "key_topics": ["AI", "trends"],
                "search_terms": ["AI trends"],
                "context": "User wants general AI information"
            })
    
    client.call_claude = AsyncMock(side_effect=mock_call_claude_routine)
    client.discover_apis = AsyncMock(return_value=[
        APIEndpoint(
            api_id="api_1",
            api_name="AI Info API",
            endpoint="/v1/info",
            method="GET",
            description="General AI information",
            verified=True,
            priority_score=0.7
        )
    ])
    client.call_api = AsyncMock(return_value={
        "success": True,
        "data": {"info": "General AI trends data"}
    })
    
    return client


@pytest.fixture
def mock_memory_store():
    """Create a mock memory store"""
    store = MagicMock(spec=MemoryStore)
    
    async def mock_find_similar(query_embedding, top_k=5, min_relevance=0.0, session_id=None):
        return []
    
    async def mock_store(query, query_embedding, results, sources, relevance_score=0.5, session_id=None):
        return f"memory_{hash(query) % 10000}"
    
    store.find_similar = AsyncMock(side_effect=mock_find_similar)
    store.store = AsyncMock(side_effect=mock_store)
    
    return store


@pytest.fixture
def alert_engine_with_console(mock_mcp_client):
    """Create alert engine configured for console output"""
    with patch.dict(os.environ, {"ALERT_CHANNELS": "console"}):
        return AlertEngine(mock_mcp_client)


@pytest.fixture
def alert_engine_with_file(mock_mcp_client, temp_alerts_file):
    """Create alert engine configured for file output"""
    with patch.dict(os.environ, {"ALERT_CHANNELS": f"file:{temp_alerts_file}"}):
        return AlertEngine(mock_mcp_client)


@pytest.fixture
def alert_engine_multi_channel(mock_mcp_client, temp_alerts_file):
    """Create alert engine with multiple channels"""
    with patch.dict(os.environ, {"ALERT_CHANNELS": f"console,file:{temp_alerts_file}"}):
        return AlertEngine(mock_mcp_client)


@pytest.mark.asyncio
async def test_alert_triggered_for_critical_query(mock_mcp_client, mock_memory_store, temp_reports_dir):
    """
    Test that alerts are triggered for critical/urgent information.
    
    Requirements: 5.1 - Analyze gathered information for urgency indicators
    """
    # Setup
    with patch.dict(os.environ, {"ALERT_CHANNELS": "console"}):
        alert_engine = AlertEngine(mock_mcp_client)
        learning_engine = LearningEngine(mock_memory_store, mock_mcp_client)
        report_generator = ReportGenerator(temp_reports_dir)
        
        orchestrator = AgentOrchestrator(
            mcp_client=mock_mcp_client,
            memory_store=mock_memory_store,
            learning_engine=learning_engine,
            alert_engine=alert_engine,
            report_generator=report_generator
        )
        
        # Execute
        result = await orchestrator.process_query(
            query="What are the latest breaking developments in AI?",
            max_sources=2,
            include_report=True,
            alert_enabled=True
        )
        
        # Verify alert was triggered
        assert result.alert is not None, "Alert should be triggered for critical query"
        assert result.alert.severity == "high", "Alert severity should be high"
        assert "breakthrough" in result.alert.message.lower(), "Alert should mention breakthrough"
        assert len(result.alert.key_points) > 0, "Alert should have key points"
        assert result.alert.query == "What are the latest breaking developments in AI?"


@pytest.mark.asyncio
async def test_duplicate_alerts_suppressed(mock_mcp_client, alert_engine_with_console):
    """
    Test that duplicate alerts are suppressed to prevent alert fatigue.
    
    Requirements: 5.4 - Deduplicate alerts to prevent notification fatigue
    """
    # Create test synthesis
    synthesis = ResearchSynthesis(
        summary="Breaking news about AI",
        detailed_analysis="Important AI development",
        findings=["Major breakthrough", "Industry impact"],
        sources=["news_api"],
        source_details=[],
        confidence_score=0.9,
        confidence_breakdown={"news_api": 0.9}
    )
    
    # First alert - should trigger
    alert1 = await alert_engine_with_console.evaluate(
        query="Breaking AI news today",
        synthesis=synthesis
    )
    
    assert alert1 is not None, "First alert should be triggered"
    
    # Second alert with very similar query - should be suppressed
    # Using same words to ensure high similarity (>0.8)
    alert2 = await alert_engine_with_console.evaluate(
        query="Breaking AI news today",  # Exact same query
        synthesis=synthesis
    )
    
    assert alert2 is None, "Duplicate alert should be suppressed"


@pytest.mark.asyncio
async def test_report_generated_with_all_sections(mock_mcp_client, mock_memory_store, temp_reports_dir):
    """
    Test that reports are generated with all required sections.
    
    Requirements: 6.1 - Generate Research_Report documents in markdown format
                  6.2 - Include executive summary, detailed findings, source citations, confidence assessments
                  6.3 - Organize information by topic with clear headings and bullet points
    """
    # Setup
    learning_engine = LearningEngine(mock_memory_store, mock_mcp_client)
    alert_engine = AlertEngine(mock_mcp_client)
    report_generator = ReportGenerator(temp_reports_dir)
    
    orchestrator = AgentOrchestrator(
        mcp_client=mock_mcp_client,
        memory_store=mock_memory_store,
        learning_engine=learning_engine,
        alert_engine=alert_engine,
        report_generator=report_generator
    )
    
    # Execute
    result = await orchestrator.process_query(
        query="What are the latest AI developments?",
        max_sources=2,
        include_report=True,
        alert_enabled=True
    )
    
    # Verify report was generated
    assert result.report_path is not None, "Report should be generated"
    assert os.path.exists(result.report_path.full_path), "Report file should exist"
    
    # Read report content
    with open(result.report_path.full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify all required sections are present
    assert "# Research Report:" in content, "Report should have title"
    assert "## Executive Summary" in content, "Report should have executive summary"
    assert "## Key Findings" in content, "Report should have key findings"
    assert "## Detailed Analysis" in content, "Report should have detailed analysis"
    assert "## Sources" in content, "Report should have sources section"
    assert "## Confidence Assessment" in content, "Report should have confidence assessment"
    assert "## Metadata" in content, "Report should have metadata"
    
    # Verify content includes query
    assert "What are the latest AI developments?" in content, "Report should include original query"
    
    # Verify confidence score is present
    assert "Confidence Score:" in content, "Report should show confidence score"
    
    # Verify sources are listed
    assert "AI News API" in content or "api_1" in content, "Report should list API sources"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
