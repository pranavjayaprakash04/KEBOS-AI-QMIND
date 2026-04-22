"""
Q-MIND Enterprise: Extended Signal Types for 10 Threat Categories

Each threat category gets specialized signals tuned to its characteristics.
All signals inherit from base Signal class with decay and influence vectors.
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Signal types across all threat categories."""
    # URL/Domain signals
    LEXICAL = "lexical"
    REPUTATION = "reputation"
    
    # Temporal signals
    TEMPORAL = "temporal"
    BURST_DETECTION = "burst"
    
    # Behavioral signals
    BEHAVIORAL = "behavioral"
    CAMPAIGN_MATCH = "campaign"
    
    # Malware-specific
    HASH_REPUTATION = "hash_reputation"
    FAMILY_AFFILIATION = "family_affiliation"
    
    # Network-specific
    ASN_REPUTATION = "asn_reputation"
    GEO_ANOMALY = "geo_anomaly"
    
    # Credential-specific
    BREACH_DATABASE = "breach_database"
    PASSWORD_AGE = "password_age"
    
    # Vulnerability-specific
    CVE_SEVERITY = "cve_severity"
    EXPLOIT_AVAILABILITY = "exploit_availability"
    
    # Insider threat-specific
    BEHAVIOR_ANOMALY = "behavior_anomaly"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    
    # Supply chain-specific
    DEPENDENCY_SCAN = "dependency_scan"
    CHAIN_BREACH = "chain_breach"


@dataclass
class Signal:
    """Base signal class for all threat categories."""
    signal_type: SignalType
    indicator_value: str
    
    # Signal properties
    strength: float  # [0, 1] - raw strength before weighting
    confidence: float  # [0, 1] - how confident is this signal?
    decay_rate: float  # [0.01, 0.5] - exponential decay rate
    
    # Effect on threat amplitudes
    influence_vector: Dict[str, float] = None  # {malicious, suspicious, benign}
    
    # Metadata
    source: str = ""  # dataset source
    timestamp: float = 0.0
    
    def __post_init__(self):
        """Validate signal properties."""
        assert 0 <= self.strength <= 1, "Strength must be [0, 1]"
        assert 0 <= self.confidence <= 1, "Confidence must be [0, 1]"
        assert 0.01 <= self.decay_rate <= 0.5, "Decay rate must be [0.01, 0.5]"
        
        if self.influence_vector is None:
            self.influence_vector = {"malicious": 0.5, "suspicious": 0.3, "benign": -0.3}


# ============================================================================
# PHISHING & MALICIOUS URLS (Category 1)
# ============================================================================

class PhishingLexicalSignal(Signal):
    """
    Detect phishing via URL structure analysis.
    
    Checks: entropy, special chars, subdomain count, etc.
    """
    def __init__(self, url: str, entropy: float, special_char_count: int):
        super().__init__(
            signal_type=SignalType.LEXICAL,
            indicator_value=url,
            strength=min(entropy / 5.0, 1.0),  # Normalize entropy
            confidence=0.75,
            decay_rate=0.15,  # Half-life ~4.6 hours
            source="lexical_analysis",
        )
        self.influence_vector = {
            "malicious": 0.7,  # Strong for phishing
            "suspicious": 0.2,
            "benign": -0.3,
        }


class PhishingReputationSignal(Signal):
    """Domain reputation signal for phishing detection."""
    def __init__(self, domain: str, age_days: int, blacklist_count: int):
        # Newer domains more suspicious
        age_score = min(age_days / 365.0, 1.0)
        blacklist_score = min(blacklist_count / 5.0, 1.0)
        strength = (1.0 - age_score) * 0.6 + blacklist_score * 0.4
        
        super().__init__(
            signal_type=SignalType.REPUTATION,
            indicator_value=domain,
            strength=strength,
            confidence=0.85,
            decay_rate=0.05,  # Long half-life ~13.8 hours
            source="reputation_database",
        )
        self.influence_vector = {
            "malicious": 0.6,
            "suspicious": 0.3,
            "benign": -0.2,
        }


# ============================================================================
# MALWARE (Category 2)
# ============================================================================

