"""
Tests for Alert Engine

Tests alert evaluation, deduplication, and channel sending.
"""
import pytest
import asyncio
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from alert_engine import AlertEngine, Alert
from models import ResearchSynthesis, APISource


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client"""
    client = MagicMock()
    client.call_claude = AsyncMock()
    return client


@pytest.fixture
def alert_engine(mock_mcp_client):
    """Create an AlertEngine instance with mock MCP client"""
    # Set console-only channel for testing
    os.environ["ALERT_CHANNELS"] = "console"
    engine = AlertEngine(mock_mcp_client)
    return engine


@pytest.fixture
def sample_synthesis():
    """Create a sample research synthesis"""
    return ResearchSynthesis(
        summary="Breaking news: Major AI breakthrough announced",
        detailed_analysis="Detailed analysis of the breakthrough",
        findings=[
            "New model achieves 95% accuracy",
            "Reduces training time by 50%",
            "Open source release planned"
        ],
        sources=["tech_api", "news_api"],
        source_details=[
            APISource(
                api_id="tech_api",
                api_name="Tech API",
                endpoint="/api/tech",
                verified=True
            )
        ],
        confidence_score=0.9,
        confidence_breakdown={"tech_api": 0.9}
    )


@pytest.mark.asyncio
async def test_alert_engine_initialization(mock_mcp_client):
    """Test alert engine initializes correctly"""
    os.environ["ALERT_CHANNELS"] = "console,file:/tmp/alerts.log"
    engine = AlertEngine(mock_mcp_client)
    
    assert engine.mcp_client == mock_mcp_client
    assert len(engine.alert_channels) == 2
    assert "console" in engine.alert_channels
    assert "file:/tmp/alerts.log" in engine.alert_channels
    assert len(engine.alert_history) == 0


@pytest.mark.asyncio
async def test_evaluate_triggers_alert(alert_engine, mock_mcp_client, sample_synthesis):
    """Test that evaluate triggers an alert for urgent information"""
    # Mock Claude response indicating alert should be triggered
    mock_mcp_client.call_claude.return_value = json.dumps({
        "should_alert": True,
        "severity": "high",
        "reasoning": "Breaking news about major AI breakthrough",
        "key_points": [
            "Significant technological advancement",
            "Time-sensitive information",
            "High impact on industry"
        ]
    })
    
    query = "What are the latest AI developments?"
    alert = await alert_engine.evaluate(query, sample_synthesis)
    
    assert alert is not None
    assert alert.severity == "high"
    assert alert.query == query
    assert len(alert.key_points) == 3
    assert alert.sources == sample_synthesis.sources
    assert len(alert_engine.alert_history) == 1


@pytest.mark.asyncio
async def test_evaluate_no_alert(alert_engine, mock_mcp_client, sample_synthesis):
    """Test that evaluate doesn't trigger alert for routine information"""
    # Mock Claude response indicating no alert needed
    mock_mcp_client.call_claude.return_value = json.dumps({
        "should_alert": False,
        "severity": "low",
        "reasoning": "Routine information, not time-sensitive",
        "key_points": []
    })
    
    query = "General AI information"
    alert = await alert_engine.evaluate(query, sample_synthesis)
    
    assert alert is None
    assert len(alert_engine.alert_history) == 0


@pytest.mark.asyncio
async def test_alert_deduplication(alert_engine, mock_mcp_client, sample_synthesis):
    """Test that duplicate alerts are suppressed"""
    # Mock Claude to always trigger alerts
    mock_mcp_client.call_claude.return_value = json.dumps({
        "should_alert": True,
        "severity": "high",
        "reasoning": "Important information",
        "key_points": ["Point 1", "Point 2"]
    })
    
    query = "AI breakthrough news"
    
    # First alert should trigger
    alert1 = await alert_engine.evaluate(query, sample_synthesis)
    assert alert1 is not None
    
    # Second identical alert should be suppressed
    alert2 = await alert_engine.evaluate(query, sample_synthesis)
    assert alert2 is None
    
    # Only one alert in history
    assert len(alert_engine.alert_history) == 1


@pytest.mark.asyncio
async def test_alert_deduplication_different_queries(alert_engine, mock_mcp_client, sample_synthesis):
    """Test that different queries trigger separate alerts"""
    # Mock Claude to always trigger alerts
    mock_mcp_client.call_claude.return_value = json.dumps({
        "should_alert": True,
        "severity": "medium",
        "reasoning": "Important information",
        "key_points": ["Point 1"]
    })
    
    # Two different queries
    alert1 = await alert_engine.evaluate("AI breakthrough", sample_synthesis)
    alert2 = await alert_engine.evaluate("Quantum computing news", sample_synthesis)
    
    assert alert1 is not None
    assert alert2 is not None
    assert len(alert_engine.alert_history) == 2


