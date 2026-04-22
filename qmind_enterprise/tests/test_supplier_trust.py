"""
Tests for SupplierTrustEngine and ExternalDatasetLoader quarantine functionality
"""
import pytest
from feeds.supplier_trust import SupplierTrustEngine, FeedSource, get_supplier_trust_engine
from external_dataset_loader import ExternalDatasetLoader, get_dataset_loader
from signal_engine.scorer import ThreatCategory


def test_get_qmind_weight_returns_zero_for_quarantined_feed():
    """Test that get_qmind_weight() returns 0.0 for quarantined feed"""
    engine = get_supplier_trust_engine()
    
    # Normal feed should return non-zero weight
    normal_weight = engine.get_qmind_weight("abuseipdb")
    assert normal_weight > 0.0, "Normal feed should have non-zero weight"
    
    # Quarantine the feed
    engine.quarantine_feed("abuseipdb")
    
    # Quarantined feed should return 0.0
    quarantined_weight = engine.get_qmind_weight("abuseipdb")
    assert quarantined_weight == 0.0, "Quarantined feed should return 0.0 weight"
    
    # Unquarantine and verify normal weight returns
    engine.unquarantine_feed("abuseipdb")
    restored_weight = engine.get_qmind_weight("abuseipdb")
    assert restored_weight > 0.0, "Unquarantined feed should have non-zero weight"


def test_external_dataset_loader_skips_quarantined_feed():
    """Test that external_dataset_loader skips quarantined feed (does not contribute to scoring)"""
    import asyncio
    
    loader = get_dataset_loader()
    engine = get_supplier_trust_engine()
    
    # Quarantine abuseipdb feed
    engine.quarantine_feed("abuseipdb")
    
    # Create mock feed data with indicators from multiple feeds
    feed_data = {
        FeedSource.ABUSEIPDB: [
            {"category": "Malware", "indicator": "192.168.1.1"},
            {"category": "Phishing", "indicator": "evil.com"},
        ],
        FeedSource.FEODO: [
            {"category": "C2_Infrastructure", "indicator": "10.0.0.1"},
        ],
        FeedSource.MALWAREBAZAAR: [
            {"category": "Malware", "indicator": "malware.exe"},
        ],
    }
    
    # Run async test
    async def test_ingest():
        enriched = await loader.ingest_indicators(feed_data)
        
        # Should only have indicators from non-quarantined feeds (FEODO + MALWAREBAZAAR)
        assert len(enriched) == 2, f"Expected 2 indicators from non-quarantined feeds, got {len(enriched)}"
        
        # Verify no indicators from quarantined abuseipdb
        feed_sources = [ind["feed_source"] for ind in enriched]
        assert "abuseipdb" not in feed_sources, "Quarantined feed should not contribute indicators"
        assert "feodo" in feed_sources, "Non-quarantined feed should contribute indicators"
        assert "malwarebazaar" in feed_sources, "Non-quarantined feed should contribute indicators"
        
        # Clean up
        engine.unquarantine_feed("abuseipdb")
    
    asyncio.run(test_ingest())


def test_get_qmind_weight_unknown_feed_returns_zero():
    """Test that get_qmind_weight() returns 0.0 for unknown feed name"""
    engine = get_supplier_trust_engine()
    
    # Unknown feed should return 0.0
    unknown_weight = engine.get_qmind_weight("unknown_feed")
    assert unknown_weight == 0.0, "Unknown feed should return 0.0 weight"


def test_quarantine_feed_unknown_feed():
    """Test that quarantining an unknown feed logs warning but doesn't crash"""
    engine = get_supplier_trust_engine()
    
    # Should not crash for unknown feed
    engine.quarantine_feed("unknown_feed")
    
    # Verify no feeds are quarantined
    assert len(engine.quarantined) == 0, "Unknown feed should not be added to quarantine set"


def test_unquarantine_feed_unknown_feed():
    """Test that unquarantining an unknown feed logs warning but doesn't crash"""
    engine = get_supplier_trust_engine()
    
    # Should not crash for unknown feed
    engine.unquarantine_feed("unknown_feed")


def test_all_8_feeds_have_base_trust_scores():
    """Test that all 8 feeds have base trust scores configured"""
    engine = get_supplier_trust_engine()
    
    expected_feeds = [
        "abuseipdb", "feodo", "malwarebazaar", "nvd",
        "openphish", "phishtank", "urlhaus", "tranco"
    ]
    
    for feed_name in expected_feeds:
        weight = engine.get_qmind_weight(feed_name)
        assert weight > 0.0, f"Feed {feed_name} should have non-zero base trust score"
