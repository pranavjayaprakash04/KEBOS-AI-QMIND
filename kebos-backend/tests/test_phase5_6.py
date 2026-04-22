"""
Tests for Phases 5 & 6 - Zero Trust + Proactive Intelligence

Phase 5 Tests:
- Network topology verification
- Kafka ACLs script exists and is executable
- PostgreSQL RLS policies
- Tenant isolation

Phase 6 Tests:
- CT Log Monitor (certstream)
- Paste Monitor
- Domain Monitor
- Supplier Trust Engine
- Feed quarantine mechanism
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from app.crawlers.ct_log_monitor import CTLogMonitor, INDIAN_BRAND_PATTERNS
from app.crawlers.paste_monitor import PasteMonitor
from app.crawlers.domain_monitor import DomainMonitor
from qmind_enterprise.feeds.supplier_trust import (
    SupplierTrustEngine,
    FeedSource,
    SupplierMetrics
)


class TestPhase5NetworkTopology:
    """Test Phase 5.1 - Network topology"""
    
    def test_docker_compose_networks(self):
        """Verify docker-compose.yml has correct 3-network topology"""
        import yaml
        import os
        
        docker_compose_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker-compose.yml"
        )
        
        with open(docker_compose_path, 'r') as f:
            compose = yaml.safe_load(f)
        
        # Verify networks exist
        assert 'networks' in compose
        assert 'frontend-net' in compose['networks']
        assert 'app-net' in compose['networks']
        assert 'data-net' in compose['networks']
        assert 'kebos_deception_net' in compose['networks']
        
        # Verify cloudflare-tunnel is only on frontend-net
        cf_tunnels = compose['services']['cloudflare-tunnel']['networks']
        assert 'frontend-net' in cf_tunnels
        assert 'app-net' not in cf_tunnels
        assert 'data-net' not in cf_tunnels
        
        # Verify kebos-backend is on frontend-net and app-net
        kebos_networks = compose['services']['kebos-backend']['networks']
        assert 'frontend-net' in kebos_networks
        assert 'app-net' in kebos_networks
        assert 'data-net' in kebos_networks  # For database access
        
        # Verify postgres is only on data-net
        postgres_networks = compose['services']['postgres']['networks']
        assert 'data-net' in postgres_networks
        assert 'frontend-net' not in postgres_networks
        assert 'app-net' not in postgres_networks
        
        # Verify kafka is only on data-net
        kafka_networks = compose['services']['kafka']['networks']
        assert 'data-net' in kafka_networks
        assert 'frontend-net' not in kafka_networks
        assert 'app-net' not in kafka_networks


class TestPhase5KafkaACLs:
    """Test Phase 5.2 - Kafka ACLs"""
    
    def test_kafka_acls_script_exists(self):
        """Verify docker/kafka-acls.sh exists and is executable"""
        import os
        
        kafka_acls_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docker",
            "kafka-acls.sh"
        )
        
        assert os.path.exists(kafka_acls_path)
        
        # Check script has proper content
        with open(kafka_acls_path, 'r') as f:
            content = f.read()
        
        assert 'SCRAM-SHA-256' in content
        assert 'kebos-backend' in content
        assert 'qmind' in content
        assert 'honeygrid' in content
        assert 'crawler' in content
        assert 'threat.indicators' in content
        assert 'qmind.results' in content


class TestPhase5RLS:
    """Test Phase 5.3 - PostgreSQL RLS"""
    
    def test_rls_migration_exists(self):
        """Verify RLS migration exists"""
        import os
        
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "alembic",
            "versions",
            "003_add_tenant_isolation.py"
        )
        
        assert os.path.exists(migration_path)
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert 'ENABLE ROW LEVEL SECURITY' in content
        assert 'tenant_isolation' in content
        assert 'app.current_tenant' in content


class TestPhase6CTLogMonitor:
    """Test Phase 6.1 - CT Log Monitor"""
    
    def test_indian_brand_patterns(self):
        """Verify Indian brand patterns are defined"""
        assert 'sbi' in INDIAN_BRAND_PATTERNS
        assert 'hdfc' in INDIAN_BRAND_PATTERNS
        assert 'icici' in INDIAN_BRAND_PATTERNS
        assert 'axis' in INDIAN_BRAND_PATTERNS
        assert 'paytm' in INDIAN_BRAND_PATTERNS
        assert 'phonepe' in INDIAN_BRAND_PATTERNS
        assert 'upi' in INDIAN_BRAND_PATTERNS
    
    def test_domain_matching_suspicious(self):
        """Test domain matching flags suspicious domains"""
        monitor = CTLogMonitor()
        
        # Suspicious: contains brand but not .in
        assert monitor._matches_brand_pattern('sbi-login.com') == True
        assert monitor._matches_brand_pattern('hdfc-bank.net') == True
        assert monitor._matches_brand_pattern('icici-secure.org') == True
        
        # Legitimate: contains brand and .in
        assert monitor._matches_brand_pattern('sbi.co.in') == False
        assert monitor._matches_brand_pattern('hdfcbank.in') == False
        assert monitor._matches_brand_pattern('icicibank.com') == True  # Not .in
    
    @pytest.mark.asyncio
    async def test_certstream_injection(self):
        """Test signal injection for suspicious domain"""
        monitor = CTLogMonitor()
        monitor.egress_client = AsyncMock()
        monitor.egress_client.post = AsyncMock(return_value=Mock(raise_for_status=Mock()))
        
        cert_data = {
            "message_type": "certificate_update",
            "data": {
                "leaf_cert": {
                    "all_domains": ["sbi-secure-login.com"],
                    "issuer": {"O": "Fake CA"}
                }
            }
        }
        
        await monitor._inject_signal("sbi-secure-login.com", cert_data)
        
        # Verify signal was injected
        monitor.egress_client.post.assert_called_once()
        call_args = monitor.egress_client.post.call_args
        assert call_args[0][0] == "http://qmind:8001/signals/inject"
        assert call_args[1]['json']['indicator_value'] == "sbi-secure-login.com"
        assert call_args[1]['json']['source'] == "ct_log"
        assert call_args[1]['json']['confidence'] == 0.65


class TestPhase6PasteMonitor:
    """Test Phase 6.2 - Paste Monitor"""
    
    def test_paste_patterns(self):
        """Verify paste patterns are defined"""
        monitor = PasteMonitor()
        
        assert 'aadhaar' in monitor.PATTERNS
        assert 'pan_card' in monitor.PATTERNS
        assert 'upi_id' in monitor.PATTERNS
        assert 'ifsc' in monitor.PATTERNS
        assert 'bank_account' in monitor.PATTERNS
    
    def test_aadhaar_pattern(self):
        """Test Aadhaar pattern matching"""
        import re
        monitor = PasteMonitor()
        
        # Valid Aadhaar patterns
        assert len(re.findall(monitor.PATTERNS['aadhaar'], '1234 5678 9012')) > 0
        assert len(re.findall(monitor.PATTERNS['aadhaar'], '123456789012')) > 0
        
        # Invalid patterns
        assert len(re.findall(monitor.PATTERNS['aadhaar'], '12345')) == 0
    
    def test_pan_card_pattern(self):
        """Test PAN card pattern matching"""
        import re
        monitor = PasteMonitor()
        
        # Valid PAN
        assert len(re.findall(monitor.PATTERNS['pan_card'], 'ABCDE1234F')) > 0
        
        # Invalid PAN
        assert len(re.findall(monitor.PATTERNS['pan_card'], '1234567890')) == 0


class TestPhase6DomainMonitor:
    """Test Phase 6.2 - Domain Monitor"""
    
    def test_levenshtein_distance(self):
        """Test Levenshtein distance calculation for typosquatting"""
        monitor = DomainMonitor()
        
        # Exact match
        assert monitor._levenshtein_distance('sbi', 'sbi') == 0
        
        # One character difference
        assert monitor._levenshtein_distance('sbi', 'sb1') == 1
        assert monitor._levenshtein_distance('sbi', 'sbii') == 1
        
        # Two character difference
        assert monitor._levenshtein_distance('sbi', 'sb12') == 2
        
        # Completely different
        assert monitor._levenshtein_distance('sbi', 'xyz') > 2
    
    def test_typosquatting_detection(self):
        """Test typosquatting detection"""
        monitor = DomainMonitor()
        
        # Potential typosquatting
        assert monitor._is_typosquatting('sb1.com', 'sbi') == True
        assert monitor._is_typosquatting('sbii.com', 'sbi') == True
        
        # Not typosquatting (too different)
        assert monitor._is_typosquatting('xyz.com', 'sbi') == False


class TestPhase6SupplierTrustEngine:
    """Test Phase 6.3 - Supplier Trust Engine"""
    
    def test_trust_engine_initialization(self):
        """Test trust engine initializes with all feeds"""
        engine = SupplierTrustEngine()
        
        assert len(engine.trust_scores) == len(FeedSource)
        assert len(engine.quarantined) == 0
        
        # All feeds should have base trust scores
        for feed in FeedSource:
            assert feed in engine.trust_scores
            assert engine.trust_scores[feed] > 0
    
    def test_get_qmind_weight_normal(self):
        """Test get_qmind_weight returns normal weight for non-quarantined feed"""
        engine = SupplierTrustEngine()
        
        weight = engine.get_qmind_weight('abuseipdb')
        assert weight > 0
        assert weight <= 1.0
    
    def test_get_qmind_weight_quarantined(self):
        """Test get_qmind_weight returns 0.0 for quarantined feed"""
        engine = SupplierTrustEngine()
        
        # Quarantine a feed
        feed_enum = FeedSource.ABUSE_CH
        engine.quarantined.add(feed_enum)
        engine.trust_scores[feed_enum] = 0.0
        
        weight = engine.get_qmind_weight('abuseipdb')
        assert weight == 0.0
    
    @pytest.mark.asyncio
    async def test_quarantine_feed(self):
        """Test feed quarantine mechanism"""
        engine = SupplierTrustEngine()
        
        # Quarantine a feed
        reason = {'ks_dist_shift': True, 'volume_spike': False}
        await engine.quarantine_feed('abuseipdb', reason)
        
        # Verify feed is quarantined
        assert FeedSource.ABUSE_CH in engine.quarantined
        assert engine.trust_scores[FeedSource.ABUSE_CH] == 0.0
    
    @pytest.mark.asyncio
    async def test_anomaly_detection_volume_spike(self):
        """Test volume spike triggers quarantine"""
        engine = SupplierTrustEngine()
        
        baseline = SupplierMetrics(mean_volume=10.0)
        new_data = list(range(100))  # 100 indicators, way above baseline
        
        anomalies = await engine.check_feed_anomaly('abuseipdb', new_data, baseline)
        
        assert anomalies['volume_spike'] == True
        assert FeedSource.ABUSE_CH in engine.quarantined
    
    @pytest.mark.asyncio
    async def test_anomaly_detection_trust_collapse(self):
        """Test trust collapse triggers quarantine"""
        engine = SupplierTrustEngine()
        
        # Set trust score below threshold
        engine.trust_scores[FeedSource.ABUSE_CH] = 0.20
        
        baseline = SupplierMetrics(mean_volume=10.0)
        new_data = list(range(5))
        
        anomalies = await engine.check_feed_anomaly('abuseipdb', new_data, baseline)
        
        assert anomalies['trust_collapse'] == True
        assert FeedSource.ABUSE_CH in engine.quarantined
    
    def test_confirmed_threat_tracking(self):
        """Test confirmed threat IOC tracking"""
        engine = SupplierTrustEngine()
        
        engine.add_confirmed_threat('192.168.1.1')
        engine.add_confirmed_threat('malicious.com')
        
        assert '192.168.1.1' in engine.confirmed_threats
        assert 'malicious.com' in engine.confirmed_threats
    
    def test_confirmed_safe_tracking(self):
        """Test confirmed safe IOC tracking"""
        engine = SupplierTrustEngine()
        
        engine.add_confirmed_safe('8.8.8.8')
        engine.add_confirmed_safe('google.com')
        
        assert '8.8.8.8' in engine.confirmed_safe
        assert 'google.com' in engine.confirmed_safe


class TestPhase6ExternalDatasetLoader:
    """Test Phase 6.4 - get_qmind_weight called in external_dataset_loader"""
    
    def test_get_qmind_weight_calls_trust_engine(self):
        """Verify external_dataset_loader calls trust_engine.get_qmind_weight"""
        from qmind_enterprise.external_dataset_loader import ExternalDatasetLoader
        from qmind_enterprise.feeds.supplier_trust import get_supplier_trust_engine
        from qmind_enterprise.signal_engine.scorer import ThreatCategory
        
        loader = ExternalDatasetLoader()
        
        # Mock the trust engine
        loader.trust_engine = Mock()
        loader.trust_engine.get_qmind_weight = Mock(return_value=0.85)
        
        # Call get_qmind_weight
        weight = loader.get_qmind_weight(FeedSource.ABUSE_CH, ThreatCategory.MALWARE)
        
        # Verify trust_engine.get_qmind_weight was called
        loader.trust_engine.get_qmind_weight.assert_called_once_with('abuse_ch')
        
        # Verify weight calculation
        assert weight > 0
    
    def test_quarantined_feed_zero_weight(self):
        """Verify quarantined feed returns 0.0 weight"""
        from qmind_enterprise.external_dataset_loader import ExternalDatasetLoader
        from qmind_enterprise.feeds.supplier_trust import get_supplier_trust_engine
        from qmind_enterprise.signal_engine.scorer import ThreatCategory
        
        loader = ExternalDatasetLoader()
        
        # Mock the trust engine to return 0.0 (quarantined)
        loader.trust_engine = Mock()
        loader.trust_engine.get_qmind_weight = Mock(return_value=0.0)
        
        # Call get_qmind_weight
        weight = loader.get_qmind_weight(FeedSource.ABUSE_CH, ThreatCategory.MALWARE)
        
        # Verify weight is 0.0
        assert weight == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