@pytest.mark.asyncio
async def test_send_console_alert(alert_engine, capsys):
    """Test sending alert to console"""
    alert = Alert(
        severity="high",
        title="Test Alert",
        message="This is a test alert",
        key_points=["Point 1", "Point 2"],
        sources=["source1", "source2"],
        timestamp=datetime.now(),
        query="test query"
    )
    
    await alert_engine._send_console(alert)
    
    captured = capsys.readouterr()
    assert "ALERT [HIGH]" in captured.out
    assert "Test Alert" in captured.out
    assert "Point 1" in captured.out
    assert "Point 2" in captured.out


@pytest.mark.asyncio
async def test_send_file_alert(alert_engine):
    """Test sending alert to file"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_file = f.name
    
    try:
        alert = Alert(
            severity="medium",
            title="File Test Alert",
            message="Testing file output",
            key_points=["File point 1"],
            sources=["file_source"],
            timestamp=datetime.now(),
            query="file test query"
        )
        
        await alert_engine._send_file(alert, temp_file)
        
        # Read and verify file contents
        with open(temp_file, 'r') as f:
            content = f.read()
            assert "File Test Alert" in content
            assert "medium" in content
            assert "file_source" in content
    
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.mark.asyncio
async def test_text_similarity(alert_engine):
    """Test text similarity calculation"""
    # Identical text
    sim1 = alert_engine._text_similarity("hello world", "hello world")
    assert sim1 == 1.0
    
    # Completely different
    sim2 = alert_engine._text_similarity("hello world", "foo bar")
    assert sim2 == 0.0
    
    # Partial overlap
    sim3 = alert_engine._text_similarity("hello world test", "hello world example")
    assert 0.0 < sim3 < 1.0


@pytest.mark.asyncio
async def test_cleanup_history(alert_engine):
    """Test that old alerts are cleaned up from history"""
    # Add some old alerts
    old_alert = Alert(
        severity="low",
        title="Old Alert",
        message="Old message",
        key_points=[],
        sources=[],
        timestamp=datetime.now() - timedelta(hours=2),
        query="old query"
    )
    
    recent_alert = Alert(
        severity="low",
        title="Recent Alert",
        message="Recent message",
        key_points=[],
        sources=[],
        timestamp=datetime.now(),
        query="recent query"
    )
    
    alert_engine.alert_history = [old_alert, recent_alert]
    alert_engine._cleanup_history()
    
    # Old alert should be removed (deduplication window is 1 hour)
    assert len(alert_engine.alert_history) == 1
    assert alert_engine.alert_history[0].title == "Recent Alert"


@pytest.mark.asyncio
async def test_get_alert_stats(alert_engine):
    """Test getting alert statistics"""
    # Add some test alerts
    for severity in ["low", "medium", "high", "critical"]:
        alert = Alert(
            severity=severity,
            title=f"{severity} alert",
            message="test",
            key_points=[],
            sources=[],
            timestamp=datetime.now(),
            query="test"
        )
        alert_engine.alert_history.append(alert)
    
    stats = alert_engine.get_alert_stats()
    
    assert stats["total_alerts_24h"] == 4
    assert stats["severity_breakdown"]["low"] == 1
    assert stats["severity_breakdown"]["medium"] == 1
    assert stats["severity_breakdown"]["high"] == 1
    assert stats["severity_breakdown"]["critical"] == 1
    assert stats["channels_configured"] == 1  # console only in fixture


@pytest.mark.asyncio
async def test_parse_json_with_markdown(alert_engine):
    """Test parsing JSON from markdown code blocks"""
    # JSON in markdown code block
    response1 = '''```json
{
    "should_alert": true,
    "severity": "high",
    "reasoning": "test",
    "key_points": ["point1"]
}
```'''
    
    result1 = alert_engine._parse_json_response(response1)
    assert result1["should_alert"] is True
    assert result1["severity"] == "high"
    
    # Plain JSON
    response2 = '{"should_alert": false, "severity": "low", "reasoning": "test", "key_points": []}'
    result2 = alert_engine._parse_json_response(response2)
    assert result2["should_alert"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
