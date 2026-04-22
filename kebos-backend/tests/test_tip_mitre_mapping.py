"""
Tests for TIP MITRE mapping and threat actor profiles
"""
import pytest
from app.tip.mitre_mapping import (
    THREAT_ACTOR_PROFILES,
    get_threat_actor_profile,
    get_all_threat_actors,
    get_mitre_techniques,
    map_category_to_mitre
)


def test_all_5_threat_actor_profiles_exist():
    """Test that all 5 threat actor profiles exist in THREAT_ACTOR_PROFILES"""
    expected_actors = [
        "SideWinder",
        "Lazarus Group",
        "Bitter",
        "SilverTerrier",
        "REvil Affiliates"
    ]
    
    for actor_name in expected_actors:
        assert actor_name in THREAT_ACTOR_PROFILES, f"Threat actor '{actor_name}' should exist in THREAT_ACTOR_PROFILES"
    
    # Verify total count is 5
    assert len(THREAT_ACTOR_PROFILES) == 5, f"Expected 5 threat actor profiles, got {len(THREAT_ACTOR_PROFILES)}"


def test_silverterrier_profile_structure():
    """Test that SilverTerrier profile has correct structure"""
    profile = THREAT_ACTOR_PROFILES.get("SilverTerrier")
    assert profile is not None, "SilverTerrier profile should exist"
    
    # Verify required fields
    assert "aliases" in profile, "SilverTerrier should have aliases field"
    assert "targets" in profile, "SilverTerrier should have targets field"
    assert "techniques" in profile, "SilverTerrier should have techniques field"
    assert "description" in profile, "SilverTerrier should have description field"
    
    # Verify values
    assert profile["aliases"] is None, "SilverTerrier aliases should be None"
    assert "Indian corporates" in profile["targets"], "SilverTerrier should target Indian corporates"
    assert "BEC victims" in profile["targets"], "SilverTerrier should target BEC victims"
    assert "T1566.002" in profile["techniques"], "SilverTerrier should use T1566.002"
    assert "T1078" in profile["techniques"], "SilverTerrier should use T1078"
    assert "T1071" in profile["techniques"], "SilverTerrier should use T1071"
    assert "Nigerian BEC" in profile["description"], "SilverTerrier description should mention Nigerian BEC"


def test_revil_affiliates_profile_structure():
    """Test that REvil Affiliates profile has correct structure"""
    profile = THREAT_ACTOR_PROFILES.get("REvil Affiliates")
    assert profile is not None, "REvil Affiliates profile should exist"
    
    # Verify required fields
    assert "aliases" in profile, "REvil Affiliates should have aliases field"
    assert "targets" in profile, "REvil Affiliates should have targets field"
    assert "techniques" in profile, "REvil Affiliates should have techniques field"
    assert "description" in profile, "REvil Affiliates should have description field"
    
    # Verify values
    assert "Sodinokibi" in profile["aliases"], "REvil Affiliates should have Sodinokibi alias"
    assert "Indian SME infrastructure" in profile["targets"], "REvil Affiliates should target Indian SME"
    assert "T1486" in profile["techniques"], "REvil Affiliates should use T1486"
    assert "T1490" in profile["techniques"], "REvil Affiliates should use T1490"
    assert "T1489" in profile["techniques"], "REvil Affiliates should use T1489"
    assert "RaaS" in profile["description"], "REvil Affiliates description should mention RaaS"


def test_get_threat_actor_profile():
    """Test get_threat_actor_profile function"""
    # Test existing actor
    profile = get_threat_actor_profile("SideWinder")
    assert profile is not None, "Should return profile for existing actor"
    assert "APT-C-17" in profile["aliases"], "SideWinder should have APT-C-17 alias"
    
    # Test non-existing actor
    profile = get_threat_actor_profile("UnknownActor")
    assert profile == {}, "Should return empty dict for non-existing actor"


def test_get_all_threat_actors():
    """Test get_all_threat_actors function"""
    all_actors = get_all_threat_actors()
    assert isinstance(all_actors, dict), "Should return dict"
    assert len(all_actors) == 5, "Should return all 5 threat actors"
    
    # Verify all expected actors are present
    expected_actors = ["SideWinder", "Lazarus Group", "Bitter", "SilverTerrier", "REvil Affiliates"]
    for actor in expected_actors:
        assert actor in all_actors, f"Actor '{actor}' should be in all_actors"


def test_mitre_techniques_mapping():
    """Test MITRE techniques mapping for categories"""
    # Test existing category
    techniques = get_mitre_techniques("Phishing")
    assert "T1566.001" in techniques, "Phishing should include T1566.001"
    assert "T1566.002" in techniques, "Phishing should include T1566.002"
    
    # Test non-existing category
    techniques = get_mitre_techniques("UnknownCategory")
    assert techniques == [], "Should return empty list for unknown category"


def test_map_category_to_mitre():
    """Test map_category_to_mitre function"""
    techniques = map_category_to_mitre("Malware")
    assert isinstance(techniques, list), "Should return list"
    assert len(techniques) > 0, "Malware should have MITRE techniques"
    assert "T1059.005" in techniques, "Malware should include T1059.005"


def test_all_threat_actors_have_required_fields():
    """Test that all threat actor profiles have required fields"""
    required_fields = ["aliases", "targets", "techniques", "description"]
    
    for actor_name, profile in THREAT_ACTOR_PROFILES.items():
        for field in required_fields:
            assert field in profile, f"Actor '{actor_name}' should have '{field}' field"
