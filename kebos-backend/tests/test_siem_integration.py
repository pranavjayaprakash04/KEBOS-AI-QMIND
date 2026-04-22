"""
Tests for SIEM Integration - CEF Forwarder, Splunk HEC, and Router endpoints.
Phase 4.3 - Outbound SIEM integrations.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.siem_integration.cef_forwarder import CEFSyslogForwarder
from app.siem_integration.splunk_hec import SplunkHECClient
from app.siem_integration.router import router
from fastapi.testclient import TestClient
from app.main import app


class TestCEFSyslogForwarder:
    """Test CEF Syslog Forwarder formatting and forwarding."""
    
    def test_format_event_confirmed_threat(self):
        """Test CEF format for CONFIRMED_THREAT status."""
        forwarder = CEFSyslogForwarder()
        threat_event = {
            "lead_category": "Malware",
            "status": "CONFIRMED_THREAT",
            "source_ip": "192.168.1.100",
            "indicator_value": "evil.com",
            "confidence": 0.85,
            "mitre_techniques": "T1059"
        }
        
        cef_line = forwarder.format_event(threat_event)
        
        # Verify CEF format structure
        assert cef_line.startswith("CEF:0|Pynevera|KebosAI|1.0|")
        assert "QMind-Malware" in cef_line
        assert "Malware detected" in cef_line
        assert "|10|" in cef_line  # Severity 10 for CONFIRMED_THREAT
        assert "src=192.168.1.100" in cef_line
        assert "dst=evil.com" in cef_line
        assert "confidence=0.850" in cef_line
        assert "cat=Malware" in cef_line
        assert "cs1=T1059" in cef_line
        assert "cs1Label=MITRETechniques" in cef_line
    
    def test_format_event_elevated(self):
        """Test CEF format for ELEVATED status."""
        forwarder = CEFSyslogForwarder()
        threat_event = {
            "lead_category": "Phishing",
            "status": "ELEVATED",
            "source_ip": "10.0.0.50",
            "indicator_value": "phish-site.com",
            "confidence": 0.65,
            "mitre_techniques": "T1566"
        }
        
        cef_line = forwarder.format_event(threat_event)
        
        assert "|7|" in cef_line  # Severity 7 for ELEVATED
        assert "src=10.0.0.50" in cef_line
        assert "dst=phish-site.com" in cef_line
    
    def test_format_event_monitoring(self):
        """Test CEF format for MONITORING status."""
        forwarder = CEFSyslogForwarder()
        threat_event = {
            "lead_category": "Suspicious",
            "status": "MONITORING",
            "source_ip": "172.16.0.10",
            "indicator_value": "suspicious.net",
            "confidence": 0.45,
            "mitre_techniques": ""
        }
        
        cef_line = forwarder.format_event(threat_event)
        
        assert "|5|" in cef_line  # Severity 5 for MONITORING
    
    def test_format_event_benign(self):
        """Test CEF format for BENIGN status."""
        forwarder = CEFSyslogForwarder()
        threat_event = {
            "lead_category": "Benign",
            "status": "BENIGN",
            "source_ip": "8.8.8.8",
            "indicator_value": "google.com",
            "confidence": 0.15,
            "mitre_techniques": ""
        }
        
        cef_line = forwarder.format_event(threat_event)
        
        assert "|1|" in cef_line  # Severity 1 for BENIGN
    
    def test_format_event_missing_fields(self):
        """Test CEF format with missing fields uses defaults."""
        forwarder = CEFSyslogForwarder()
        threat_event = {
            "lead_category": "Unknown",
            "status": "",
            "source_ip": "0.0.0.0",
            "indicator_value": "",
            "confidence": 0,
            "mitre_techniques": ""
        }
        
        cef_line = forwarder.format_event(threat_event)
        
        assert "|5|" in cef_line  # Default severity 5
        assert "src=0.0.0.0" in cef_line
        assert "dst=" in cef_line
    
    @pytest.mark.asyncio
    async def test_forward_with_syslog_handler(self):
        """Test forward calls tls_syslog_handler.emit_raw when configured."""
        forwarder = CEFSyslogForwarder()
        threat_event = {
            "lead_category": "Malware",
            "status": "CONFIRMED_THREAT",
            "source_ip": "192.168.1.100",
            "indicator_value": "evil.com",
            "confidence": 0.85,
            "mitre_techniques": "T1059"
        }
        
        with patch('app.siem_integration.cef_forwarder.get_tls_syslog_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.emit_raw = Mock()
            mock_get_handler.return_value = mock_handler
            
            result = await forwarder.forward(threat_event)
            
            assert result is True
            mock_handler.emit_raw.assert_called_once()
            cef_arg = mock_handler.emit_raw.call_args[0][0]
            assert "CEF:0|Pynevera|KebosAI|1.0|" in cef_arg
    
    @pytest.mark.asyncio
    async def test_forward_without_syslog_handler(self):
        """Test forward logs when syslog handler not configured."""
        forwarder = CEFSyslogForwarder()
        threat_event = {
            "lead_category": "Malware",
            "status": "CONFIRMED_THREAT",
            "source_ip": "192.168.1.100",
            "indicator_value": "evil.com",
            "confidence": 0.85,
            "mitre_techniques": "T1059"
        }
        
        with patch('app.siem_integration.cef_forwarder.get_tls_syslog_handler') as mock_get_handler:
            mock_get_handler.return_value = None
            
            result = await forwarder.forward(threat_event)
            
            assert result is True


class TestSplunkHECClient:
    """Test Splunk HEC Client."""
    
    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        client = SplunkHECClient(
            hec_url="https://splunk.example.com:8088",
            hec_token="test-token-123",
            index="custom-index"
        )
        
        assert client.url == "https://splunk.example.com:8088/services/collector"
        assert client.token == "test-token-123"
        assert client.index == "custom-index"
    
    def test_init_defaults(self):
        """Test initialization uses settings defaults."""
        with patch('app.siem_integration.splunk_hec.settings') as mock_settings:
            mock_settings.SPLUNK_HEC_URL = "https://splunk.local:8088"
            mock_settings.SPLUNK_HEC_TOKEN = "default-token"
            mock_settings.SPLUNK_INDEX = "kebos"
            
            client = SplunkHECClient()
            
            assert client.url == "https://splunk.local:8088/services/collector"
            assert client.token == "default-token"
            assert client.index == "kebos"
    
    @pytest.mark.asyncio
    async def test_send_event_skips_when_no_token(self):
        """Test send_event returns early when token is empty."""
        client = SplunkHECClient(hec_token="")
        threat_event = {
            "indicator_value": "evil.com",
            "lead_category": "Malware",
            "confidence": 0.85,
            "category_scores": {},
            "reversibility": "REVERSIBLE",
            "mitre_techniques": ["T1059"],
            "status": "CONFIRMED_THREAT",
            "tenant_id": "tenant-123"
        }
        
        result = await client.send_event(threat_event)
        
        # Should return None (early return) when no token
        assert result is None
    
    @pytest.mark.asyncio
    async def test_send_event_with_token(self):
        """Test send_event sends to Splunk when token is configured."""
        client = SplunkHECClient(
            hec_url="https://splunk.example.com:8088",
            hec_token="test-token"
        )
        threat_event = {
            "indicator_value": "evil.com",
            "lead_category": "Malware",
            "confidence": 0.85,
            "category_scores": {"malware": 0.9},
            "reversibility": "REVERSIBLE",
            "mitre_techniques": ["T1059"],
            "status": "CONFIRMED_THREAT",
            "tenant_id": "tenant-123",
            "timestamp": 1713782400
        }
        
        with patch('app.siem_integration.splunk_hec.EgressControlledClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await client.send_event(threat_event)
            
            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://splunk.example.com:8088/services/collector"
            assert call_args[1]["headers"]["Authorization"] == "Splunk test-token"
            assert call_args[1]["json"]["event"]["indicator"] == "evil.com"
            assert call_args[1]["json"]["event"]["lead_category"] == "Malware"
            assert call_args[1]["json"]["event"]["confidence"] == 0.85
            assert call_args[1]["json"]["sourcetype"] == "kebos:threat"
            assert call_args[1]["json"]["index"] == "kebos"
    
    @pytest.mark.asyncio
    async def test_send_event_handles_error(self):
        """Test send_event handles errors gracefully."""
        client = SplunkHECClient(
            hec_url="https://splunk.example.com:8088",
            hec_token="test-token"
        )
        threat_event = {
            "indicator_value": "evil.com",
            "lead_category": "Malware",
            "confidence": 0.85,
            "category_scores": {},
            "reversibility": "REVERSIBLE",
            "mitre_techniques": [],
            "status": "CONFIRMED_THREAT",
            "tenant_id": "tenant-123"
        }
        
        with patch('app.siem_integration.splunk_hec.EgressControlledClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection error")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await client.send_event(threat_event)
            
            assert result is False


class TestSIEMRouter:
    """Test SIEM Integration Router endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_enrich_endpoint_requires_auth(self, client):
        """Test /api/v1/siem/enrich requires authentication."""
        response = client.post(
            "/api/v1/siem/enrich",
            params={"indicator_value": "evil.com", "indicator_type": "domain"}
        )
        
        # Should return 401 or 403 without auth
        assert response.status_code in (401, 403)
    
    @pytest.mark.asyncio
    async def test_enrich_endpoint_calls_qmind(self):
        """Test /api/v1/siem/enrich calls QMind with tenant_id."""
        from fastapi import Request
        from unittest.mock import AsyncMock
        
        # Mock current_user
        mock_user = Mock()
        mock_user.tenant_id = "tenant-123"
        
        threat_event = {
            "indicator_value": "evil.com",
            "indicator_type": "domain",
            "tenant_id": "tenant-123"
        }
        
        with patch('app.siem_integration.router.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('app.siem_integration.router.EgressControlledClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "lead_category": "Malware",
                    "confidence": 0.85,
                    "category_scores": {}
                }
                mock_response.raise_for_status = Mock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                # Call the endpoint function directly
                from app.siem_integration.router import enrich_indicator
                result = await enrich_indicator(
                    indicator_value="evil.com",
                    indicator_type="domain",
                    request=Mock(),
                    current_user=mock_user
                )
                
                assert result["lead_category"] == "Malware"
                mock_client.post.assert_called_once()
                call_args = mock_client.post.call_args
                assert call_args[1]["json"]["tenant_id"] == "tenant-123"
    
    @pytest.mark.asyncio
    async def test_stix_bundle_endpoint(self):
        """Test /api/v1/siem/stix/bundle returns STIX 2.1 bundle."""
        from unittest.mock import AsyncMock, Mock
        
        # Mock current_user
        mock_user = Mock()
        mock_user.tenant_id = "tenant-123"
        
        # Mock request with db_pool
        mock_request = Mock()
        mock_db_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                'indicator_type': 'domain',
                'indicator_value': 'evil.com',
                'lead_category': 'Malware',
                'first_seen': None
            }
        ]
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_request.app.state.db_pool = mock_db_pool
        
        with patch('app.siem_integration.router.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            from app.siem_integration.router import get_stix_bundle
            result = await get_stix_bundle(request=mock_request, current_user=mock_user)
            
            # Should return a dict with STIX bundle structure
            assert "type" in result
            assert result["type"] == "bundle"
            assert "objects" in result
            # Should have at least one indicator
            assert len(result["objects"]) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
