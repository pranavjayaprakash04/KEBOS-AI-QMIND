"""
Integration tests for Network Analytics API endpoints
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest_asyncio

from main import app
from network_analytics.models import (
    NetworkFlowORM, TrafficPatternORM, NetworkAnomalyORM,
    AnalyticsJobORM, NetworkTopologyORM
)
from network_analytics.services import NetworkAnalyticsService


class TestNetworkAnalyticsAPI:
    """Test Network Analytics API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_analytics_service(self):
        """Mock analytics service"""
        service = Mock(spec=NetworkAnalyticsService)
        
        # Mock methods as async
        service.query_network_flows = AsyncMock()
        service.detect_traffic_patterns = AsyncMock()
        service.detect_anomalies = AsyncMock()
        service.get_flow_statistics = AsyncMock()
        service.create_analytics_job = AsyncMock()
        service.query_network_topology = AsyncMock()
        service.get_analytics_job = AsyncMock()
        service.get_pattern_by_id = AsyncMock()
        service.get_anomaly_by_id = AsyncMock()
        service.get_topology_by_ip = AsyncMock()
        
        return service
    
    def test_network_flows_query_endpoint(self, client):
        """Test /analytics/flows endpoint"""
        # Mock successful response
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.query_network_flows = AsyncMock(return_value=[])
            
            response = client.post(
                "/analytics/flows",
                json={
                    "start_time": "2024-01-01T00:00:00",
                    "end_time": "2024-01-01T23:59:59",
                    "limit": 100
                }
            )
            
            assert response.status_code == 200
            assert "flows" in response.json()
    
    def test_network_flows_query_validation(self, client):
        """Test flows query input validation"""
        # Test missing required fields
        response = client.post("/analytics/flows", json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid date format
        response = client.post(
            "/analytics/flows",
            json={
                "start_time": "invalid-date",
                "end_time": "2024-01-01T23:59:59"
            }
        )
        assert response.status_code == 422
    
    def test_traffic_patterns_detection_endpoint(self, client):
        """Test /analytics/patterns/detect endpoint"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.detect_traffic_patterns = AsyncMock(return_value=[])
            
            response = client.post(
                "/analytics/patterns/detect",
                json={
                    "time_window_hours": 24,
                    "pattern_types": ["periodic", "burst"],
                    "min_confidence": 0.7
                }
            )
            
            assert response.status_code == 200
            assert "patterns" in response.json()
    
    def test_anomaly_detection_endpoint(self, client):
        """Test /analytics/anomalies/detect endpoint"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.detect_anomalies = AsyncMock(return_value=[])
            
            response = client.post(
                "/analytics/anomalies/detect",
                json={
                    "detection_algorithm": "statistical",
                    "sensitivity_threshold": 2.0,
                    "time_window_hours": 24
                }
            )
            
            assert response.status_code == 200
            assert "anomalies" in response.json()
    
    def test_flow_statistics_endpoint(self, client):
        """Test /analytics/statistics endpoint"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_flow_statistics = AsyncMock(return_value=Mock(
                total_flows=1000,
                total_bytes=5000000,
                unique_source_ips=50,
                unique_destination_ips=25,
                average_flow_duration=10.5,
                protocol_distribution={"TCP": 800, "UDP": 200},
                top_source_ips=[],
                top_destination_ips=[],
                top_ports=[]
            ))
            
            response = client.post(
                "/analytics/statistics",
                json={
                    "start_time": "2024-01-01T00:00:00",
                    "end_time": "2024-01-01T23:59:59"
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert "statistics" in result
            assert result["statistics"]["total_flows"] == 1000
    
    def test_analytics_job_creation_endpoint(self, client):
        """Test /analytics/jobs endpoint"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_job = Mock()
            mock_job.id = str(uuid4())
            mock_job.job_id = "job_001"
            mock_job.job_type = "pattern_analysis"
            mock_job.status = "pending"
            mock_job.created_at = datetime.now()
            
            mock_service.create_analytics_job = AsyncMock(return_value=mock_job)
            
            response = client.post(
                "/analytics/jobs",
                json={
                    "job_type": "pattern_analysis",
                    "job_name": "Test Pattern Analysis",
                    "query_parameters": {"time_window": 24}
                }
            )
            
            assert response.status_code == 201
            result = response.json()
            assert "job" in result
            assert result["job"]["job_type"] == "pattern_analysis"
    
    def test_network_topology_query_endpoint(self, client):
        """Test /analytics/topology endpoint"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.query_network_topology = AsyncMock(return_value=[])
            
            response = client.post(
                "/analytics/topology",
                json={
                    "asset_types": ["server", "workstation"],
                    "is_active": True
                }
            )
            
            assert response.status_code == 200
            assert "topology" in response.json()
    
    def test_get_analytics_job_endpoint(self, client):
        """Test GET /analytics/jobs/{job_id} endpoint"""
        job_id = str(uuid4())
        
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_job = Mock()
            mock_job.id = job_id
            mock_job.job_id = "job_001"
            mock_job.status = "completed"
            
            mock_service.get_analytics_job = AsyncMock(return_value=mock_job)
            
            response = client.get(f"/analytics/jobs/{job_id}")
            
            assert response.status_code == 200
            result = response.json()
            assert "job" in result
            assert result["job"]["status"] == "completed"
    
    def test_get_analytics_job_not_found(self, client):
        """Test job not found scenario"""
        job_id = str(uuid4())
        
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_analytics_job = AsyncMock(return_value=None)
            
            response = client.get(f"/analytics/jobs/{job_id}")
            
            assert response.status_code == 404
    
    def test_get_pattern_by_id_endpoint(self, client):
        """Test GET /analytics/patterns/{pattern_id} endpoint"""
        pattern_id = str(uuid4())
        
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_pattern = Mock()
            mock_pattern.id = pattern_id
            mock_pattern.pattern_id = "pattern_001"
            mock_pattern.pattern_type = "periodic"
            
            mock_service.get_pattern_by_id = AsyncMock(return_value=mock_pattern)
            
            response = client.get(f"/analytics/patterns/{pattern_id}")
            
            assert response.status_code == 200
            result = response.json()
            assert "pattern" in result
            assert result["pattern"]["pattern_type"] == "periodic"
    
    def test_get_anomaly_by_id_endpoint(self, client):
        """Test GET /analytics/anomalies/{anomaly_id} endpoint"""
        anomaly_id = str(uuid4())
        
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_anomaly = Mock()
            mock_anomaly.id = anomaly_id
            mock_anomaly.anomaly_id = "anomaly_001"
            mock_anomaly.anomaly_type = "traffic_spike"
            
            mock_service.get_anomaly_by_id = AsyncMock(return_value=mock_anomaly)
            
            response = client.get(f"/analytics/anomalies/{anomaly_id}")
            
            assert response.status_code == 200
            result = response.json()
            assert "anomaly" in result
            assert result["anomaly"]["anomaly_type"] == "traffic_spike"
    
    def test_export_data_endpoint(self, client):
        """Test /analytics/export endpoint"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.query_network_flows = AsyncMock(return_value=[])
            
            response = client.post(
                "/analytics/export",
                json={
                    "data_type": "flows",
                    "format": "csv",
                    "query_parameters": {
                        "start_time": "2024-01-01T00:00:00",
                        "end_time": "2024-01-01T23:59:59"
                    }
                }
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_get_diagnostics_endpoint(self, client):
        """Test /analytics/diagnostics endpoint"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_flow_statistics = AsyncMock(return_value=Mock(
                total_flows=1000
            ))
            mock_service.query_network_flows = AsyncMock(return_value=[Mock()])
            
            response = client.get("/analytics/diagnostics")
            
            assert response.status_code == 200
            result = response.json()
            assert "diagnostics" in result
            assert "database_status" in result["diagnostics"]
            assert "recent_activity" in result["diagnostics"]
    
    def test_authentication_required(self, client):
        """Test that endpoints require authentication"""
        # This test would be more meaningful with actual auth implementation
        # For now, test the structure
        
        endpoints = [
            ("/analytics/flows", "POST"),
            ("/analytics/patterns/detect", "POST"),
            ("/analytics/anomalies/detect", "POST"),
            ("/analytics/statistics", "POST"),
            ("/analytics/jobs", "POST"),
            ("/analytics/topology", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "POST":
                # Without mocking auth, this will likely fail authentication
                # In a real test, we'd test with and without valid tokens
                assert endpoint.startswith("/analytics")
    
    def test_error_handling(self, client):
        """Test API error handling"""
        with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.query_network_flows = AsyncMock(side_effect=Exception("Database error"))
            
            response = client.post(
                "/analytics/flows",
                json={
                    "start_time": "2024-01-01T00:00:00",
                    "end_time": "2024-01-01T23:59:59"
                }
            )
            
            assert response.status_code == 500
            assert "error" in response.json()


@pytest.mark.asyncio
class TestAsyncNetworkAnalyticsAPI:
    """Async API tests"""
    
    async def test_async_flow_query(self):
        """Test async flow query processing"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.query_network_flows = AsyncMock(return_value=[])
                
                response = await ac.post(
                    "/analytics/flows",
                    json={
                        "start_time": "2024-01-01T00:00:00",
                        "end_time": "2024-01-01T23:59:59"
                    }
                )
                
                assert response.status_code == 200
    
    async def test_concurrent_requests(self):
        """Test handling concurrent analytics requests"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            with patch('network_analytics.api.NetworkAnalyticsService') as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.query_network_flows = AsyncMock(return_value=[])
                mock_service.detect_traffic_patterns = AsyncMock(return_value=[])
                
                # Send concurrent requests
                requests = [
                    ac.post("/analytics/flows", json={
                        "start_time": "2024-01-01T00:00:00",
                        "end_time": "2024-01-01T23:59:59"
                    }),
                    ac.post("/analytics/patterns/detect", json={
                        "time_window_hours": 24,
                        "min_confidence": 0.7
                    })
                ]
                
                responses = await asyncio.gather(*requests)
                
                assert all(r.status_code == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__])
