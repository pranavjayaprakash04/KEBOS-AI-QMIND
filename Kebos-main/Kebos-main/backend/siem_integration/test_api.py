import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch
from datetime import datetime
from backend.siem_integration.api import router, authenticate
from backend.siem_integration.models import SIEMEvent, SIEMConfig, SIEMQuery, SIEMType, SIEMAuthType

# Create a test app with just the SIEM router
app = FastAPI()
app.include_router(router, prefix="/siem")

# Mock the authentication dependency
def mock_get_current_user():
    return {"user_id": "test_user", "username": "test"}

# Override the authentication dependency
app.dependency_overrides[authenticate] = mock_get_current_user

client = TestClient(app)

def test_read_siem_configs():
    """Test GET /siem/configs endpoint"""
    with patch('backend.siem_integration.api.siem_service.list_siem_configs') as mock_list:
        mock_list.return_value = []
        response = client.get("/siem/api/v1/siem/configs")
        assert response.status_code == 200
        assert response.json() == []

def test_create_siem_config():
    """Test POST /siem/config endpoint"""
    config_data = {
        "id": "test-siem-1",
        "name": "Test SIEM",
        "siem_type": "splunk",
        "base_url": "https://test-siem.example.com",
        "auth_type": "api_key"
    }
    
    with patch('backend.siem_integration.api.siem_service.add_siem_config') as mock_add:
        mock_add.return_value = "test-siem-1"
        response = client.post("/siem/api/v1/siem/config", json=config_data)
        assert response.status_code == 200
        assert "siem_id" in response.json()

def test_get_siem_health():
    """Test GET /siem/health/{siem_id} endpoint"""
    with patch('backend.siem_integration.api.siem_service.get_siem_health') as mock_health:
        from backend.siem_integration.models import SIEMHealthStatus
        mock_health_obj = SIEMHealthStatus(
            siem_id="test-siem-1",
            status="healthy",
            last_successful_connection=datetime.utcnow(),
            last_check_time=datetime.utcnow(),
            response_time_ms=150.0,
            events_processed_24h=1000
        )
        mock_health.return_value = mock_health_obj
        
        response = client.get("/siem/api/v1/siem/health/test-siem-1")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_query_siem():
    """Test POST /siem/query/{siem_id} endpoint"""
    query_data = {
        "query_string": "source=security",
        "start_time": datetime.utcnow().isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "max_results": 100
    }
    
    with patch('backend.siem_integration.api.siem_service.query_siem') as mock_query:
        from backend.siem_integration.models import SIEMResponse
        mock_response = SIEMResponse(
            status="success",
            total_events=5,
            events=[],
            query_time_ms=250.0
        )
        mock_query.return_value = mock_response
        
        response = client.post("/siem/api/v1/siem/query/test-siem-1", json=query_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

def test_siem_webhook():
    """Test POST /siem/webhook endpoint"""
    webhook_data = {
        "webhook_id": "webhook-123",
        "timestamp": datetime.utcnow().isoformat(),
        "siem_source": "test-siem",
        "events": [
            {
                "event_id": "evt-001",
                "event_type": "security_alert",
                "severity": "high",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    
    with patch('backend.siem_integration.api.siem_service.process_webhook') as mock_webhook:
        from backend.siem_integration.models import SIEMEvent
        mock_events = [
            SIEMEvent(
                event_id="evt-001",
                siem_source="test-siem",
                timestamp=datetime.utcnow(),
                event_type="security_alert",
                severity="high"
            )
        ]
        mock_webhook.return_value = mock_events
        
        response = client.post("/siem/api/v1/siem/webhook", json=webhook_data)
        assert response.status_code == 200
        # The actual webhook endpoint returns different format
        response_data = response.json()
        assert "status" in response_data