class MalwareHashReputationSignal(Signal):
    """File hash reputation (MD5, SHA256)."""
    def __init__(self, file_hash: str, av_hits: int, total_scanners: int = 70):
        # Detection ratio across antivirus engines
        strength = min(av_hits / total_scanners, 1.0)
        
        super().__init__(
            signal_type=SignalType.HASH_REPUTATION,
            indicator_value=file_hash,
            strength=strength,
            confidence=min(0.5 + av_hits / total_scanners, 0.99),  # More AV hits = higher confidence
            decay_rate=0.02,  # Very slow decay (persistent threat)
            source="virustotal",
        )
        self.influence_vector = {
            "malicious": 0.9,  # Hash reputation is strong indicator
            "suspicious": 0.05,
            "benign": -0.4,
        }


class MalwareFamilySignal(Signal):
    """Malware family affiliation signal."""
    def __init__(self, hash_value: str, family_name: str, confidence: float):
        super().__init__(
            signal_type=SignalType.FAMILY_AFFILIATION,
            indicator_value=hash_value,
            strength=0.8,
            confidence=confidence,
            decay_rate=0.01,  # Extremely slow decay
            source="malware_taxonomy",
        )
        self.influence_vector = {
            "malicious": 0.85,
            "suspicious": 0.1,
            "benign": -0.5,
        }


# ============================================================================
# C2 INFRASTRUCTURE (Category 3)
# ============================================================================

class C2TemporalSignal(Signal):
    """C2 activity pattern detection."""
    def __init__(self, ip_or_domain: str, request_rate: float, off_hours_activity: bool):
        # Sustained high request rate and off-hours activity = C2
        strength = min(request_rate / 100.0, 1.0)
        if off_hours_activity:
            strength = min(strength + 0.3, 1.0)
        
        super().__init__(
            signal_type=SignalType.TEMPORAL,
            indicator_value=ip_or_domain,
            strength=strength,
            confidence=0.7,
            decay_rate=0.25,  # Fast decay (patterns change)
            source="network_behavior",
        )
        self.influence_vector = {
            "malicious": 0.75,
            "suspicious": 0.2,
            "benign": -0.3,
        }


# ============================================================================
# MALICIOUS IPS & BOTNETS (Category 4)
# ============================================================================

class ASNReputationSignal(Signal):
    """ASN (Autonomous System Number) reputation."""
    def __init__(self, asn: str, known_bulletproof_hosting: bool, abuse_reports: int):
        strength = 0.9 if known_bulletproof_hosting else min(abuse_reports / 50.0, 1.0)
        
        super().__init__(
            signal_type=SignalType.ASN_REPUTATION,
            indicator_value=asn,
            strength=strength,
            confidence=0.85,
            decay_rate=0.03,
            source="asn_tracking",
        )
        self.influence_vector = {
            "malicious": 0.8,
            "suspicious": 0.15,
            "benign": -0.3,
        }


class GeoAnomalySignal(Signal):
    """Geographic anomaly detection for botnet activity."""
    def __init__(self, ip: str, expected_geo: str, actual_geo: str, distance_km: float):
        # Large geographic deviation = anomaly
        strength = min(distance_km / 10000.0, 1.0)  # Normalize to 1.0 at 10k km
        
        super().__init__(
            signal_type=SignalType.GEO_ANOMALY,
            indicator_value=ip,
            strength=strength,
            confidence=0.6,
            decay_rate=0.2,
            source="geolocation",
        )
        self.influence_vector = {
            "malicious": 0.5,
            "suspicious": 0.4,
            "benign": -0.2,
        }


# ============================================================================
# CREDENTIAL LEAKS & ACCOUNT ABUSE (Category 5)
# ============================================================================

class BreachDatabaseSignal(Signal):
    """Signal from known breach databases."""
    def __init__(self, email: str, breach_name: str, exposure_count: int):
        # Each breach increases confidence
        strength = min(exposure_count / 10.0, 1.0)
        
        super().__init__(
            signal_type=SignalType.BREACH_DATABASE,
            indicator_value=email,
            strength=strength,
            confidence=0.95,  # Breaches are high-confidence
            decay_rate=0.01,  # Breach data is persistent
            source="breach_database",
        )
        self.influence_vector = {
            "malicious": 0.7,  # Compromised credential
            "suspicious": 0.2,
            "benign": -0.3,
        }


