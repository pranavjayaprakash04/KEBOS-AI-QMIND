import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.deception.honeygrid_manager import HoneyGridManager, HoneytokenType
from app.deception.honeygrid import HoneyGridManager as HoneypotManager
from uuid import uuid4


client = TestClient(app)


class TestHoneyGrid:
    """HoneyGrid Manager Tests"""
    
    def test_create_aws_honeytoken(self):
        """Test creating AWS access key honeytoken"""
        manager = HoneyGridManager()
        honeytoken = manager.create_honeytoken(
            token_type=HoneytokenType.AWS_ACCESS_KEY,
            description="Test AWS key"
        )
        
        assert honeytoken.token_type == HoneytokenType.AWS_ACCESS_KEY
        assert honeytoken.value.startswith("AKIA")
        assert honeytoken.description == "Test AWS key"
        assert honeytoken.is_active is True
    
    def test_create_database_honeytoken(self):
        """Test creating database credential honeytoken"""
        manager = HoneyGridManager()
        honeytoken = manager.create_honeytoken(
            token_type=HoneytokenType.DATABASE_CREDENTIAL,
            description="Test DB credential"
        )
        
        assert honeytoken.token_type == HoneytokenType.DATABASE_CREDENTIAL
        assert honeytoken.value.startswith("honey_")
        assert honeytoken.description == "Test DB credential"
    
    def test_create_api_token_honeytoken(self):
        """Test creating API token honeytoken"""
        manager = HoneyGridManager()
        honeytoken = manager.create_honeytoken(
            token_type=HoneytokenType.API_TOKEN,
            description="Test API token"
        )
        
        assert honeytoken.token_type == HoneytokenType.API_TOKEN
        assert len(honeytoken.value) > 20
        assert honeytoken.description == "Test API token"
    
    def test_create_honeytoken_with_custom_value(self):
        """Test creating honeytoken with custom value"""
        manager = HoneyGridManager()
        custom_value = "custom_secret_123"
        honeytoken = manager.create_honeytoken(
            token_type=HoneytokenType.API_TOKEN,
            description="Custom token",
            custom_value=custom_value
        )
        
        assert honeytoken.value == custom_value
    
    def test_honeytoken_types_enum(self):
        """Verify 3 honeytoken types exist"""
        assert HoneytokenType.AWS_ACCESS_KEY.value == "aws_access_key"
        assert HoneytokenType.DATABASE_CREDENTIAL.value == "database_credential"
        assert HoneytokenType.API_TOKEN.value == "api_token"
        assert len(list(HoneytokenType)) == 3


class TestSIEMFormatter:
    """SIEM Formatter Tests"""
    
    def test_cef_format(self):
        """Test CEF formatting"""
        from app.siem_integration.formatter import SIEMFormatter
        
        formatter = SIEMFormatter()
        cef = formatter.format_cef(
            event_name="test_event",
            severity="high",
            extensions={"key1": "value1", "key2": "value2"}
        )
        
        assert cef.startswith("CEF:0|KebosAI|Kebos|1.0.0|test_event|test_event|8")
        assert "key1=value1" in cef
        assert "key2=value2" in cef
    
    def test_cef_escaping(self):
        """Test CEF special character escaping"""
        from app.siem_integration.formatter import SIEMFormatter
        
        formatter = SIEMFormatter()
        escaped = formatter._escape_cef_value("test=value")
        
        assert "\\=" in escaped
    
    def test_threat_cef_format(self):
        """Test threat event CEF formatting"""
        from app.siem_integration.formatter import SIEMFormatter
        
        formatter = SIEMFormatter()
        cef = formatter.format_threat_as_cef(
            threat_id="threat-123",
            category="C2_Infrastructure",
            confidence=0.95,
            ioc_value="192.168.1.1",
            ioc_type="ip",
            source_type="honeypot",
            is_proactive=False
        )
        
        assert "CEF:0" in cef
        assert "threat-123" in cef
        assert "C2_Infrastructure" in cef
        assert "10" in cef  # Critical severity
    
    def test_honeytoken_trigger_cef_format(self):
        """Test honeytoken trigger CEF formatting (critical)"""
        from app.siem_integration.formatter import SIEMFormatter
        
        formatter = SIEMFormatter()
        cef = formatter.format_honeytoken_trigger_as_cef(
            honeytoken_id="honey-123",
            token_type="aws_access_key",
            trigger_source="cloudwatch",
            threat_id="threat-456"
        )
        
        assert "CEF:0" in cef
        assert "honeytoken_trigger" in cef
        assert "10" in cef  # Critical severity
        assert "honey-123" in cef
    
    def test_stix_indicator_format(self):
        """Test STIX 2.1 Indicator formatting"""
        from app.siem_integration.formatter import SIEMFormatter
        
        formatter = SIEMFormatter()
        stix = formatter.format_stix_indicator(
            ioc_value="malicious.com",
            ioc_type="domain",
            category="Phishing",
            confidence=0.85,
            threat_id="threat-789"
        )
        
        assert stix["type"] == "indicator"
        assert stix["pattern_type"] == "stix"
        assert "malicious.com" in stix["pattern"]
        assert stix["confidence"] == "high"
        assert "phishing" in stix["labels"]
    
    def test_stix_sighting_format(self):
        """Test STIX 2.1 Sighting formatting"""
        from app.siem_integration.formatter import SIEMFormatter
        from datetime import datetime
        
        formatter = SIEMFormatter()
        stix = formatter.format_stix_sighting(
            indicator_id="indicator--test",
            sighting_source="sensor-1"
        )
        
        assert stix["type"] == "sighting"
        assert stix["sighting_of_ref"] == "indicator--test"
        assert stix["where_sighted_refs"][0]["source_name"] == "sensor-1"


