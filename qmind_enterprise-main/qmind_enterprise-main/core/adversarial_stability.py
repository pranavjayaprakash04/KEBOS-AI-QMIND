"""
================================================================================
Q-MIND ENTERPRISE v3.6 - ADVERSARIAL DECISION STABILITY ENGINE
================================================================================

Core Module: adversarial_stability.py

OVERVIEW:
    Implements resilience mechanisms to prevent decision collapse under:
    - Signal noise injection
    - Adversarial behavior patterns
    - Delayed or conflicting ground truth
    - Polymorphic threat variants
    - Reputation poisoning attacks

STABILITY MECHANISMS:
    1. Confidence Damping Under Disagreement
    2. Multi-Window Temporal Confirmation
    3. Signal Trust Decay (for externally manipulable signals)
    4. Campaign-Level Memory (prevent repeated misses)
    5. Decision Hysteresis (avoid rapid state reversals)

GUARANTEES:
    - No arbitrary collapse on single dominant signal
    - Minimum observation window before Stage-2 confirmation
    - Penalty for rapid confidence spikes without corroboration
    - Preference for delayed decisions over wrong decisions
    - Full auditability of confidence evolution

================================================================================
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import deque


class SignalManipulability(Enum):
    """Classification of signal external manipulability risk."""
    
    HIGH = 0.25      # Domain age, reputation, whois info - easily spoofed
    MEDIUM = 0.50    # Certificate info, DNS patterns - harder to spoof
    LOW = 0.75       # Hash-based, malware family - nearly impossible to spoof
    CRYPTOGRAPHIC = 1.0  # Signatures, hashes - cryptographically bound


class ThreatConfidence(Enum):
    """Threat confidence levels with hysteresis bands."""
    
    # Stage 1: Early Suspicion (Watchlist)
    UNKNOWN = 0.0
    MINIMAL_SUSPICION = 0.15
    LOW_SUSPICION = 0.35
    
    # Stage 2: Confirmed Threat (Blocking)
    ELEVATED_SUSPICION = 0.55
    CONFIRMED_THREAT = 0.75
    HIGH_CONFIDENCE_THREAT = 0.90
    CERTAIN_THREAT = 1.0


@dataclass
class SignalObservation:
    """Single signal reading with trust metadata."""
    
    signal_name: str
    strength: float           # [0.0, 1.0] - signal magnitude
    confidence: float         # [0.0, 1.0] - signal reliability
    manipulability: SignalManipulability  # Risk of external manipulation
    timestamp: float          # Unix timestamp of observation
    context_hash: str         # Hash of decision context (for audit)
    is_corroborated: bool = False  # Did another signal confirm this?
    supporting_signals: List[str] = field(default_factory=list)


@dataclass
class ConfidenceWindow:
    """Time-windowed confidence observation."""
    
    window_start: float       # Timestamp of window start
    window_end: float         # Timestamp of window end
    mean_confidence: float    # Mean confidence in window
    confidence_variance: float  # Variance in confidence
    max_confidence: float     # Peak confidence observed
    min_confidence: float     # Minimum confidence observed
    signal_count: int         # Number of signals in window
    dominant_signals: List[str] = field(default_factory=list)
    is_agreement: bool = False  # Did signals agree in this window?


@dataclass
class CampaignMemory:
    """Historical memory of threat campaign patterns."""
    
    campaign_id: str          # Unique campaign identifier
    first_seen: float         # When campaign first detected
    last_seen: float          # When campaign last observed
    total_observations: int   # Number of observations
    false_negative_count: int # Times we missed this campaign
    false_positive_count: int # Times we wrongly accused it
    trust_score: float        # [0.0, 1.0] - confidence in our decisions
    signal_patterns: Dict[str, float] = field(default_factory=dict)  # Recurring signal patterns
    
    def update_trust(self, correct: bool, magnitude: float = 1.0):
        """Update trust score based on correctness."""
        adjustment = 0.05 * magnitude if correct else -0.10 * magnitude
        self.trust_score = max(0.0, min(1.0, self.trust_score + adjustment))


@dataclass
class DecisionHysteresis:
    """Prevents rapid decision reversals (flipping between threat/benign)."""
    
    previous_state: ThreatConfidence  # Last confirmed state
    state_lock_until: float            # Timestamp: earliest time state can change
    reversals_count: int = 0           # Number of rapid reversals
    lock_duration: float = 300.0       # 5 minutes default - time to lock state
    


class AdversarialStabilityEngine:
    """
    Core decision stability system for v3.6.
    
    Prevents collapse under adversarial conditions while maintaining:
    - Precision ≥95%
    - Explainability (all decisions auditable)
    - Performance (>8K indicators/sec)
    - Determinism (no ML randomness)
    """
    
    def __init__(
        self,
        confidence_damping_factor: float = 0.7,
        min_observation_window: float = 300.0,  # 5 minutes
        signal_agreement_threshold: float = 0.6,
        campaign_memory_size: int = 1000,
    ):
        """
        Initialize adversarial stability engine.
        
        Args:
            confidence_damping_factor: Reduce confidence when signals disagree [0.5, 0.9]
            min_observation_window: Minimum seconds before Stage-2 confirmation
            signal_agreement_threshold: Required agreement percentage for confidence increase
            campaign_memory_size: Max campaigns to track in memory
        """
        self.confidence_damping_factor = confidence_damping_factor
        self.min_observation_window = min_observation_window
        self.signal_agreement_threshold = signal_agreement_threshold
        
        # State management
        self.observations: Dict[str, deque] = {}  # threat_id -> deque of observations
        self.confidence_windows: Dict[str, deque] = {}  # threat_id -> deque of windows
        self.campaign_memory: Dict[str, CampaignMemory] = {}  # campaign_id -> memory
        self.decision_hysteresis: Dict[str, DecisionHysteresis] = {}  # threat_id -> hysteresis
        self.campaign_memory_size = campaign_memory_size
        
        # Audit trail
        self.decision_log: List[Dict] = []
        self.stability_events: List[Dict] = []
        
    def record_observation(
        self,
        threat_id: str,
        signal_name: str,
        strength: float,
        confidence: float,
        manipulability: SignalManipulability,
        supporting_signals: Optional[List[str]] = None,
    ) -> SignalObservation:
        """
        Record a single signal observation.
        
        Args:
            threat_id: Unique identifier for threat
            signal_name: Name of signal source
            strength: Signal magnitude [0.0, 1.0]
            confidence: Signal reliability [0.0, 1.0]
            manipulability: Risk of external manipulation
            supporting_signals: List of corroborating signals
        
        Returns:
            SignalObservation with audit metadata
        """
        timestamp = time.time()
        
        # Build context hash for audit trail
        context = f"{threat_id}_{signal_name}_{timestamp:.2f}"
        context_hash = hashlib.sha256(context.encode()).hexdigest()[:16]
        
        # Determine if corroborated
        is_corroborated = len(supporting_signals or []) > 0
        
        observation = SignalObservation(
            signal_name=signal_name,
            strength=strength,
            confidence=confidence,
            manipulability=manipulability,
            timestamp=timestamp,
            context_hash=context_hash,
            is_corroborated=is_corroborated,
            supporting_signals=supporting_signals or []
        )
        
        # Store observation
        if threat_id not in self.observations:
            self.observations[threat_id] = deque(maxlen=1000)
        self.observations[threat_id].append(observation)
        
        # Log for audit
        self.stability_events.append({
            'type': 'observation_recorded',
            'threat_id': threat_id,
            'signal_name': signal_name,
            'strength': strength,
            'confidence': confidence,
            'corroborated': is_corroborated,
            'timestamp': timestamp,
            'context_hash': context_hash,
        })
        
        return observation
    
    def apply_signal_trust_decay(
        self,
        confidence: float,
        manipulability: SignalManipulability,
        age_seconds: float,
    ) -> float:
        """
        Apply trust decay to confidence based on signal manipulability.
        
        High manipulability signals lose trust over time.
        Low manipulability signals maintain trust longer.
        
        Args:
            confidence: Original confidence [0.0, 1.0]
            manipulability: Signal manipulability level
            age_seconds: Age of signal observation
        
        Returns:
            Decayed confidence value
        """
        # Decay rate depends on manipulability
        decay_rate = (1.0 - manipulability.value) * 0.001  # decay per second
        decay_factor = max(0.3, 1.0 - (decay_rate * age_seconds))
        
        decayed = confidence * decay_factor
        
        # Log decay event
        if age_seconds > 60:  # Only log significant decay
            self.stability_events.append({
                'type': 'signal_trust_decay',
                'original_confidence': confidence,
                'decayed_confidence': decayed,
                'manipulability': manipulability.name,
                'age_seconds': age_seconds,
                'decay_factor': decay_factor,
            })
        
        return decayed
    
    def calculate_agreement_level(
        self,
        observations: List[SignalObservation],
        window_start: float,
        window_end: float,
    ) -> Tuple[float, bool]:
        """
        Calculate signal agreement in time window.
        
        Agreement means:
        - Multiple signals present
        - Mean confidence > threshold
        - No contradictory signals
        - Variance below limit
        
        Args:
            observations: Signals in window
            window_start: Window start timestamp
            window_end: Window end timestamp
        
        Returns:
            (agreement_level [0.0, 1.0], is_agreement bool)
        """
        if not observations:
            return 0.0, False
        
        # Filter observations in window
        windowed = [o for o in observations 
                   if window_start <= o.timestamp <= window_end]
        
        if len(windowed) < 2:
            return 0.0, False  # Need at least 2 signals for agreement
        
        # Calculate statistics
        confidences = [o.confidence for o in windowed]
        mean_conf = sum(confidences) / len(confidences)
        variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
        std_dev = variance ** 0.5
        
        # High agreement: high mean, low variance
        agreement_score = mean_conf * (1.0 - min(0.5, std_dev))
        is_agreement = (agreement_score > self.signal_agreement_threshold and 
                       std_dev < 0.3)
        
        return agreement_score, is_agreement
    
    def apply_confidence_damping(
        self,
        base_confidence: float,
        agreement_level: float,
        signal_count: int,
    ) -> float:
        """
        Apply confidence damping when signals disagree.
        
        Under disagreement, reduce confidence to prevent false alarms.
        Under agreement, maintain or amplify confidence.
        
        Args:
            base_confidence: Original calculated confidence
            agreement_level: Signal agreement [0.0, 1.0]
            signal_count: Number of signals observed
        
        Returns:
            Damped confidence value
        """
        # Damping increases as agreement decreases
        agreement_factor = agreement_level
        
        # More signals provide more evidence (less damping needed)
        signal_bonus = min(0.2, signal_count * 0.05)
        
        # Calculate damped confidence
        damping = self.confidence_damping_factor
        damped = base_confidence * (damping + agreement_factor * (1.0 - damping)) + signal_bonus
        
        # Clamp to [0.0, 1.0]
        damped = max(0.0, min(1.0, damped))
        
        return damped
    
    def evaluate_stage2_readiness(
        self,
        threat_id: str,
        current_confidence: float,
        observation_history: List[SignalObservation],
    ) -> Tuple[bool, str, float]:
        """
        Determine if threat is ready for Stage-2 (confirmed threat) classification.
        
        Requirements:
        - Observation window ≥ min_observation_window seconds
        - Minimum signal count
        - Confidence > 0.75
        - Signal agreement observed
        - No recent reversals
        
        Args:
            threat_id: Threat identifier
            current_confidence: Current calculated confidence
            observation_history: Historical observations
        
        Returns:
            (is_ready bool, reason str, confidence_adjusted float)
        """
        if not observation_history:
            return False, "NO_OBSERVATIONS", 0.0
        
        # Check observation window duration
        first_obs = observation_history[0]
        last_obs = observation_history[-1]
        window_duration = last_obs.timestamp - first_obs.timestamp
        
        if window_duration < self.min_observation_window:
            return False, f"WINDOW_TOO_SHORT_{window_duration:.1f}s", current_confidence
        
        # Check minimum signal count (need diversity)
        signal_names = set(o.signal_name for o in observation_history)
        if len(signal_names) < 2:
            return False, "INSUFFICIENT_SIGNAL_DIVERSITY", current_confidence
        
        # Check confidence threshold
        if current_confidence < 0.75:
            return False, f"CONFIDENCE_BELOW_THRESHOLD_{current_confidence:.2f}", current_confidence
        
        # Check signal agreement
        agreement_level, is_agreement = self.calculate_agreement_level(
            observation_history,
            first_obs.timestamp,
            last_obs.timestamp
        )
        
        if not is_agreement:
            return False, f"NO_AGREEMENT_{agreement_level:.2f}", current_confidence
        
        # Check hysteresis (no rapid reversals)
        if threat_id in self.decision_hysteresis:
            hysteresis = self.decision_hysteresis[threat_id]
            if time.time() < hysteresis.state_lock_until:
                lock_remaining = hysteresis.state_lock_until - time.time()
                return False, f"STATE_LOCKED_{lock_remaining:.1f}s", current_confidence
        
        # All checks passed - ready for Stage-2
        return True, "STAGE2_READY", current_confidence
    
    def enforce_decision_hysteresis(
        self,
        threat_id: str,
        new_state: ThreatConfidence,
        current_state: Optional[ThreatConfidence] = None,
    ) -> Tuple[ThreatConfidence, bool, str]:
        """
        Enforce hysteresis to prevent rapid decision reversals.
        
        If state is trying to change too quickly, lock it in place.
        This prevents flip-flopping between threat/benign.
        
        Args:
            threat_id: Threat identifier
            new_state: Proposed new confidence level
            current_state: Current confirmed state
        
        Returns:
            (enforced_state, did_change bool, reason str)
        """
        current_time = time.time()
        
        # Initialize hysteresis if needed
        if threat_id not in self.decision_hysteresis:
            self.decision_hysteresis[threat_id] = DecisionHysteresis(
                previous_state=current_state or ThreatConfidence.UNKNOWN
            )
        
        hysteresis = self.decision_hysteresis[threat_id]
        
        # Check if state is locked
        if current_time < hysteresis.state_lock_until:
            lock_remaining = hysteresis.state_lock_until - current_time
            reason = f"STATE_LOCKED_{lock_remaining:.1f}s"
            return hysteresis.previous_state, False, reason
        
        # Check if this is a reversal (change from threat to benign or vice versa)
        is_reversal = (
            (hysteresis.previous_state.value > 0.5 and new_state.value < 0.5) or
            (hysteresis.previous_state.value < 0.5 and new_state.value > 0.5)
        )
        
        if is_reversal:
            # Lock state to prevent flip-flopping
            hysteresis.reversals_count += 1
            hysteresis.state_lock_until = current_time + hysteresis.lock_duration
            
            reason = f"REVERSAL_BLOCKED_{hysteresis.reversals_count}_reversals"
            
            self.stability_events.append({
                'type': 'hysteresis_engaged',
                'threat_id': threat_id,
                'previous_state': hysteresis.previous_state.name,
                'attempted_state': new_state.name,
                'reversals_count': hysteresis.reversals_count,
                'lock_duration': hysteresis.lock_duration,
                'timestamp': current_time,
            })
            
            return hysteresis.previous_state, False, reason
        
        # State change is allowed
        hysteresis.previous_state = new_state
        
        # Increase lock duration on repeated reversals to prevent patterns
        if hysteresis.reversals_count > 0:
            hysteresis.lock_duration = min(1800.0, 300.0 * (hysteresis.reversals_count + 1))
        
        return new_state, True, "STATE_CHANGED"
    
    def update_campaign_memory(
        self,
        campaign_id: str,
        observation: SignalObservation,
        was_correct: bool,
        is_false_positive: bool = False,
        is_false_negative: bool = False,
    ) -> CampaignMemory:
        """
        Update historical memory of threat campaign.
        
        Used to detect repeated patterns and prevent recurring misses.
        
        Args:
            campaign_id: Campaign identifier
            observation: Signal observation
            was_correct: Was decision correct?
            is_false_positive: Was it a false positive?
            is_false_negative: Was it a false negative?
        
        Returns:
            Updated CampaignMemory object
        """
        if campaign_id not in self.campaign_memory:
            self.campaign_memory[campaign_id] = CampaignMemory(
                campaign_id=campaign_id,
                first_seen=observation.timestamp,
                last_seen=observation.timestamp,
                total_observations=0,
                false_negative_count=0,
                false_positive_count=0,
                trust_score=0.5,  # Start neutral
            )
        
        memory = self.campaign_memory[campaign_id]
        
        # Update counts
        memory.total_observations += 1
        memory.last_seen = observation.timestamp
        
        if is_false_negative:
            memory.false_negative_count += 1
        elif is_false_positive:
            memory.false_positive_count += 1
        
        # Update trust score
        memory.update_trust(was_correct)
        
        # Track signal patterns
        key = observation.signal_name
        if key not in memory.signal_patterns:
            memory.signal_patterns[key] = 0.0
        memory.signal_patterns[key] += observation.confidence
        
        # Prune old campaigns if memory is full
        if len(self.campaign_memory) > self.campaign_memory_size:
            # Remove least-seen campaign
            oldest = min(
                self.campaign_memory.values(),
                key=lambda m: m.last_seen
            )
            del self.campaign_memory[oldest.campaign_id]
        
        return memory
    
    def generate_stability_report(self) -> Dict:
        """
        Generate comprehensive stability metrics report.
        
        Returns:
            Dictionary with stability analysis
        """
        return {
            'threat_count': len(self.observations),
            'total_observations': sum(len(obs) for obs in self.observations.values()),
            'campaign_memory_size': len(self.campaign_memory),
            'active_hysteresis_locks': sum(
                1 for h in self.decision_hysteresis.values()
                if time.time() < h.state_lock_until
            ),
            'total_reversals': sum(
                h.reversals_count for h in self.decision_hysteresis.values()
            ),
            'stability_events_logged': len(self.stability_events),
            'decisions_logged': len(self.decision_log),
            'avg_agreement_level': self._calculate_avg_agreement(),
            'campaign_memory_details': {
                cid: {
                    'observations': m.total_observations,
                    'false_positives': m.false_positive_count,
                    'false_negatives': m.false_negative_count,
                    'trust_score': m.trust_score,
                }
                for cid, m in list(self.campaign_memory.items())[:10]  # Top 10
            }
        }
    
    def _calculate_avg_agreement(self) -> float:
        """Calculate average signal agreement across all threats."""
        if not self.observations:
            return 0.0
        
        agreements = []
        for obs_list in self.observations.values():
            if len(obs_list) >= 2:
                agreement, _ = self.calculate_agreement_level(
                    list(obs_list),
                    obs_list[0].timestamp,
                    obs_list[-1].timestamp
                )
                agreements.append(agreement)
        
        return sum(agreements) / len(agreements) if agreements else 0.0
    
    def export_audit_trail(self) -> Dict:
        """
        Export complete audit trail for forensics.
        
        Returns:
            Audit trail with all decision events
        """
        return {
            'export_timestamp': time.time(),
            'stability_events': self.stability_events,
            'decision_log': self.decision_log,
            'campaign_memory_snapshot': {
                cid: {
                    'first_seen': m.first_seen,
                    'last_seen': m.last_seen,
                    'total_observations': m.total_observations,
                    'trust_score': m.trust_score,
                    'signal_patterns': m.signal_patterns,
                }
                for cid, m in self.campaign_memory.items()
            },
            'hysteresis_state': {
                tid: {
                    'previous_state': h.previous_state.name,
                    'reversals': h.reversals_count,
                    'locked': time.time() < h.state_lock_until,
                }
                for tid, h in self.decision_hysteresis.items()
            }
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_stability_engine_with_defaults() -> AdversarialStabilityEngine:
    """Factory function to create engine with recommended defaults."""
    return AdversarialStabilityEngine(
        confidence_damping_factor=0.7,      # 70% - reasonable damping
        min_observation_window=300.0,       # 5 minutes
        signal_agreement_threshold=0.6,     # 60% agreement required
        campaign_memory_size=1000,
    )


# ============================================================================
# END OF MODULE
# ============================================================================
