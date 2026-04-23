"""
Comprehensive tests for Phases 3 & 4 - Egress Control, CERT-In, Deception, SIEM.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import httpx

from app.integrations.egress_client import EgressControlledClient, EgressViolation, get_egress_client
from app.reporting.cert_in import CERTInReportGenerator, CERTInReport, DilithiumSigner
from app.reporting.cert_in_sla_monitor import CERTInSLAMonitor
from app.deception.honeygrid import HoneyGridManager, HoneypotDeployment, IOC
from app.deception.honeytokens import HoneytokenManager, Honeytoken, HoneytokenType
from app.siem_integration.cef_forwarder import CEFSyslogForwarder, get_cef_forwarder
from app.siem_integration.stix_export import STIXExporter, get_stix_exporter
from app.siem_integration.splunk_hec import SplunkHECClient, get_splunk_hec_client
from app.simulation.digital_twin import DigitalTwinSimulator, SimulationResult, get_digital_twin_simulator
from app.config import settings


# ============================================================================
# PHASE 3 TESTS - Egress Control
# ============================================================================

class TestEgressControlledClient:
    """Tests for EgressControlledClient"""
    
    @pytest.fixture
    def client(self):
        """Create EgressControlledClient instance"""
        return EgressControlledClient()
    
    def test_allowed_domain(self, client):
        """Test that allowlisted domains are permitted"""
        # certstream.calidog.io should be in allowlist
        client._check_domain_allowed("https://certstream.calidog.io/stream")
        # Should not raise
    
    def test_blocked_domain_strict_mode(self, client):
        """Test that non-allowlisted domains are blocked in STRICT_MODE"""
        with pytest.raises(EgressViolation) as exc_info:
            client._check_domain_allowed("https://evil.com/malware")
        assert "not in ALLOWED_EGRESS_DOMAINS" in str(exc_info.value)
    
    def test_timeout_configured(self, client):
        """Test that 10s timeout is configured"""
        assert client.TIMEOUT == 10.0
    
    def test_get_singleton(self):
        """Test that get_egress_client returns singleton"""
        client1 = get_egress_client()
        client2 = get_egress_client()
        assert client1 is client2


# ============================================================================
# PHASE 3 TESTS - CERT-In Report Generator
# ============================================================================

class TestCERTInReportGenerator:
    """Tests for CERTInReportGenerator"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        return AsyncMock()
    
    @pytest.fixture
    def generator(self, mock_db_pool):
        """Create CERTInReportGenerator instance"""
        return CERTInReportGenerator(mock_db_pool)
    
    @pytest.fixture
    def threat_event(self):
        """Sample threat event"""
        return {
            "id": "THREAT-001",
            "threat_type": "malware",
            "severity": "high",
            "source_ip": "192.168.1.100",
            "created_at": datetime.now(timezone.utc),
        }
    
    @pytest.mark.asyncio
    async def test_generate_report(self, generator, threat_event, mock_db_pool):
        """Test CERT-In report generation"""
        mock_db_pool.acquire = AsyncMock()
        mock_conn = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        report = await generator.generate(threat_event)
        
        assert isinstance(report, CERTInReport)
        assert report.incident_id == "THREAT-001"
        assert report.report_hash is not None
        assert report.signature is not None
        assert report.pubkey_ref == "vault:dilithium3-cert-in-key"
    
    @pytest.mark.asyncio
    async def test_jinja2_fallback(self, generator, threat_event):
        """Test Jinja2 fallback when SOC report fails"""
        sections = await generator._jinja2_fallback(threat_event)
        
        assert "affected_assets" in sections
        assert "timeline" in sections
        assert "iocs" in sections
        assert "mitigation_steps" in sections


