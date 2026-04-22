"""
Tests for CatBoost threat engine and Kafka producer.
Phase 2.2 - CatBoost scoring and Kafka publishing.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from app.threat_detection.catboost_engine import CatBoostThreatEngine, ThreatFeatures
from app.threat_detection.kafka_producer import ThreatIndicatorPublisher


class TestCatBoostThreatEngine:
    """Tests for CatBoostThreatEngine"""
    
    def test_score_returns_0_5_when_model_not_loaded(self):
        """Test that CatBoostThreatEngine.score() returns 0.5 when model not loaded"""
        engine = CatBoostThreatEngine()
        # Model path doesn't exist, so _model_loaded should be False
        features = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="malicious-domain.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        score = engine.score(features)
        assert score == 0.5
    
    def test_indian_brand_domain_gets_has_indian_brand_1(self):
        """Test that Indian brand domain gets has_indian_brand=1"""
        engine = CatBoostThreatEngine()
        
        # Test with Indian brand
        features_sbi = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="sbi-online.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_sbi.indicator_value)
        assert domain_features["has_indian_brand"] == 1
        
        # Test with HDFC
        features_hdfc = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="hdfcbank.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_hdfc.indicator_value)
        assert domain_features["has_indian_brand"] == 1
        
        # Test with UPI
        features_upi = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="upi-payment.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_upi.indicator_value)
        assert domain_features["has_indian_brand"] == 1
        
        # Test with non-Indian brand
        features_non_indian = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="example.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_non_indian.indicator_value)
        assert domain_features["has_indian_brand"] == 0
    
    def test_source_confidence_prior(self):
        """Test that source confidence priors are correctly assigned"""
        engine = CatBoostThreatEngine()
        
        assert engine._source_confidence_prior("ct_log") == 0.65
        assert engine._source_confidence_prior("paste_monitor") == 0.70
        assert engine._source_confidence_prior("honeypot") == 0.95
        assert engine._source_confidence_prior("network") == 0.50
        assert engine._source_confidence_prior("endpoint") == 0.60
        assert engine._source_confidence_prior("analyst_manual") == 0.80
        assert engine._source_confidence_prior("unknown") == 0.50
    
    def test_ip_is_indian_asn(self):
        """Test IP ASN check (simplified implementation)"""
        engine = CatBoostThreatEngine()
        # Current implementation always returns 0
        assert engine._ip_is_indian_asn("192.168.1.1") == 0
        assert engine._ip_is_indian_asn("8.8.8.8") == 0
    
    def test_extract_domain_features_entropy(self):
        """Test domain entropy calculation"""
        engine = CatBoostThreatEngine()
        
        # High entropy (random-looking)
        features_high = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="x7k9m2p4.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_high.indicator_value)
        assert domain_features["entropy"] > 0
        
        # Low entropy (repeating characters)
        features_low = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="aaaaaaaa.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_low.indicator_value)
        assert domain_features["entropy"] >= 0
    
    def test_extract_domain_features_subdomain_depth(self):
        """Test subdomain depth calculation"""
        engine = CatBoostThreatEngine()
        
        features_single = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="example.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_single.indicator_value)
        assert domain_features["subdomain_depth"] == 1
        
        features_multi = ThreatFeatures(
            source_ip="192.168.1.1",
            destination_ip="10.0.0.1",
            indicator_value="a.b.c.example.com",
            indicator_type="domain",
            source="ct_log",
            tenant_id="tenant-123"
        )
        domain_features = engine._extract_domain_features(features_multi.indicator_value)
        assert domain_features["subdomain_depth"] == 4


class TestThreatIndicatorPublisher:
    """Tests for ThreatIndicatorPublisher"""
    
    @pytest.mark.asyncio
    async def test_publish_sends_correct_message_to_kafka_topic(self):
        """Test that ThreatIndicatorPublisher.publish() sends correct message to Kafka topic"""
        publisher = ThreatIndicatorPublisher()
        
        # Mock the producer
        mock_producer = Mock()
        publisher._producer = mock_producer
        mock_producer.send_and_wait = Mock(return_value=asyncio.Future())
        mock_producer.send_and_wait.return_value.set_result(None)
        
        # Publish an indicator
        await publisher.publish(
            indicator_value="malicious-domain.com",
            indicator_type="domain",
            catboost_score=0.85,
            source="ct_log",
            tenant_id="tenant-123",
            tenant_type="enterprise"
        )
        
        # Verify send_and_wait was called with correct topic and message
        mock_producer.send_and_wait.assert_called_once()
        call_args = mock_producer.send_and_wait.call_args
        assert call_args[0][0] == "threat.indicators"
        
        message = call_args[1]["value"]
        assert message["indicator_value"] == "malicious-domain.com"
        assert message["indicator_type"] == "domain"
        assert message["catboost_score"] == 0.85
        assert message["source"] == "ct_log"
        assert message["tenant_id"] == "tenant-123"
        assert message["tenant_type"] == "enterprise"
        assert "timestamp" in message
    
    @pytest.mark.asyncio
    async def test_publisher_start_must_be_called_before_publish(self):
        """Test that publisher.start() must be called before publish() (else RuntimeError)"""
        publisher = ThreatIndicatorPublisher()
        # Don't call start(), so _producer is None
        
        with pytest.raises(RuntimeError, match="Publisher not started"):
            await publisher.publish(
                indicator_value="malicious-domain.com",
                indicator_type="domain",
                catboost_score=0.85,
                source="ct_log",
                tenant_id="tenant-123",
                tenant_type="enterprise"
            )
    
    @pytest.mark.asyncio
    async def test_start_initializes_producer(self):
        """Test that start() initializes the AIOKafkaProducer"""
        publisher = ThreatIndicatorPublisher()
        
        with patch('app.threat_detection.kafka_producer.AIOKafkaProducer') as mock_producer_class:
            mock_producer = Mock()
            mock_producer.start = Mock(return_value=asyncio.Future())
            mock_producer.start.return_value.set_result(None)
            mock_producer_class.return_value = mock_producer
            
            await publisher.start("localhost:9092")
            
            # Verify producer was created with correct parameters
            mock_producer_class.assert_called_once()
            call_kwargs = mock_producer_class.call_args[1]
            assert call_kwargs["bootstrap_servers"] == "localhost:9092"
            assert call_kwargs["compression_type"] == "lz4"
            
            # Verify start was called
            mock_producer.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_stops_producer(self):
        """Test that stop() stops the AIOKafkaProducer"""
        publisher = ThreatIndicatorPublisher()
        
        mock_producer = Mock()
        mock_producer.stop = Mock(return_value=asyncio.Future())
        mock_producer.stop.return_value.set_result(None)
        publisher._producer = mock_producer
        
        await publisher.stop()
        
        mock_producer.stop.assert_called_once()
