"""
Q-MIND Enterprise: Multi-Category Threat State

Extends Q-MIND v3.0 to handle 10 cybersecurity threat categories with
probabilistic superposition, delayed ground truth alignment, and
individual threat lifecycle tracking.

Threat Categories:
1. Phishing & Malicious URLs
2. Malware (hashes, families)
3. Command-and-Control (C2)
4. Malicious IPs & Botnets
5. Credential Leaks & Account Abuse
6. Supply Chain / Dependency Attacks
7. Insider Threat Signals
8. DDoS & Traffic Anomalies
9. Vulnerability Exploitation (CVEs)
10. Benign / Clean Baseline (control)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# Threat Categories
class ThreatCategory(str, Enum):
    """10 threat categories supported by Q-MIND Enterprise."""
    PHISHING = "phishing"
    MALWARE = "malware"
    C2_INFRASTRUCTURE = "c2_infrastructure"
    BOTNET_IP = "botnet_ip"
    CREDENTIAL_LEAK = "credential_leak"
    SUPPLY_CHAIN = "supply_chain"
    INSIDER_THREAT = "insider_threat"
    DDOS = "ddos"
    VULNERABILITY = "vulnerability"
    BENIGN = "benign"


class ThreatAmplitude(Enum):
    """Threat state hypotheses (quantum-inspired)."""
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    BENIGN = "benign"


@dataclass
class IndicatorSignature:
    """
    Unique identifier for a threat indicator.
    
    Examples:
    - Phishing: sha256(url)
    - Malware: hash value
    - IP: ip_address
    - CVE: cve_id
    - Domain: domain_name
    """
    indicator_type: str  # "url", "hash", "ip", "domain", "email", "cve"
    indicator_value: str  # actual value
    category: ThreatCategory
    
    def __hash__(self):
        return hash((self.indicator_type, self.indicator_value, self.category.value))
    
    def __eq__(self, other):
        if not isinstance(other, IndicatorSignature):
            return False
        return (
            self.indicator_type == other.indicator_type and
            self.indicator_value == other.indicator_value and
            self.category == other.category
        )


@dataclass
class SignalContribution:
    """Record of how a signal influenced the threat state."""
    signal_type: str  # "lexical", "reputation", "temporal", "behavioral"
    signal_id: str
    strength: float  # [0, 1]
    confidence: float  # [0, 1]
    influence_vector: Dict[str, float]  # effect on each amplitude
    timestamp: float
    decayed_strength: float = 0.0  # strength after decay


@dataclass
class GroundTruthRecord:
    """
    Delayed ground truth alignment.
    
    Ground truth arrives at:
    - T+24h: Initial confirmation
    - T+48h: Full context available
    """
    indicator: IndicatorSignature
    actual_threat: bool
    actual_category: Optional[ThreatCategory] = None
    timing: str = "timely"  # "early", "timely", "late"
    analyst_confidence: float = 0.95
    context: str = ""
    recorded_at: float = field(default_factory=datetime.now().timestamp)


class ThreatState:
    """
    Multi-category threat state with probabilistic amplitudes.
    
    Key design:
    - Amplitudes represent uncertainty over 3 hypotheses
    - Signals update amplitudes via influence vectors
    - Ground truth arrives asynchronously
    - Feedback adapts signal weights
    - No labels in decision logic
    """
    
    def __init__(self, indicator: IndicatorSignature):
        """
        Initialize threat state for an indicator.
        
        Args:
            indicator: IndicatorSignature identifying the threat
        """
        self.indicator = indicator
        self.state_id = f"{indicator.category.value}_{indicator.indicator_value}_{datetime.now().timestamp()}"
        
        # Probabilistic amplitudes (sum = 1.0)
        self.amplitudes: Dict[str, float] = {
            "malicious": 0.1,
            "suspicious": 0.1,
            "benign": 0.8,  # Assume innocent until proven otherwise
        }
        
        # Overall confidence [0, 1]
        self.confidence = 0.1
        
        # Signal history with decay tracking
        self.signal_contributions: List[SignalContribution] = []
        
        # Ground truth (arrives later)
        self.ground_truth: Optional[GroundTruthRecord] = None
        self.ground_truth_received_at: Optional[float] = None
        
        # Lifecycle tracking
        self.created_at = datetime.now().timestamp()
        self.last_updated = self.created_at
        self.measurement_taken = False
        self.measurement_timestamp: Optional[float] = None
        self.measurement_result: Optional[str] = None
        
        # Campaign/correlation linkage
        self.campaign_ids: Set[str] = set()
        self.related_indicators: Set[str] = set()
        
        # Audit trail
        self.audit_log: List[Dict] = []
        
        self._log_audit("state_created", {
            "category": indicator.category.value,
            "indicator": indicator.indicator_value[:50],
        })
    
    def add_signal(self, contribution: SignalContribution) -> None:
        """
        Add signal contribution to threat state.
        
        Args:
            contribution: SignalContribution with decay-adjusted strength
        """
        # Apply decay to old signals
        current_time = datetime.now().timestamp()
        time_hours = (current_time - self.created_at) / 3600
        
        # Exponential decay: value(t) = initial × e^(-λt)
        import math
        decay_factor = math.exp(-0.1 * time_hours)  # λ=0.1 (half-life ~7h)
        contribution.decayed_strength = contribution.strength * decay_factor
        
        self.signal_contributions.append(contribution)
        
        # Update amplitudes using influence vector
        if contribution.decayed_strength > 0.05:  # Skip very weak signals
            for amplitude_key, influence in contribution.influence_vector.items():
                if amplitude_key in self.amplitudes:
                    # Add weighted influence
                    influence_magnitude = (
                        contribution.decayed_strength *
                        contribution.confidence *
                        influence
                    )
                    self.amplitudes[amplitude_key] += influence_magnitude
            
            # Renormalize amplitudes to sum = 1.0
            total = sum(self.amplitudes.values())
            if total > 0:
                self.amplitudes = {
                    k: v / total for k, v in self.amplitudes.items()
                }
            
            # Update confidence (moving average)
            self.confidence = (
                0.7 * self.confidence +
                0.3 * contribution.confidence
            )
            
            self.last_updated = current_time
            
            self._log_audit("signal_added", {
                "signal_type": contribution.signal_type,
                "strength": f"{contribution.strength:.2f}",
                "new_malicious": f"{self.amplitudes['malicious']:.2f}",
            })
    
    def measure(self) -> Dict:
        """
        Collapse threat state to decision via measurement.
        
        Returns decision based on amplitude thresholds.
        Implements threat level classification.
        """
        if self.measurement_taken:
            return {
                "state_id": self.state_id,
                "already_measured": True,
                "measurement_timestamp": self.measurement_timestamp,
                "threat_level": self.measurement_result,
            }
        
        malicious_amp = self.amplitudes.get("malicious", 0.1)
        suspicious_amp = self.amplitudes.get("suspicious", 0.1)
        
        # Threshold-based measurement
        if malicious_amp > 0.75:
            threat_level = "critical"
            lead_time_hours = 2
        elif malicious_amp > 0.55:
            threat_level = "high"
            lead_time_hours = 6
        elif malicious_amp > 0.35:
            threat_level = "medium"
            lead_time_hours = 12
        elif suspicious_amp > 0.6:
            threat_level = "medium"
            lead_time_hours = 24
        elif suspicious_amp > 0.4:
            threat_level = "low"
            lead_time_hours = 48
        else:
            threat_level = "minimal"
            lead_time_hours = 0
        
        self.measurement_taken = True
        self.measurement_timestamp = datetime.now().timestamp()
        self.measurement_result = threat_level
        
        self._log_audit("measurement_taken", {
            "threat_level": threat_level,
            "confidence": f"{self.confidence:.2f}",
            "amplitudes": {k: f"{v:.2f}" for k, v in self.amplitudes.items()},
        })
        
        return {
            "state_id": self.state_id,
            "indicator": self.indicator.indicator_value[:50],
            "category": self.indicator.category.value,
            "threat_level": threat_level,
            "confidence": round(self.confidence, 4),
            "lead_time_hours": lead_time_hours,
            "amplitudes": {k: round(v, 4) for k, v in self.amplitudes.items()},
            "signals_processed": len(self.signal_contributions),
            "timestamp": self.measurement_timestamp,
        }
    
    def record_ground_truth(self, truth: GroundTruthRecord) -> None:
        """
        Record delayed ground truth outcome.
        
        Enables feedback loop and accuracy calculation.
        """
        self.ground_truth = truth
        self.ground_truth_received_at = datetime.now().timestamp()
        
        # Determine if decision was correct
        if self.measurement_result:
            predicted_threat = self.measurement_result != "minimal"
            is_correct = predicted_threat == truth.actual_threat
            
            self._log_audit("ground_truth_recorded", {
                "actual_threat": truth.actual_threat,
                "predicted_threat": predicted_threat,
                "decision_correct": is_correct,
                "timing": truth.timing,
            })
    
    def is_high_confidence(self) -> bool:
        """Check if measurement should be trusted without anchor model."""
        return self.confidence >= 0.6
    
    def get_export(self) -> Dict:
        """Export complete threat state for API/storage."""
        return {
            "state_id": self.state_id,
            "indicator": {
                "type": self.indicator.indicator_type,
                "value": self.indicator.indicator_value,
                "category": self.indicator.category.value,
            },
            "amplitudes": self.amplitudes.copy(),
            "confidence": self.confidence,
            "measurement": {
                "taken": self.measurement_taken,
                "result": self.measurement_result,
                "timestamp": self.measurement_timestamp,
            },
            "ground_truth": {
                "received": self.ground_truth_received_at is not None,
                "actual_threat": self.ground_truth.actual_threat if self.ground_truth else None,
            } if self.ground_truth else None,
            "signal_count": len(self.signal_contributions),
            "campaign_ids": list(self.campaign_ids),
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "audit_trail": self.audit_log[-10:],  # Last 10 events
        }
    
    def _log_audit(self, event: str, details: Dict) -> None:
        """Log event to audit trail."""
        self.audit_log.append({
            "event": event,
            "timestamp": datetime.now().timestamp(),
            "details": details,
        })


class ThreatStateManager:
    """
    Manages lifecycle of threat states across all categories.
    
    Enables:
    - Indicator deduplication
    - State evolution over time
    - Ground truth alignment
    - Feedback collection
    """
    
    def __init__(self):
        """Initialize threat state manager."""
        self.states: Dict[str, ThreatState] = {}
        self.indicator_to_state: Dict[IndicatorSignature, str] = {}
    
    def get_or_create_state(self, indicator: IndicatorSignature) -> ThreatState:
        """
        Get existing threat state or create new one.
        
        Args:
            indicator: IndicatorSignature
            
        Returns:
            ThreatState (existing or new)
        """
        if indicator in self.indicator_to_state:
            state_id = self.indicator_to_state[indicator]
            return self.states[state_id]
        
        # Create new state
        state = ThreatState(indicator)
        self.states[state.state_id] = state
        self.indicator_to_state[indicator] = state.state_id
        
        logger.info(f"Created state {state.state_id} for {indicator.indicator_value[:30]}")
        return state
    
    def get_states_by_category(self, category: ThreatCategory) -> List[ThreatState]:
        """Get all threat states in a category."""
        return [
            state for state in self.states.values()
            if state.indicator.category == category
        ]
    
    def get_all_states(self) -> List[ThreatState]:
        """Get all threat states."""
        return list(self.states.values())
    
    def get_state(self, state_id: str) -> Optional[ThreatState]:
        """Get threat state by ID."""
        return self.states.get(state_id)


# Module initialization
logger.info("Q-MIND Enterprise: Multi-Category Threat State initialized")