# ============================================================================
# SUPPLY CHAIN ATTACKS (Category 6)
# ============================================================================

class DependencyScanSignal(Signal):
    """Supply chain vulnerability signal."""
    def __init__(self, library: str, version: str, vulnerability_count: int):
        strength = min(vulnerability_count / 5.0, 1.0)
        
        super().__init__(
            signal_type=SignalType.DEPENDENCY_SCAN,
            indicator_value=f"{library}@{version}",
            strength=strength,
            confidence=0.8,
            decay_rate=0.1,
            source="dependency_checker",
        )
        self.influence_vector = {
            "malicious": 0.6,
            "suspicious": 0.3,
            "benign": -0.2,
        }


# ============================================================================
# INSIDER THREATS (Category 7)
# ============================================================================

class BehaviorAnomalySignal(Signal):
    """User behavior anomaly detection."""
    def __init__(self, user_id: str, zscore: float, anomaly_type: str):
        # Z-score > 3 is strong anomaly
        strength = min(abs(zscore) / 5.0, 1.0)
        
        super().__init__(
            signal_type=SignalType.BEHAVIOR_ANOMALY,
            indicator_value=user_id,
            strength=strength,
            confidence=min(0.5 + abs(zscore) / 10.0, 0.9),
            decay_rate=0.3,
            source="ueba",
        )
        self.influence_vector = {
            "malicious": 0.4,  # Moderate (could be innocent)
            "suspicious": 0.5,
            "benign": -0.2,
        }


# ============================================================================
# VULNERABILITY EXPLOITATION (Category 9)
# ============================================================================

class CVESeveritySignal(Signal):
    """CVE severity and exploitability signal."""
    def __init__(self, cve_id: str, cvss_score: float, exploits_public: int):
        # CVSS 0-10 scale
        strength = cvss_score / 10.0
        if exploits_public > 0:
            strength = min(strength + 0.2, 1.0)
        
        super().__init__(
            signal_type=SignalType.CVE_SEVERITY,
            indicator_value=cve_id,
            strength=strength,
            confidence=0.9,
            decay_rate=0.15,
            source="nvd",
        )
        self.influence_vector = {
            "malicious": 0.8,
            "suspicious": 0.15,
            "benign": -0.3,
        }


# ============================================================================
# Benign/Clean Baseline (Category 10)
# ============================================================================

class BenignSignal(Signal):
    """Signal indicating clean/benign indicator (false-positive control)."""
    def __init__(self, indicator: str, reason: str, certitude: float):
        super().__init__(
            signal_type=SignalType.LEXICAL,
            indicator_value=indicator,
            strength=certitude,
            confidence=0.9,
            decay_rate=0.05,
            source="whitelist",
        )
        self.influence_vector = {
            "malicious": -0.8,  # Strong negative
            "suspicious": -0.5,
            "benign": 0.9,
        }


# Signal weight management for feedback loop
class SignalWeightManager:
    """
    Dynamic signal weighting based on feedback.
    
    Boosts signals that enable early correct detection.
    Penalizes signals that cause false positives.
    """
    
    def __init__(self):
        self.signal_weights: Dict[SignalType, float] = {
            signal_type: 1.0 for signal_type in SignalType
        }
        self.update_history = []
    
    def boost_weight(self, signal_type: SignalType, factor: float = 1.05):
        """Boost signal weight for correct detection."""
        self.signal_weights[signal_type] *= factor
        self.signal_weights[signal_type] = min(self.signal_weights[signal_type], 2.0)
        self.update_history.append({
            "signal": signal_type.value,
            "operation": "boost",
            "new_weight": self.signal_weights[signal_type],
        })
    
    def penalize_weight(self, signal_type: SignalType, factor: float = 0.9):
        """Reduce signal weight for false positives."""
        self.signal_weights[signal_type] *= factor
        self.signal_weights[signal_type] = max(self.signal_weights[signal_type], 0.1)
        self.update_history.append({
            "signal": signal_type.value,
            "operation": "penalize",
            "new_weight": self.signal_weights[signal_type],
        })
    
    def get_weight(self, signal_type: SignalType) -> float:
        """Get current weight for signal type."""
        return self.signal_weights.get(signal_type, 1.0)


logger.info("Q-MIND Enterprise: Extended Signal Types initialized (10 categories)")
