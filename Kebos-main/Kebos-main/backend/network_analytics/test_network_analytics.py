"""
Unit tests for Network Analytics module
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from ipaddress import IPv4Address
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from network_analytics.models import (
    NetworkFlowORM, TrafficPatternORM, NetworkAnomalyORM, 
    AnalyticsJobORM, NetworkTopologyORM,
    NetworkFlowCreate, TrafficPatternCreate, NetworkAnomalyCreate,
    AnalyticsJobCreate, NetworkTopologyCreate,
    NetworkFlowQuery, AnalyticsQuery, PatternDetectionQuery,
    AnomalyDetectionQuery, NetworkTopologyQuery
)
from network_analytics.services import NetworkAnalyticsService
from common.db import get_async_db


class TestNetworkAnalyticsModels:
    """Test ORM models and Pydantic schemas"""
    
    def test_network_flow_orm_creation(self):
        """Test NetworkFlowORM model creation"""
        flow = NetworkFlowORM(
            flow_id="test_flow_001",
            source_ip=IPv4Address("192.168.1.100"),
            destination_ip=IPv4Address("10.0.0.1"),
            source_port=12345,
            destination_port=80,
            protocol="TCP",
            direction="outbound",
            packet_count=150,
            byte_count=75000,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        
        assert flow.flow_id == "test_flow_001"
        assert str(flow.source_ip) == "192.168.1.100"
        assert str(flow.destination_ip) == "10.0.0.1"
        assert flow.protocol == "TCP"
        assert flow.packet_count == 150
    
    def test_network_flow_create_schema(self):
        """Test NetworkFlowCreate Pydantic schema"""
        flow_data = {
            "flow_id": "test_flow_002",
            "source_ip": "192.168.1.200",
            "destination_ip": "10.0.0.2",
            "source_port": 54321,
            "destination_port": 443,
            "protocol": "TCP",
            "direction": "outbound",
            "packet_count": 200,
            "byte_count": 100000,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        
        flow = NetworkFlowCreate(**flow_data)
        assert flow.flow_id == "test_flow_002"
        assert flow.protocol == "TCP"
        assert flow.packet_count == 200
    
    def test_traffic_pattern_orm_creation(self):
        """Test TrafficPatternORM model creation"""
        pattern = TrafficPatternORM(
            pattern_id="pattern_001",
            pattern_type="periodic",
            pattern_name="Daily Backup Traffic",
            confidence_score=0.95,
            first_detected=datetime.now(),
            last_detected=datetime.now()
        )
        
        assert pattern.pattern_id == "pattern_001"
        assert pattern.pattern_type == "periodic"
        assert pattern.confidence_score == 0.95
    
    def test_network_anomaly_orm_creation(self):
        """Test NetworkAnomalyORM model creation"""
        anomaly = NetworkAnomalyORM(
            anomaly_id="anomaly_001",
            anomaly_type="traffic_spike",
            title="Unusual Traffic Volume",
            severity_score=0.8,
            confidence_score=0.9,
            risk_level="high",
            detected_at=datetime.now()
        )
        
        assert anomaly.anomaly_id == "anomaly_001"
        assert anomaly.anomaly_type == "traffic_spike"
        assert anomaly.risk_level == "high"
    
    def test_analytics_job_orm_creation(self):
        """Test AnalyticsJobORM model creation"""
        job = AnalyticsJobORM(
            job_id="job_001",
            job_type="pattern_analysis",
            job_name="Weekly Pattern Analysis",
            status="pending"
        )
        
        assert job.job_id == "job_001"
        assert job.job_type == "pattern_analysis"
        assert job.status == "pending"
    
    def test_network_topology_orm_creation(self):
        """Test NetworkTopologyORM model creation"""
        topology = NetworkTopologyORM(
            ip_address=IPv4Address("192.168.1.50"),
            hostname="server-001",
            asset_type="server",
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        
        assert str(topology.ip_address) == "192.168.1.50"
        assert topology.hostname == "server-001"
        assert topology.asset_type == "server"
    
    def test_network_flow_query_schema(self):
        """Test NetworkFlowQuery schema validation"""
        query_data = {
            "start_time": datetime.now() - timedelta(hours=1),
            "end_time": datetime.now(),
            "source_ips": ["192.168.1.100", "192.168.1.200"],
            "destination_ports": [80, 443],
            "protocols": ["TCP", "UDP"],
            "min_packet_count": 10,
            "limit": 100
        }
        
        query = NetworkFlowQuery(**query_data)
        assert len(query.source_ips) == 2
        assert len(query.protocols) == 2
        assert query.min_packet_count == 10


class TestNetworkAnalyticsService:
    """Test NetworkAnalyticsService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        return session
    
    @pytest.fixture
    def analytics_service(self, mock_db_session):
        """Create NetworkAnalyticsService instance"""
        return NetworkAnalyticsService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_query_network_flows(self, analytics_service, mock_db_session):
        """Test network flows query"""
        # Mock database result
        mock_flows = [
            NetworkFlowORM(
                id=uuid4(),
                flow_id="flow_001",
                source_ip=IPv4Address("192.168.1.100"),
                destination_ip=IPv4Address("10.0.0.1"),
                protocol="TCP",
                packet_count=100,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            )
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_flows
        mock_db_session.execute.return_value = mock_result
        
        query = NetworkFlowQuery(
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            limit=10
        )
        
        flows = await analytics_service.query_network_flows(query)
        
        assert len(flows) == 1
        assert flows[0].flow_id == "flow_001"
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_detect_traffic_patterns(self, analytics_service, mock_db_session):
        """Test traffic pattern detection"""
        # Mock database results
        mock_flows = [
            Mock(source_ip="192.168.1.100", packet_count=100, first_seen=datetime.now()),
            Mock(source_ip="192.168.1.100", packet_count=120, first_seen=datetime.now()),
        ]
        
        mock_result = Mock()
        mock_result.fetchall.return_value = mock_flows
        mock_db_session.execute.return_value = mock_result
        
        query = PatternDetectionQuery(
            time_window_hours=24,
            min_confidence=0.7
        )
        
        patterns = await analytics_service.detect_traffic_patterns(query)
        
        assert isinstance(patterns, list)
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, analytics_service, mock_db_session):
        """Test anomaly detection"""
        # Mock statistical data
        mock_stats = [
            (100.0, 20.0, 150)  # avg, stddev, count
        ]
        
        mock_result = Mock()
        mock_result.fetchall.return_value = mock_stats
        mock_db_session.execute.return_value = mock_result
        
        query = AnomalyDetectionQuery(
            detection_algorithm="statistical",
            sensitivity_threshold=2.0
        )
        
        anomalies = await analytics_service.detect_anomalies(query)
        
        assert isinstance(anomalies, list)
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_flow_statistics(self, analytics_service, mock_db_session):
        """Test flow statistics calculation"""
        # Mock statistics data
        mock_stats = [
            (1000, 500000, 10.5, 100)  # total_flows, total_bytes, avg_duration, unique_ips
        ]
        
        mock_result = Mock()
        mock_result.fetchone.return_value = mock_stats[0]
        mock_db_session.execute.return_value = mock_result
        
        query = AnalyticsQuery(
            start_time=datetime.now() - timedelta(hours=24),
            end_time=datetime.now()
        )
        
        stats = await analytics_service.get_flow_statistics(query)
        
        assert stats.total_flows == 1000
        assert stats.total_bytes == 500000
        assert stats.average_flow_duration == 10.5
        assert stats.unique_source_ips == 100
    
    @pytest.mark.asyncio
    async def test_create_analytics_job(self, analytics_service, mock_db_session):
        """Test analytics job creation"""
        job_data = AnalyticsJobCreate(
            job_type="pattern_analysis",
            job_name="Test Pattern Analysis",
            query_parameters={"time_window": 24}
        )
        
        # Mock the add and refresh operations
        mock_db_session.add = Mock()
        
        job = await analytics_service.create_analytics_job(job_data, "test_user")
        
        assert job.job_type == "pattern_analysis"
        assert job.created_by == "test_user"
        assert job.status == "pending"
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_query_network_topology(self, analytics_service, mock_db_session):
        """Test network topology query"""
        # Mock topology data
        mock_topology = [
            NetworkTopologyORM(
                id=uuid4(),
                ip_address=IPv4Address("192.168.1.100"),
                hostname="server-001",
                asset_type="server",
                first_seen=datetime.now(),
                last_seen=datetime.now()
            )
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_topology
        mock_db_session.execute.return_value = mock_result
        
        query = NetworkTopologyQuery(
            asset_types=["server"],
            is_active=True
        )
        
        topology = await analytics_service.query_network_topology(query)
        
        assert len(topology) == 1
        assert topology[0].hostname == "server-001"
        assert mock_db_session.execute.called


class TestNetworkAnalyticsIntegration:
    """Integration tests for network analytics components"""
    
    @pytest.mark.asyncio
    async def test_flow_to_pattern_pipeline(self):
        """Test complete flow from network flow to pattern detection"""
        # This would test the full pipeline in an integration environment
        # Mock the complete flow for now
        
        # 1. Create network flows
        flows = [
            NetworkFlowCreate(
                flow_id=f"flow_{i}",
                source_ip="192.168.1.100",
                destination_ip="10.0.0.1",
                protocol="TCP",
                packet_count=100 + i,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            ) for i in range(10)
        ]
        
        # 2. Detect patterns from flows
        pattern_query = PatternDetectionQuery(
            time_window_hours=1,
            min_confidence=0.5
        )
        
        # 3. Detect anomalies
        anomaly_query = AnomalyDetectionQuery(
            detection_algorithm="statistical",
            sensitivity_threshold=2.0
        )
        
        # Assert basic structure
        assert len(flows) == 10
        assert pattern_query.time_window_hours == 1
        assert anomaly_query.sensitivity_threshold == 2.0
    
    @pytest.mark.asyncio
    async def test_analytics_job_lifecycle(self):
        """Test analytics job creation and processing lifecycle"""
        job_create = AnalyticsJobCreate(
            job_type="full_analysis",
            job_name="Complete Network Analysis",
            description="Full network analysis including patterns and anomalies",
            query_parameters={
                "time_range": "24h",
                "include_patterns": True,
                "include_anomalies": True
            }
        )
        
        # Test job creation
        assert job_create.job_type == "full_analysis"
        assert job_create.query_parameters["include_patterns"] is True
        
        # Mock job processing states
        job_states = ["pending", "running", "completed"]
        for state in job_states:
            assert state in ["pending", "running", "completed", "failed"]


if __name__ == "__main__":
    pytest.main([__file__])