class TestEgressControl:
    """Egress Control Tests"""
    
    def test_egress_domain_validation(self):
        """Test domain whitelist validation"""
        from app.integrations.egress_control import EgressControlledClient
        
        client = EgressControlledClient()
        
        # Valid domain
        try:
            client._validate_domain("https://abuse.ch/api")
        except ValueError:
            pytest.fail("Should allow abuse.ch domain")
        
        # Invalid domain
        try:
            client._validate_domain("https://evil.com/api")
            pytest.fail("Should block evil.com domain")
        except ValueError as e:
            assert "not in ALLOWED_EGRESS_DOMAINS" in str(e)
    
    def test_egress_timeout_is_10_seconds(self):
        """Test that default timeout is 10 seconds"""
        from app.integrations.egress_control import EgressControlledClient
        
        client = EgressControlledClient()
        assert client.timeout == 10.0
    
    def test_allowed_domains_list(self):
        """Test that all required domains are in ALLOWED_EGRESS_DOMAINS"""
        from app.integrations.egress_control import EgressControlledClient
        
        required_domains = [
            "abuse.ch",
            "virustotal.com",
            "otx.alienvault.com",
            "threatconnect.com",
            "misp.example.com",
            "api.crowdstrike.com",
            "firehose.example.com",
            "api.shodan.io",
        ]
        
        for domain in required_domains:
            assert domain in EgressControlledClient.ALLOWED_DOMAINS


class TestHoneypotManager:
    """Honeypot Deployment Manager Tests"""

    @patch('app.deception.honeygrid.docker.DockerClient')
    def test_connects_to_docker_proxy_not_socket(self, mock_docker_client):
        """Test HoneyGridManager connects to docker-proxy:2375 (NOT docker.sock)"""
        manager = HoneypotManager()
        mock_docker_client.assert_called_once_with(base_url="tcp://docker-proxy:2375")
        # Verify docker.from_env() was NOT called
        assert not any(call[0][0] == 'from_env' for call in mock_docker_client.call_args_list)

    @patch('app.deception.honeygrid.docker.DockerClient')
    async def test_deploy_honeypot_raises_valueerror_for_invalid_ip(self, mock_docker_client):
        """Test deploy_honeypot() raises ValueError for invalid IP"""
        manager = HoneypotManager()
        threat_id = uuid4()
        
        with pytest.raises(ValueError) as exc_info:
            await manager.deploy_honeypot(threat_id, "invalid-ip", "C2_Infrastructure")
        
        assert "Invalid attacker IP" in str(exc_info.value)

    @patch('app.deception.honeygrid.docker.DockerClient')
    async def test_deploy_honeypot_valid_ip_succeeds(self, mock_docker_client):
        """Test deploy_honeypot() succeeds with valid IP"""
        mock_container = MagicMock()
        mock_container.id = "container123"
        mock_docker_client.return_value.containers.run.return_value = mock_container
        
        manager = HoneypotManager()
        threat_id = uuid4()
        
        deployment = await manager.deploy_honeypot(threat_id, "192.168.1.1", "C2_Infrastructure")
        
        assert deployment.threat_id == threat_id
        assert deployment.attacker_ip == "192.168.1.1"
        assert deployment.container_id == "container123"

    def test_parse_cowrie_logs_extracts_source_ips(self):
        """Test _parse_cowrie_logs() extracts source IPs from login events"""
        manager = HoneypotManager()
        
        raw_logs = """{"eventid": "cowrie.login.failed", "src_ip": "192.168.1.100"}
{"eventid": "cowrie.login.success", "src_ip": "10.0.0.50"}
{"eventid": "cowrie.command.input", "input": "ls -la"}"""
        
        iocs = manager._parse_cowrie_logs(raw_logs)
        
        # Should extract 2 IPs from login events
        ip_iocs = [ioc for ioc in iocs if ioc["type"] == "ip"]
        assert len(ip_iocs) == 2
        assert ip_iocs[0]["value"] == "192.168.1.100"
        assert ip_iocs[1]["value"] == "10.0.0.50"
        
        # Should extract 1 command
        cmd_iocs = [ioc for ioc in iocs if ioc["type"] == "command"]
        assert len(cmd_iocs) == 1
        assert "ls -la" in cmd_iocs[0]["value"]

    @patch('app.deception.honeygrid.docker.DockerClient')
    @patch('app.deception.honeygrid.EgressControlledClient')
    async def test_extract_iocs_and_inject_calls_signals_inject(self, mock_egress_client, mock_docker_client):
        """Test extract_iocs_and_inject() calls /signals/inject for each IOC"""
        mock_container = MagicMock()
        mock_container.logs.return_value = b'{"eventid": "cowrie.login.failed", "src_ip": "192.168.1.100"}'
        mock_docker_client.return_value.containers.get.return_value = mock_container
        
        mock_async_client = AsyncMock()
        mock_egress_client.return_value.__aenter__.return_value = mock_async_client
        
        manager = HoneypotManager()
        tenant_id = uuid4()
        
        await manager.extract_iocs_and_inject("container123", tenant_id)
        
        # Verify post was called with correct endpoint
        mock_async_client.post.assert_called()
        call_args = mock_async_client.post.call_args
        assert call_args[0][0] == "http://qmind:8001/signals/inject"
        
        # Verify IOC data in the call
        json_data = call_args[1]["json"]
        assert json_data["indicator_value"] == "192.168.1.100"
        assert json_data["indicator_type"] == "ip"
        assert json_data["source"] == "honeypot"
        assert json_data["confidence"] == 0.95
        assert json_data["tenant_id"] == str(tenant_id)
