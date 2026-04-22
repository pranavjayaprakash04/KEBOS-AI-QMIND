import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from backend.siem_integration.services import SIEMIntegrationService
from backend.siem_integration.models import (
    SIEMConfig, SIEMEvent, SIEMQuery, SIEMWebhookPayload, 
    SIEMType, SIEMAuthType, SIEMHealthStatus
)
import asyncio

@pytest.fixture
def siem_service():
    """Fixture to create a SIEMIntegrationService instance"""
    return SIEMIntegrationService()

@pytest.fixture
def sample_siem_config():
    """Fixture for a sample SIEM configuration"""
    return SIEMConfig(
        id="test-siem-1",
        name="Test SIEM",
        siem_type=SIEMType.SPLUNK,
        base_url="https://test-siem.example.com",
        auth_type=SIEMAuthType.API_KEY
    )

@pytest.fixture
def sample_siem_query():
    """Fixture for a sample SIEM query"""
    return SIEMQuery(
        query_string="source=security",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        max_results=100
    )

@pytest.mark.asyncio
async def test_add_siem_config(siem_service, sample_siem_config):
    """Test adding a SIEM configuration"""
    with patch.object(siem_service, '_validate_siem_connection', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = True
        
        config_id = await siem_service.add_siem_config(sample_siem_config)
        assert config_id == sample_siem_config.id
        assert sample_siem_config.id in siem_service.siem_configs

@pytest.mark.asyncio
async def test_get_siem_config(siem_service, sample_siem_config):
    """Test retrieving a SIEM configuration"""
    # Add the config first
    siem_service.siem_configs[sample_siem_config.id] = sample_siem_config
    
    retrieved_config = await siem_service.get_siem_config(sample_siem_config.id)
    assert retrieved_config is not None
    assert retrieved_config.id == sample_siem_config.id
    assert retrieved_config.name == sample_siem_config.name

@pytest.mark.asyncio
async def test_list_siem_configs(siem_service, sample_siem_config):
    """Test listing all SIEM configurations"""
    # Add a config
    siem_service.siem_configs[sample_siem_config.id] = sample_siem_config
    
    configs = await siem_service.list_siem_configs()
    assert len(configs) == 1
    assert configs[0].id == sample_siem_config.id

@pytest.mark.asyncio
async def test_get_siem_health(siem_service, sample_siem_config):
    """Test getting SIEM health status"""
    # Add config and mock health status
    siem_service.siem_configs[sample_siem_config.id] = sample_siem_config
    mock_health = SIEMHealthStatus(
        siem_id=sample_siem_config.id,
        status="healthy",
        last_successful_connection=datetime.utcnow(),
        last_check_time=datetime.utcnow(),  # Add the missing field
        response_time_ms=150.0,
        events_processed_24h=1000
    )
    siem_service.health_status[sample_siem_config.id] = mock_health
    
    health = await siem_service.get_siem_health(sample_siem_config.id)
    assert health is not None
    assert health.siem_id == sample_siem_config.id
    assert health.status == "healthy"

@pytest.mark.asyncio
async def test_query_siem(siem_service, sample_siem_config, sample_siem_query):
    """Test querying a SIEM system"""
    # Add config
    siem_service.siem_configs[sample_siem_config.id] = sample_siem_config
    
    with patch.object(siem_service, '_query_splunk', new_callable=AsyncMock) as mock_query:
        mock_response = {
            "status": "success",
            "total_events": 5,
            "events": [],
            "query_time_ms": 250.0
        }
        mock_query.return_value = mock_response
        
        response = await siem_service.query_siem(sample_siem_config.id, sample_siem_query)
        assert response["status"] == "success"
        assert response["total_events"] == 5

@pytest.mark.asyncio
async def test_normalize_event(siem_service):
    """Test event normalization"""
    raw_event = {
        "id": "evt-001",
        "type": "security_alert",
        "severity": "high",
        "time": datetime.utcnow().isoformat(),
        "source_ip": "192.168.1.100",
        "destination_ip": "10.0.0.5"
    }
    
    normalized = siem_service.normalize_event(raw_event, "test-siem")
    
    assert normalized.event_id == "evt-001"
    assert normalized.event_type == "security_alert"
    assert normalized.severity == "high"
    assert normalized.siem_source == "test-siem"
    assert normalized.source_ip == "192.168.1.100"

@pytest.mark.asyncio
async def test_process_webhook(siem_service, sample_siem_config):
    """Test webhook processing"""
    # Add a SIEM config first (webhook needs to find the config)
    siem_service.siem_configs["test-siem"] = sample_siem_config
    
    webhook_payload = SIEMWebhookPayload(
        webhook_id="webhook-123",
        timestamp=datetime.utcnow(),
        siem_source="test-siem",
        events=[
            {
                "id": "evt-001",
                "type": "alert",
                "severity": "medium",
                "time": datetime.utcnow().isoformat()
            }
        ]
    )
    
    events = await siem_service.process_webhook(webhook_payload)
    assert len(events) == 1
    assert events[0].event_id == "evt-001"
    assert events[0].siem_source == "test-siem"

@pytest.mark.asyncio
async def test_delete_siem_config(siem_service, sample_siem_config):
    """Test deleting a SIEM configuration"""
    # Add config first
    siem_service.siem_configs[sample_siem_config.id] = sample_siem_config
    
    success = await siem_service.delete_siem_config(sample_siem_config.id)
    assert success is True
    assert sample_siem_config.id not in siem_service.siem_configs