class TestCERTInSLAMonitor:
    """Tests for CERTInSLAMonitor"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        return AsyncMock()
    
    @pytest.fixture
    def monitor(self, mock_db_pool):
        """Create CERTInSLAMonitor instance"""
        return CERTInSLAMonitor(mock_db_pool)
    
    def test_alert_threshold_hours(self, monitor):
        """Test that alert fires at 5-hour mark, not 6"""
        assert monitor.ALERT_THRESHOLD_HOURS == 5
        assert monitor.REPORTING_WINDOW_HOURS == 6
    
    @pytest.mark.asyncio
    async def test_five_hour_alert(self, monitor, mock_db_pool):
        """Test 5-hour alert logic"""
        mock_conn = AsyncMock()
        mock_db_pool.acquire = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        # Case at 5.5 hours - should trigger alert
        case = {
            "id": 1,
            "threat_id": "THREAT-001",
            "created_at": datetime.now(timezone.utc).replace(hour=datetime.now().hour - 5, minute=30),
            "five_hour_alert_sent": False,
            "cert_in_status": "PENDING",
            "tenant_id": 1,
        }
        
        await monitor._check_case_sla(mock_conn, case)
        
        # Should have updated five_hour_alert_sent
        mock_conn.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_six_hour_breach(self, monitor, mock_db_pool):
        """Test 6-hour breach alert"""
        mock_conn = AsyncMock()
        mock_db_pool.acquire = AsyncMock()
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        # Case at 6.5 hours - should trigger breach alert
        case = {
            "id": 1,
            "threat_id": "THREAT-001",
            "created_at": datetime.now(timezone.utc).replace(hour=datetime.now().hour - 6, minute=30),
            "five_hour_alert_sent": True,
            "cert_in_status": "PENDING",
            "tenant_id": 1,
        }
        
        await monitor._check_case_sla(mock_conn, case)
        
        # Should have updated status to BREACHED
        mock_conn.execute.assert_called()


# ============================================================================
# PHASE 4 TESTS - HoneyGrid
# ============================================================================

class TestHoneyGridManager:
    """Tests for HoneyGridManager"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        return AsyncMock()
    
    @pytest.fixture
    def manager(self, mock_db_pool):
        """Create HoneyGridManager instance"""
        return HoneyGridManager(mock_db_pool)
    
    def test_docker_proxy_url(self, manager):
        """Test that docker-proxy URL is correct (NOT docker.sock)"""
        assert manager.docker_proxy_url == "tcp://docker-proxy:2375"
        assert "docker.sock" not in manager.docker_proxy_url
    
    def test_honeypot_images(self, manager):
        """Test that honeypot images are defined"""
        assert "ssh" in manager.HONEYPOT_IMAGES
        assert "http" in manager.HONEYPOT_IMAGES
        assert manager.HONEYPOT_IMAGES["ssh"] == "cowrie/cowrie:latest"


# ============================================================================
# PHASE 4 TESTS - Honeytokens
# ============================================================================

class TestHoneytokenManager:
    """Tests for HoneytokenManager"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        return AsyncMock()
    
    @pytest.fixture
    def manager(self, mock_db_pool):
        """Create HoneytokenManager instance"""
        return HoneytokenManager(mock_db_pool)
    
    def test_token_types(self, manager):
        """Test that all 5 honeytoken types are defined"""
        assert HoneytokenType.AWS_KEY in manager.TOKEN_TYPES
        assert HoneytokenType.DB_PASSWORD in manager.TOKEN_TYPES
        assert HoneytokenType.API_KEY in manager.TOKEN_TYPES
        assert HoneytokenType.UPI_CRED in manager.TOKEN_TYPES
        assert HoneytokenType.SWIFT_TOKEN in manager.TOKEN_TYPES
    
    def test_token_generation(self, manager):
        """Test that tokens generate unique values"""
        aws_value, _ = manager.TOKEN_TYPES[HoneytokenType.AWS_KEY]
        assert aws_value.startswith("AKIA")
        
        db_value, _ = manager.TOKEN_TYPES[HoneytokenType.DB_PASSWORD]
        assert db_value.startswith("honey_")
        
        api_value, _ = manager.TOKEN_TYPES[HoneytokenType.API_KEY]
        assert api_value.startswith("sk-honey-")


# ============================================================================
# PHASE 4 TESTS - Digital Twin Simulator
# ============================================================================

class TestDigitalTwinSimulator:
    """Tests for DigitalTwinSimulator"""
    
    @pytest.fixture
    def mock_db_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire = AsyncMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock()
        return pool
    
    @pytest.fixture
    def simulator(self, mock_db_pool):
        """Create DigitalTwinSimulator instance"""
        return DigitalTwinSimulator(mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_simulate_action_not_stub(self, simulator, mock_db_pool):
        """Test that simulate_action is NOT a stub (Bug #14)"""
        # Mock empty historical data
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[])
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        result = await simulator.simulate_action("block_ip", tenant_id=1)
        
        # Should return proper SimulationResult, not just pass
        assert isinstance(result, SimulationResult)
        assert result.impact_score == 1.0  # Conservative for empty data
        assert result.recommendation == "BLOCK_PENDING_INVESTIGATION"
        assert result.n_total == 0
    
    @pytest.mark.asyncio
    async def test_impact_score_range(self, simulator, mock_db_pool):
        """Test that impact_score is in range 0.0-1.0"""
        # Mock some historical data
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[
            {"source_ip": "1.2.3.4", "destination_ip": "5.6.7.8", "indicator_type": "ip", "status": "unknown"},
            {"source_ip": "1.2.3.5", "destination_ip": "5.6.7.9", "indicator_type": "ip", "status": "CONFIRMED_THREAT"},
        ])
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        result = await simulator.simulate_action("block_ip", tenant_id=1)
        
        assert 0.0 <= result.impact_score <= 1.0
        assert result.n_total == 2
    
    @pytest.mark.asyncio
    async def test_recommendation_threshold(self, simulator, mock_db_pool):
        """Test recommendation threshold: <0.05 = present, >=0.05 = block"""
        # Low false positive rate
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[
            {"source_ip": f"1.2.3.{i}", "destination_ip": "5.6.7.8", "indicator_type": "ip", "status": "CONFIRMED_THREAT"}
            for i in range(100)
        ])
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        result = await simulator.simulate_action("block_ip", tenant_id=1)
        
        if result.impact_score < 0.05:
            assert result.recommendation == "PRESENT_TO_ANALYST_FOR_APPROVAL"
        else:
            assert result.recommendation == "BLOCK_PENDING_INVESTIGATION"
    
    @pytest.mark.asyncio
    async def test_empty_history_conservative(self, simulator, mock_db_pool):
        """Test that empty history returns impact_score=1.0 (conservative)"""
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=[])
        mock_db_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        mock_db_pool.acquire.return_value.__aexit__ = AsyncMock()
        
        result = await simulator.simulate_action("block_ip", tenant_id=1)
        
        assert result.impact_score == 1.0
        assert result.n_total == 0
        assert result.recommendation == "BLOCK_PENDING_INVESTIGATION"


