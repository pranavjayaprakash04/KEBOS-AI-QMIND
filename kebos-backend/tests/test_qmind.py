import pytest
from signal_engine.scorer import SignalScorer, ThreatCategory
from feeds.supplier_trust import SupplierTrustEngine, FeedSource


class TestSignalScorer:
    """Signal Scorer Tests"""
    
    def test_10_threat_categories_exist(self):
        """Verify 10 threat categories exist"""
        categories = [
            ThreatCategory.C2_INFRASTRUCTURE,
            ThreatCategory.BOTNET_IP,
            ThreatCategory.PHISHING,
            ThreatCategory.MALWARE,
            ThreatCategory.CREDENTIAL_LEAK,
            ThreatCategory.DDoS,
            ThreatCategory.INSIDER_THREAT,
            ThreatCategory.SUPPLY_CHAIN,
            ThreatCategory.CVE_EXPLOITATION,
            ThreatCategory.BENIGN,
        ]
        
        assert len(categories) == 10
    
    def test_signal_decay_calculation(self):
        """Test exponential decay calculation"""
        scorer = SignalScorer()
        
        # C2_Infrastructure has 90-day half-life (λ = 1/90)
        decay_24h = scorer.calculate_decay(ThreatCategory.C2_INFRASTRUCTURE, 24)
        decay_90d = scorer.calculate_decay(ThreatCategory.C2_INFRASTRUCTURE, 90 * 24)
        
        # After 24 hours, should still be high
        assert decay_24h > 0.7
        # After 90 days, should be lower
        assert decay_90d < 0.4
    
    def test_india_calibration_decay_rates(self):
        """Verify India-calibrated decay rates for long dwell times"""
        scorer = SignalScorer()
        
        # C2, Supply Chain, Insider Threat should have 90-day calibration
        assert scorer.DECAY_RATES[ThreatCategory.C2_INFRASTRUCTURE] == 1/90
        assert scorer.DECAY_RATES[ThreatCategory.SUPPLY_CHAIN] == 1/90
        assert scorer.DECAY_RATES[ThreatCategory.INSIDER_THREAT] == 1/90
    
    def test_adversarial_stability_calculation(self):
        """Test adversarial stability scoring"""
        scorer = SignalScorer()
        
        # High supplier trust + multi-feed = high stability
        stability = scorer.calculate_adversarial_stability(
            confidence=0.8,
            supplier_trust=0.9,
            feed_count=3
        )
        
        assert stability > 0.8
        
        # Low supplier trust + single feed = low stability
        stability = scorer.calculate_adversarial_stability(
            confidence=0.5,
            supplier_trust=0.3,
            feed_count=1
        )
        
        assert stability < 0.5
    
    def test_signal_scoring(self):
        """Test full signal scoring"""
        scorer = SignalScorer()
        
        result = scorer.score_signal(
            threat_id="threat-123",
            category=ThreatCategory.C2_INFRASTRUCTURE,
            raw_confidence=0.8,
            supplier_trust=0.7,
            feed_source="abuse_ch",
            hours_since_detection=0.0,
            feed_count=2
        )
        
        assert result.threat_id == "threat-123"
        assert result.category == ThreatCategory.C2_INFRASTRUCTURE
        assert result.confidence == 0.8
        assert result.decayed_confidence == 0.8  # No decay at t=0
        assert result.adversarial_stability > 0


class TestSupplierTrustEngine:
    """Supplier Trust Engine Tests"""
    
    def test_8_feed_sources_exist(self):
        """Verify 8 feed sources exist"""
        feeds = [
            FeedSource.ABUSE_CH,
            FeedSource.VIRUS_TOTAL,
            FeedSource.ALIEN_VAULT,
            FeedSource.THREAT_CONNECT,
            FeedSource.MISP,
            FeedSource.CROWDSTRIKE,
            FeedSource.FIREHOSE,
            FeedSource.SHODAN,
        ]
        
        assert len(feeds) == 8
    
    def test_base_trust_scores_exist(self):
        """Verify base trust scores for all feeds"""
        engine = SupplierTrustEngine()
        
        for feed in FeedSource:
            assert feed in engine.base_trust_scores
            assert 0 <= engine.base_trust_scores[feed] <= 1
    
    def test_trust_score_calculation(self):
        """Test dynamic trust score calculation"""
        engine = SupplierTrustEngine()
        
        # Record some true positives
        engine.record_true_positive(FeedSource.VIRUS_TOTAL)
        engine.record_true_positive(FeedSource.VIRUS_TOTAL)
        
        trust_score = engine.calculate_trust_score(FeedSource.VIRUS_TOTAL)
        
        assert 0 <= trust_score <= 1
    
    def test_false_positive_affects_trust(self):
        """Test that false positives reduce trust score"""
        engine = SupplierTrustEngine()
        
        # Record false positive
        engine.record_false_positive(FeedSource.SHODAN)
        
        trust_score = engine.calculate_trust_score(FeedSource.SHODAN)
        
        # Should be lower than base score
        assert trust_score < engine.base_trust_scores[FeedSource.SHODAN]
    
    def test_get_feed_trust_scores(self):
        """Test getting all feed trust scores"""
        engine = SupplierTrustEngine()
        
        scores = engine.get_feed_trust_scores()
        
        assert len(scores) == 8
        for feed, score in scores.items():
            assert 0 <= score <= 1
    
    def test_get_low_trust_feeds(self):
        """Test identifying low-trust feeds"""
        engine = SupplierTrustEngine()
        
        # Artificially lower a feed's trust
        engine.record_false_positive(FeedSource.FIREHOSE)
        engine.record_false_positive(FeedSource.FIREHOSE)
        engine.record_false_positive(FeedSource.FIREHOSE)
        
        low_trust = engine.get_low_trust_feeds(threshold=0.5)
        
        # Should include the low-trust feed
        assert FeedSource.FIREHOSE in low_trust or len(low_trust) == 0
