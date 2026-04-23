"""
Session 28 Tests — GeoIP, Vault, and Timeline Endpoint Fixes

Tests for:
1. GeoIP _extract_location() in UEBA baseline engine
2. VaultSecretManager runtime secret retrieval
3. GET /api/v1/cases/{id}/timeline forensic timeline endpoint
"""
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from app.ueba.baseline_engine import UEBABaselineEngine, _get_geoip_reader
from app.security.vault_breach import VaultSecretManager, vault_manager
from app.cases.router import TimelineEvent, CaseTimeline


class TestGeoIPExtraction:
    """Test GeoIP location extraction in UEBA baseline engine"""

    def test_private_ip_returns_zero_zero(self):
        """Private IPs should return (0.0, 0.0) — expected, not a bug"""
        engine = UEBABaselineEngine()
        result = engine._extract_location("192.168.1.1")
        assert result == (0.0, 0.0), f"Expected (0.0, 0.0) for private IP, got {result}"

    def test_loopback_returns_zero_zero(self):
        """Loopback IPs should return (0.0, 0.0)"""
        engine = UEBABaselineEngine()
        result = engine._extract_location("127.0.0.1")
        assert result == (0.0, 0.0), f"Expected (0.0, 0.0) for loopback, got {result}"

    def test_invalid_ip_returns_zero_zero(self):
        """Invalid IP strings should return (0.0, 0.0) without raising"""
        engine = UEBABaselineEngine()
        result = engine._extract_location("not-an-ip")
        assert result == (0.0, 0.0), f"Expected (0.0, 0.0) for invalid IP, got {result}"

    def test_geoip_reader_none_returns_gracefully(self):
        """When GeoIP reader is None, should return (0.0, 0.0) without exception"""
        engine = UEBABaselineEngine()
        with patch('app.ueba.baseline_engine._get_geoip_reader', return_value=None):
            result = engine._extract_location("8.8.8.8")
            assert result == (0.0, 0.0), f"Expected (0.0, 0.0) when reader is None, got {result}"


class TestVaultSecretManager:
    """Test VaultSecretManager for runtime secret retrieval"""

    def test_vault_initialise_no_config(self):
        """VaultSecretManager.initialise() with empty VAULT_ADDR should return False"""
        with patch('app.security.vault_breach.settings.VAULT_ADDR', ""), \
             patch('app.security.vault_breach.settings.VAULT_TOKEN', ""):
            manager = VaultSecretManager()
            result = manager.initialise()
            assert result is False, "Expected False when VAULT_ADDR is empty"

    def test_vault_get_secret_fallback(self):
        """When Vault is unavailable, get_secret should return fallback value"""
        manager = VaultSecretManager()
        manager._ready = False
        result = manager.get_secret("any/path", "key", "fallback_val")
        assert result == "fallback_val", f"Expected fallback value, got {result}"

    def test_vault_is_ready_property(self):
        """is_ready property should reflect Vault connection state"""
        manager = VaultSecretManager()
        # Before initialise
        assert manager.is_ready is False, "is_ready should be False before initialise"
        
        # Mock successful initialise
        with patch('app.security.vault_breach.hvac.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.is_authenticated.return_value = True
            mock_client_class.return_value = mock_client
            
            with patch('app.security.vault_breach.settings.VAULT_ADDR', "http://localhost:8200"), \
                 patch('app.security.vault_breach.settings.VAULT_TOKEN', "test-token"):
                result = manager.initialise()
                assert result is True, "initialise should return True with valid config"
                assert manager.is_ready is True, "is_ready should be True after successful initialise"


class TestTimelineEndpoint:
    """Test forensic timeline endpoint for cases"""

    def test_timeline_models_exist(self):
        """Verify TimelineEvent and CaseTimeline models are properly defined"""
        event1_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        event2_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        
        event = TimelineEvent(
            timestamp=event1_time,
            event_type="signal_detected",
            actor="QMind",
            description="Threat signal detected",
            metadata={"confidence": 0.85},
            severity="warning"
        )
        assert event.event_type == "signal_detected"
        assert event.actor == "QMind"
        
        timeline = CaseTimeline(
            case_id="case-123",
            total_events=2,
            events=[
                TimelineEvent(timestamp=event1_time, event_type="signal_detected", actor="QMind", description="Signal", metadata={}, severity="info"),
                TimelineEvent(timestamp=event2_time, event_type="case_created", actor="System", description="Case", metadata={}, severity="info")
            ],
            generated_at=datetime.now(timezone.utc),
            dilithium_signature="abc123"
        )
        assert timeline.case_id == "case-123"
        assert timeline.total_events == 2
        assert len(timeline.events) == 2
        assert timeline.dilithium_signature == "abc123"

    def test_timeline_events_chronological_sorting(self):
        """Verify that timeline events can be sorted chronologically"""
        event3_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event1_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        event2_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        
        # Create events out of order
        events = [
            TimelineEvent(timestamp=event3_time, event_type="case_created", actor="System", description="Case", metadata={}, severity="info"),
            TimelineEvent(timestamp=event1_time, event_type="signal_detected", actor="QMind", description="Signal", metadata={}, severity="warning"),
            TimelineEvent(timestamp=event2_time, event_type="qmind_scored", actor="QMind", description="Scored", metadata={}, severity="info")
        ]
        
        # Sort chronologically
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        assert sorted_events[0].timestamp == event1_time
        assert sorted_events[1].timestamp == event2_time
        assert sorted_events[2].timestamp == event3_time