# ============================================================================
# PHASE 4 TESTS - SIEM Integration
# ============================================================================

class TestCEFSyslogForwarder:
    """Tests for CEFSyslogForwarder"""
    
    @pytest.fixture
    def forwarder(self):
        """Create CEFSyslogForwarder instance"""
        return get_cef_forwarder()
    
    def test_format_event(self, forwarder):
        """Test CEF event formatting"""
        threat_event = {
            "id": "THREAT-001",
            "qmind_category": "malware",
            "severity": "high",
            "source_ip": "192.168.1.100",
            "qmind_confidence": 0.95,
            "tenant_id": 1,
            "dilithium_signature": "abc123def456",
        }
        
        cef_message = forwarder.format_event(threat_event)
        
        assert "CEF:0|" in cef_message
        assert "Pynevera" in cef_message
        assert "KebosAI" in cef_message
        assert "src=192.168.1.100" in cef_message
        assert "confidence=0.950" in cef_message


class TestSTIXExporter:
    """Tests for STIXExporter"""
    
    @pytest.fixture
    def exporter(self):
        """Create STIXExporter instance"""
        return get_stix_exporter()
    
    def test_to_indicator(self, exporter):
        """Test IOC to STIX Indicator conversion"""
        ioc = {
            "id": "IOC-001",
            "type": "ip",
            "value": "192.168.1.100",
            "lead_category": "malicious-activity",
            "confidence": 0.95,
        }
        
        indicator = exporter.to_indicator(ioc)
        
        assert indicator.type == "indicator"
        assert "ipv4-addr:value = '192.168.1.100'" in indicator.pattern
        assert indicator.confidence == 95
    
    def test_to_bundle(self, exporter):
        """Test IOC list to STIX Bundle conversion"""
        iocs = [
            {
                "id": "IOC-001",
                "type": "ip",
                "value": "192.168.1.100",
                "lead_category": "malicious-activity",
                "confidence": 0.95,
            }
        ]
        
        bundle = exporter.to_bundle(iocs)
        
        assert bundle.type == "bundle"
        assert len(bundle.objects) >= 2  # Identity + at least one indicator


class TestSplunkHECClient:
    """Tests for SplunkHECClient"""
    
    @pytest.fixture
    def hec_client(self):
        """Create SplunkHECClient instance"""
        return get_splunk_hec_client()
    
    def test_index_configured(self, hec_client):
        """Test that Splunk index is configured"""
        assert hec_client.index == "kebos_threats"
    
    def test_hec_url_from_settings(self, hec_client):
        """Test that HEC URL comes from settings"""
        assert hec_client.hec_url == settings.SPLUNK_HEC_URL


# ============================================================================
# Integration Tests
# ============================================================================

class TestConfigSettings:
    """Test that config settings are correct"""
    
    def test_certstream_in_allowlist(self):
        """Test that certstream.calidog.io is in ALLOWED_EGRESS_DOMAINS"""
        assert "certstream.calidog.io" in settings.ALLOWED_EGRESS_DOMAINS
    
    def test_egress_strict_mode(self):
        """Test that EGRESS_STRICT_MODE is enabled"""
        assert settings.EGRESS_STRICT_MODE == True
    
    def test_splunk_settings(self):
        """Test that Splunk settings are defined"""
        assert hasattr(settings, 'SPLUNK_HEC_URL')
        assert hasattr(settings, 'SPLUNK_HEC_TOKEN')
        assert hasattr(settings, 'SPLUNK_INDEX')
