"""
Session 25 Tests - SIEM Integration Updates
Tests for CEF forwarder, Splunk HEC, enrich endpoint, STIX bundle, threat actor profiles, and timeline endpoint.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.siem_integration.cef_forwarder import get_cef_forwarder
from app.siem_integration.splunk_hec import get_splunk_hec_client
from app.tip.mitre_mapping import THREAT_ACTOR_PROFILES, get_threat_actor_profile


def test_cef_format_produces_valid_cef_string():
    """Test CEF format produces valid CEF string starting with 'CEF:0|Pynevera'"""
    threat_event = {
        "lead_category": "Phishing",
        "status": "CONFIRMED_THREAT",
        "source_ip": "192.168.1.100",
        "indicator_value": "evil.com",
        "confidence": 0.85,
        "mitre_techniques": ["T1566.002"],
        "tenant_id": "tenant-123",
        "source": "qmind"
    }
    
    cef_line = get_cef_forwarder().format_event(threat_event)
    
    # Verify CEF format starts with correct vendor
    assert cef_line.startswith("CEF:0|Pynevera Technologies|KebosAI|1.0")
    assert "QMind-Phishing" in cef_line
    assert "Phishing Domain Detected" in cef_line
    assert "|10|" in cef_line  # Severity 10 for CONFIRMED_THREAT
    assert "src=192.168.1.100" in cef_line
    assert "dst=evil.com" in cef_line
    assert "confidence=0.8500" in cef_line
    assert "cs1Label=MITRETechniques" in cef_line
    assert "cs2Label=TenantID" in cef_line
    assert "cs3Label=DetectionSource" in cef_line


@pytest.mark.asyncio
async def test_splunk_hec_skips_when_not_configured():
    """Test Splunk HEC skips when not configured (no HTTP call when token is empty)"""
    # Ensure Splunk HEC is not configured
    get_splunk_hec_client()._ready = False
    get_splunk_hec_client().token = ""
    
    threat_event = {
        "indicator_value": "evil.com",
        "lead_category": "Malware",
        "confidence": 0.85,
        "category_scores": {},
        "reversibility": "REVERSIBLE",
        "mitre_techniques": ["T1059"],
        "status": "CONFIRMED_THREAT",
        "tenant_id": "tenant-123",
        "source": "qmind"
    }
    
    # Should return early without making HTTP call
    result = await get_splunk_hec_client().send_event(threat_event)
    
    # Returns None when not configured
    assert result is None


@pytest.mark.asyncio
async def test_enrich_endpoint_returns_category_scores():
    """Test enrich endpoint returns category scores with 10 keys"""
    from app.siem_integration.router import enrich_indicator
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    # Mock current user
    mock_user = Mock()
    mock_user.tenant_id = "tenant-123"
    mock_user.tenant_type = "enterprise"
    
    # Mock request as proper Starlette Request
    mock_request = Mock(spec=StarletteRequest)
    mock_request.state = Mock()
    
    # Mock QMind response with 10 category scores
    mock_response_data = {
        "lead_category": "Malware",
        "confidence": 0.85,
        "category_scores": {
            "Phishing": 0.1,
            "Malware": 0.9,
            "C2_Infrastructure": 0.3,
            "Botnet_IP": 0.2,
            "Credential_Leak": 0.1,
            "Supply_Chain": 0.05,
            "Insider_Threat": 0.1,
            "DDoS": 0.05,
            "CVE_Exploitation": 0.2,
            "Benign": 0.1
        },
        "mitre_techniques": ["T1059"],
        "status": "CONFIRMED_THREAT"
    }
    
    with patch('app.siem_integration.router.get_current_user') as mock_get_user:
        mock_get_user.return_value = mock_user
        
        with patch('app.siem_integration.router.EgressControlledClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await enrich_indicator(
                indicator_value="evil.com",
                indicator_type="domain",
                request=mock_request,
                current_user=mock_user
            )
            
            # Verify category_scores has 10 keys
            assert "category_scores" in result
            assert len(result["category_scores"]) == 10
            # Verify all expected categories are present
            expected_categories = [
                "Phishing", "Malware", "C2_Infrastructure", "Botnet_IP",
                "Credential_Leak", "Supply_Chain", "Insider_Threat",
                "DDoS", "CVE_Exploitation", "Benign"
            ]
            for category in expected_categories:
                assert category in result["category_scores"]


@pytest.mark.asyncio
async def test_stix_bundle_returns_valid_json():
    """Test STIX bundle endpoint returns valid JSON with 'type': 'bundle'"""
    from app.siem_integration.router import get_stix_bundle
    from starlette.requests import Request as StarletteRequest
    
    # Mock current user
    mock_user = Mock()
    mock_user.tenant_id = "tenant-123"
    
    # Create async context manager mock
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        Mock(
            indicator_type='domain',
            indicator_value='evil.com',
            lead_category='Malware',
            confidence=0.85,
            first_seen=None,
            last_seen=None
        )
    ]
    
    # Create a proper async context manager
    class AsyncContextManagerMock:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, *args):
            pass
    
    mock_db_pool = Mock()
    mock_db_pool.acquire = Mock(return_value=AsyncContextManagerMock())
    
    # Mock request with db_pool
    mock_request = Mock(spec=StarletteRequest)
    mock_request.app = Mock()
    mock_request.app.state = Mock()
    mock_request.app.state.db_pool = mock_db_pool
    
    with patch('app.siem_integration.router.get_current_user') as mock_get_user:
        mock_get_user.return_value = mock_user
        
        result = await get_stix_bundle(limit=500, request=mock_request, current_user=mock_user)
        
        # Verify STIX bundle structure
        assert isinstance(result, dict)
        assert "type" in result
        assert result["type"] == "bundle"
        assert "objects" in result


def test_silverterrier_in_threat_actors():
    """Test SilverTerrier threat actor profile exists in THREAT_ACTOR_PROFILES"""
    profile = get_threat_actor_profile("SilverTerrier")
    
    assert profile is not None, "SilverTerrier profile should exist"
    assert profile["name"] == "SilverTerrier"
    assert profile["alias"] is None
    assert "Indian corporates" in profile["targets"]
    assert "BEC victims" in profile["targets"]
    assert "Financial services" in profile["targets"]
    assert "T1566.002" in profile["mitre_techniques"]
    assert "T1078" in profile["mitre_techniques"]
    assert "T1071" in profile["mitre_techniques"]
    assert "T1036" in profile["mitre_techniques"]
    assert profile["primary_ttps"] == "Business email compromise, banking trojans, spear-phishing"
    assert profile["region"] == "India"
    assert profile["threat_level"] == "HIGH"
    assert "Nigerian threat actor" in profile["description"]


def test_revil_in_threat_actors():
    """Test REvil Affiliates threat actor profile exists in THREAT_ACTOR_PROFILES"""
    profile = get_threat_actor_profile("REvil Affiliates")
    
    assert profile is not None, "REvil Affiliates profile should exist"
    assert profile["name"] == "REvil Affiliates"
    assert profile["alias"] == "Sodinokibi"
    assert "Indian SME infrastructure" in profile["targets"]
    assert "Manufacturing" in profile["targets"]
    assert "Healthcare" in profile["targets"]
    assert "T1486" in profile["mitre_techniques"]
    assert "T1490" in profile["mitre_techniques"]
    assert "T1489" in profile["mitre_techniques"]
    assert "T1059" in profile["mitre_techniques"]
    assert profile["primary_ttps"] == "Ransomware-as-a-service, double extortion, RDP exploitation"
    assert profile["region"] == "India"
    assert profile["threat_level"] == "CRITICAL"
    assert "REvil (Sodinokibi)" in profile["description"]


@pytest.mark.asyncio
async def test_timeline_endpoint_returns_buckets():
    """Test forensic timeline endpoint returns list of time buckets"""
    from uuid import uuid4
    from app.auth.services import UserProfile
    from unittest.mock import MagicMock
    import sys
    
    # Mock current user
    mock_user = Mock(spec=UserProfile)
    mock_user.tenant_id = uuid4()
    
    # Mock case row as dict
    case_id = str(uuid4())
    threat_event_id = str(uuid4())
    mock_case = {'id': case_id, 'threat_event_id': threat_event_id}
    
    # Mock timeline rows
    mock_bucket = Mock()
    mock_bucket.isoformat = Mock(return_value="2024-01-01T10:00:00")
    mock_row1 = {
        'bucket': mock_bucket,
        'source_type': "qmind",
        'event_count': 5,
        'peak_confidence': 0.9,
        'min_confidence': 0.7
    }
    
    # Mock db connection
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = mock_case
    mock_conn.fetch.return_value = [mock_row1]
    
    # Create a proper async context manager
    class AsyncContextManagerMock:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, *args):
            pass
    
    mock_db_pool = Mock()
    mock_db_pool.acquire = Mock(return_value=AsyncContextManagerMock())
    
    # Create mock app
    mock_app = MagicMock()
    mock_app.state.db_pool = mock_db_pool
    
    # Patch sys.modules to inject mock app.main
    if 'app.main' in sys.modules:
        original_app_main = sys.modules['app.main']
    else:
        original_app_main = None
    
    mock_main_module = MagicMock()
    mock_main_module.app = mock_app
    sys.modules['app.main'] = mock_main_module
    
    try:
        from app.cases.router import get_case_timeline
        
        result = await get_case_timeline(
            case_id=uuid4(),
            current_user=mock_user
        )
        
        # Verify result is a list
        assert isinstance(result, list)
        # Verify bucket structure
        if len(result) > 0:
            assert "bucket" in result[0]
            assert "source_type" in result[0]
            assert "event_count" in result[0]
            assert "peak_confidence" in result[0]
            assert "min_confidence" in result[0]
    finally:
        # Restore original module
        if original_app_main is None:
            sys.modules.pop('app.main', None)
        else:
            sys.modules['app.main'] = original_app_main


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
