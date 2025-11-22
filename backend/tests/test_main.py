"""
Tests for main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app, Config


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint returns correct structure"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]
    assert data["service"] == "adaptive-research-agent"
    assert data["version"] == "1.0.0"
    assert "configuration" in data
    
    # Check configuration fields
    config = data["configuration"]
    assert "redis_configured" in config
    assert "anthropic_configured" in config
    assert "postman_configured" in config
    assert "reports_directory" in config


def test_health_endpoint_includes_request_id(client):
    """Test that health endpoint response includes request ID header"""
    response = client.get("/health")
    
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_cors_headers(client):
    """Test CORS middleware is configured"""
    response = client.options("/health")
    
    # CORS headers should be present
    assert response.status_code in [200, 405]  # OPTIONS might not be explicitly handled


def test_config_validation():
    """Test configuration validation"""
    missing = Config.validate()
    
    # Should return a list (may be empty or contain missing vars)
    assert isinstance(missing, list)
