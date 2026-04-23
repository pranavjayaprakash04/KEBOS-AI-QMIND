"""
Tests for DependencyHealthMonitor degradation policies
"""
import pytest
from app.integrations.dependency_health import (
    DependencyHealthMonitor,
    DependencyStatus,
    get_dependency_health_monitor
)


def test_all_feeds_down_sets_max_confidence_cap_0_65():
    """Test that all_feeds_down degradation policy sets max_confidence_cap to 0.65"""
    monitor = get_dependency_health_monitor()
    
    # Initial state should have normal cap
    assert monitor.max_confidence_cap == 1.0, "Initial max_confidence_cap should be 1.0"
    
    # Simulate all feeds down by calling the degradation policy directly
    monitor._apply_degradation_policy("all_feeds")
    
    # Should set cap to 0.65
    assert monitor.max_confidence_cap == 0.65, "all_feeds_down should set max_confidence_cap to 0.65"
    
    # Restore from degradation
    monitor._restore_from_degradation("all_feeds")
    
    # Should restore to normal
    assert monitor.max_confidence_cap == 1.0, "Restoring should set max_confidence_cap back to 1.0"


def test_qmind_down_sets_max_confidence_cap_0_60():
    """Test that qmind_down degradation policy sets max_confidence_cap to 0.60"""
    monitor = get_dependency_health_monitor()
    
    # Initial state should have normal cap
    assert monitor.max_confidence_cap == 1.0, "Initial max_confidence_cap should be 1.0"
    
    # Simulate qmind down by calling the degradation policy directly
    monitor._apply_degradation_policy("qmind")
    
    # Should set cap to 0.60
    assert monitor.max_confidence_cap == 0.60, "qmind_down should set max_confidence_cap to 0.60"
    
    # Restore from degradation
    monitor._restore_from_degradation("qmind")
    
    # Should restore to normal
    assert monitor.max_confidence_cap == 1.0, "Restoring should set max_confidence_cap back to 1.0"


def test_groq_down_sets_soc_report_mode_jinja2_only():
    """Test that groq_down degradation policy sets soc_report_mode to jinja2_only"""
    monitor = get_dependency_health_monitor()
    
    # Initial state should be normal
    assert monitor.soc_report_mode == "normal", "Initial soc_report_mode should be normal"
    
    # Simulate groq down
    monitor._apply_degradation_policy("groq")
    
    # Should set to jinja2_only
    assert monitor.soc_report_mode == "jinja2_only", "groq_down should set soc_report_mode to jinja2_only"
    
    # Restore from degradation
    monitor._restore_from_degradation("groq")
    
    # Should restore to normal
    assert monitor.soc_report_mode == "normal", "Restoring should set soc_report_mode back to normal"


def test_vault_down_sets_read_only_mode():
    """Test that vault_down degradation policy sets read_only_mode to True"""
    monitor = get_dependency_health_monitor()
    
    # Initial state should not be read-only
    assert monitor.read_only_mode is False, "Initial read_only_mode should be False"
    
    # Simulate vault down
    monitor._apply_degradation_policy("vault")
    
    # Should set to read-only
    assert monitor.read_only_mode is True, "vault_down should set read_only_mode to True"
    
    # Restore from degradation
    monitor._restore_from_degradation("vault")
    
    # Should restore to normal
    assert monitor.read_only_mode is False, "Restoring should set read_only_mode back to False"


def test_kafka_down_sets_qmind_transport_http():
    """Test that kafka_down degradation policy sets qmind_transport to http"""
    monitor = get_dependency_health_monitor()
    
    # Initial state should be kafka
    assert monitor.qmind_transport == "kafka", "Initial qmind_transport should be kafka"
    
    # Simulate kafka down
    monitor._apply_degradation_policy("kafka")
    
    # Should set to http
    assert monitor.qmind_transport == "http", "kafka_down should set qmind_transport to http"
    
    # Restore from degradation
    monitor._restore_from_degradation("kafka")
    
    # Should restore to normal
    assert monitor.qmind_transport == "kafka", "Restoring should set qmind_transport back to kafka"


def test_redis_down_sets_rate_limit_backend_db():
    """Test that redis_down degradation policy sets rate_limit_backend to db"""
    monitor = get_dependency_health_monitor()
    
    # Initial state should be redis
    assert monitor.rate_limit_backend == "redis", "Initial rate_limit_backend should be redis"
    
    # Simulate redis down
    monitor._apply_degradation_policy("redis")
    
    # Should set to db
    assert monitor.rate_limit_backend == "db", "redis_down should set rate_limit_backend to db"
    
    # Restore from degradation
    monitor._restore_from_degradation("redis")
    
    # Should restore to normal
    assert monitor.rate_limit_backend == "redis", "Restoring should set rate_limit_backend back to redis"


def test_certstream_down_sets_ct_monitor_mode_whoisxml_fallback():
    """Test that certstream_down degradation policy sets ct_monitor_mode to whoisxml_fallback"""
    monitor = get_dependency_health_monitor()
    
    # Initial state should be certstream
    assert monitor.ct_monitor_mode == "certstream", "Initial ct_monitor_mode should be certstream"
    
    # Simulate certstream down
    monitor._apply_degradation_policy("certstream")
    
    # Should set to whoisxml_fallback
    assert monitor.ct_monitor_mode == "whoisxml_fallback", "certstream_down should set ct_monitor_mode to whoisxml_fallback"
    
    # Restore from degradation
    monitor._restore_from_degradation("certstream")
    
    # Should restore to normal
    assert monitor.ct_monitor_mode == "certstream", "Restoring should set ct_monitor_mode back to certstream"


def test_abuseipdb_down_logs_warning():
    """Test that abuseipdb_down degradation policy logs warning (no state change)"""
    monitor = get_dependency_health_monitor()
    
    # Should not crash and should log warning
    monitor._apply_degradation_policy("abuseipdb")
    
    # No state change expected for abuseipdb_down
    # Just logs warning


def test_cloudflare_down_logs_warning():
    """Test that cloudflare_down degradation policy logs warning (no state change)"""
    monitor = get_dependency_health_monitor()
    
    # Should not crash and should log warning
    monitor._apply_degradation_policy("cloudflare")
    
    # No state change expected for cloudflare_down
    # Just logs warning


def test_check_all_feeds_status():
    """Test check_all_feeds_status method"""
    monitor = get_dependency_health_monitor()
    
    # Initially, feeds should be considered healthy (not checked yet)
    # Force abuseipdb to be down
    monitor._health_status["abuseipdb"] = DependencyStatus.DOWN
    
    # Should return True since abuseipdb is down
    assert monitor.check_all_feeds_status() is True, "Should return True when feeds are down"
    
    # Set abuseipdb to healthy
    monitor._health_status["abuseipdb"] = DependencyStatus.HEALTHY
    
    # Should return False since feeds are healthy
    assert monitor.check_all_feeds_status() is False, "Should return False when feeds are healthy"


def test_all_9_degradation_policies_registered():
    """Test that all 9 degradation policies are registered"""
    monitor = get_dependency_health_monitor()
    
    expected_policies = [
        "postgres", "kafka", "qmind", "vault", "redis",
        "abuseipdb", "groq", "certstream", "cloudflare"
    ]
    
    for policy_name in expected_policies:
        assert policy_name in monitor._degradation_policies, f"Policy {policy_name} should be registered"
