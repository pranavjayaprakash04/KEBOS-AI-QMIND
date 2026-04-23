"""
Q-MIND Enterprise v3.6.1+: Integrated Threat Intelligence Module

Ports and adapts quantum threat model from quantum_tis/qmind/ 
for integration with v3.6.1 encryption system.

Core components:
- Quantum-inspired threat state representation
- Probability-based threat measurement
- Entanglement tracking for correlated threats
- Observer effect modeling during cryptographic operations

This module enables real-time threat assessment during encryption/decryption.
"""

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
import uuid


# ============================================================================
# QUANTUM AMPLITUDES: Probabilistic threat representation
# ============================================================================

class ObservableProperty(Enum):
    """Observable properties that define threat state dimensions."""
    MALICIOUSNESS = "maliciousness"
    PERSISTENCE = "persistence"
    TRANSMISSIBILITY = "transmissibility"
    UNCERTAINTY = "uncertainty"
    DECOHERENCE = "decoherence"


@dataclass
class QuantumAmplitude:
    """
    Probability amplitude in threat state space.
    Unlike classical probability, amplitudes are complex with magnitude and phase.
    Magnitude² = probability. Phase encodes temporal and correlative information.
    """
    magnitude: float = 0.5          # |ψ|, must be in [0, 1]
    phase: float = 0.0              # Phase angle (temporal information)
    coherence: float = 1.0          # Quantum coherence level [0, 1]
    
    def __post_init__(self):
        """Enforce quantum amplitude invariants."""
        self.magnitude = max(0.0, min(self.magnitude, 1.0))
        self.coherence = max(0.0, min(self.coherence, 1.0))
    
    def to_complex(self) -> complex:
        """Convert amplitude to complex representation."""
        return self.magnitude * self.coherence * np.exp(1j * self.phase)
    
    def probability(self) -> float:
        """Extract probability from amplitude (|ψ|²)."""
        return (self.magnitude ** 2) * (self.coherence ** 2)
    
    def decohere(self, decoherence_rate: float) -> None:
        """Apply environmental decoherence (coherence decay)."""
        self.coherence *= (1.0 - decoherence_rate)
    
    def __repr__(self) -> str:
        prob = self.probability()
        return f"Amplitude(p={prob:.3f}, phase={self.phase:.2f}, coherence={self.coherence:.3f})"


# ============================================================================
# THREAT STATE VECTORS: Individual threat indicators as quantum states
# ============================================================================

@dataclass
class ThreatStateVector:
    """
    Represents a threat indicator as quantum-like probability superposition.
    
    A threat is not simply "malicious" or "benign", but a superposition
    of probabilistic states evolving through time and correlation.
    """
    
    # Identifier
    indicator_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    indicator_value: str = ""
    indicator_type: str = ""
    
    # Quantum state amplitudes (5 dimensions of threat)
    maliciousness: QuantumAmplitude = field(default_factory=QuantumAmplitude)
    persistence: QuantumAmplitude = field(default_factory=QuantumAmplitude)
    transmissibility: QuantumAmplitude = field(default_factory=QuantumAmplitude)
    uncertainty: QuantumAmplitude = field(default_factory=QuantumAmplitude)
    
    # Temporal tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_observed: datetime = field(default_factory=datetime.utcnow)
    observation_count: int = 0
    
    # Entanglement tracking
    entangled_with: Set[str] = field(default_factory=set)
    entanglement_strength: float = 0.0
    
    # Historical evolution
    amplitude_history: Dict[str, List[float]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize amplitude history tracking."""
        self.amplitude_history = {
            "maliciousness": [self.maliciousness.probability()],
            "persistence": [self.persistence.probability()],
            "transmissibility": [self.transmissibility.probability()],
            "uncertainty": [self.uncertainty.probability()],
        }
    
    def net_threat_amplitude(self) -> float:
        """
        Compute net threat as entangled superposition of amplitudes.
        Uses quantum interference (not simple averaging).
        """
        mal_complex = self.maliciousness.to_complex()
        pers_complex = self.persistence.to_complex()
        trans_complex = self.transmissibility.to_complex()
        
        # Quantum interference
        superposition = mal_complex * 0.5 + pers_complex * 0.3 + trans_complex * 0.2
        net_prob = abs(superposition) ** 2
        
        return min(net_prob, 1.0)
    
    def apply_decoherence(self, rate: float) -> None:
        """Apply environmental decoherence to all amplitudes."""
        self.maliciousness.decohere(rate)
        self.persistence.decohere(rate)
        self.transmissibility.decohere(rate)
        self.uncertainty.decohere(rate)
    
    def evolve_state(self, time_step: float, external_signal: Optional[float] = None) -> None:
        """
        Evolve threat state through time (quantum-like evolution).
        
        Args:
            time_step: Time elapsed since last evolution (seconds)
            external_signal: Optional external observation (0-1)
        """
        # Natural phase drift
        phase_drift = time_step * 0.1
        self.maliciousness.phase = (self.maliciousness.phase + phase_drift) % (2 * np.pi)
        self.persistence.phase = (self.persistence.phase + phase_drift) % (2 * np.pi)
        
        # Uncertainty naturally increases
        uncertainty_growth = time_step * 0.05
        self.uncertainty.magnitude = min(1.0, self.uncertainty.magnitude + uncertainty_growth)
        
        # External signal acts as measurement-like observation
        if external_signal is not None:
            collapse_strength = 0.3
            self.maliciousness.magnitude += (external_signal - self.maliciousness.magnitude) * collapse_strength
            self.uncertainty.magnitude *= (1.0 - collapse_strength)
        
        # Apply decoherence
        self.apply_decoherence(time_step * 0.02)
        
        # Update timestamp
        self.last_observed = datetime.utcnow()
        for dim in ["maliciousness", "persistence", "transmissibility", "uncertainty"]:
            amplitude = getattr(self, dim)
            self.amplitude_history[dim].append(amplitude.probability())
    
    def get_amplitude_drift(self, window: int = 5) -> float:
        """
        Measure rate of amplitude change (drift prediction).
        High drift = threat state destabilizing = imminent action.
        """
        if len(self.amplitude_history["maliciousness"]) < window:
            return 0.0
        
        recent = self.amplitude_history["maliciousness"][-window:]
        drift = np.mean(np.diff(recent))
        return drift
    
    def __repr__(self) -> str:
        net = self.net_threat_amplitude()
        drift = self.get_amplitude_drift()
        return (f"ThreatState({self.indicator_value[:20]}, "
                f"threat={net:.3f}, drift={drift:.4f}, "
                f"entangled_with={len(self.entangled_with)} indicators)")


# ============================================================================
# THREAT ENSEMBLE: Collective threat state management
# ============================================================================

@dataclass
class ThreatStateEnsemble:
    """
    Manages collection of threat states as interconnected quantum system.
    States do not evolve in isolation; they influence each other through entanglement.
    """
    
    states: Dict[str, ThreatStateVector] = field(default_factory=dict)
    entanglement_graph: Dict[str, Dict[str, float]] = field(default_factory=dict)
    measurement_history: List[Tuple[str, float, datetime]] = field(default_factory=list)
    
    def add_state(self, state: ThreatStateVector) -> None:
        """Register a new threat state."""
        self.states[state.indicator_id] = state
        self.entanglement_graph[state.indicator_id] = {}
    
    def entangle_states(self, state1_id: str, state2_id: str, strength: float) -> None:
        """Create entanglement between two threat states."""
        if state1_id in self.states and state2_id in self.states:
            self.entanglement_graph[state1_id][state2_id] = strength
            self.entanglement_graph[state2_id][state1_id] = strength
            
            self.states[state1_id].entangled_with.add(state2_id)
            self.states[state2_id].entangled_with.add(state1_id)
    
    def propagate_entanglement(self, source_id: str, intensity: float, decay: float = 0.9) -> None:
        """
        Propagate entanglement effects through the graph.
        When one threat changes, it affects connected states.
        
        Args:
            source_id: ID of state experiencing change
            intensity: Strength of entanglement pulse [0, 1]
            decay: Exponential decay as entanglement spreads
        """
        if source_id not in self.states:
            return
        
        visited = set()
        to_process = [(source_id, intensity)]
        
        while to_process:
            current_id, current_intensity = to_process.pop(0)
            if current_id in visited or current_intensity < 0.01:
                continue
            
            visited.add(current_id)
            current_state = self.states[current_id]
            
            # Propagate to entangled neighbors
            for neighbor_id, coupling_strength in self.entanglement_graph.get(current_id, {}).items():
                if neighbor_id not in visited:
                    neighbor_state = self.states[neighbor_id]
                    
                    # Apply influence (quantum interference effect)
                    influence = current_intensity * coupling_strength * decay
                    neighbor_state.maliciousness.magnitude += influence * 0.05
                    neighbor_state.maliciousness.phase += influence * 0.1
                    
                    to_process.append((neighbor_id, influence))
    
    def evolve_all_states(self, time_step: float) -> None:
        """Evolve all states through one time step."""
        for state in self.states.values():
            state.evolve_state(time_step)
    
    def get_highest_drift_threat(self) -> Optional[ThreatStateVector]:
        """Identify threat with highest amplitude drift (most dangerous)."""
        if not self.states:
            return None
        return max(self.states.values(), key=lambda s: s.get_amplitude_drift())


# ============================================================================
# MEASUREMENT ENGINE: Collapse superpositions into decisions
# ============================================================================

class MeasurementBasis(Enum):
    """
    Different measurement bases reveal different aspects of threat state.
    Like quantum mechanics: measuring in X basis destroys Y information.
    """
    MALICE_BASIS = "malice"
    PERSISTENCE_BASIS = "persistence"
    TRANSMISSIBILITY_BASIS = "transmit"
    HOLISTIC_BASIS = "holistic"


@dataclass
class MeasurementEvent:
    """Records a single measurement collapse event."""
    state_id: str
    basis: MeasurementBasis
    collapsed_value: float              # Result of collapse [0, 1]
    uncertainty_reduction: float        # Entropy removed
    timestamp: datetime = field(default_factory=datetime.utcnow)
    observer_id: str = ""
    irreversibility_index: float = 0.0  # How much state changed


@dataclass
class ThreatMeasurementEngine:
    """
    Central measurement authority that collapses threat superpositions.
    
    Properties:
    - Measurement is irreversible
    - Measurement affects system state (observer effect)
    - Different bases reveal different aspects
    - Repeated measurement affects future measurements
    """
    
    ensemble: ThreatStateEnsemble
    measurement_history: List[MeasurementEvent] = field(default_factory=list)
    observer_effect_coefficient: float = 0.5
    measurement_count: int = 0
    state_trajectory: Dict[str, List[Tuple[datetime, float]]] = field(default_factory=dict)
    
    def measure_state(self, state_id: str, basis: MeasurementBasis,
                      observation_context: Optional[Dict] = None) -> float:
        """
        Perform measurement on threat state in specified basis.
        
        Measurement:
        1. Collapses superposition to definite value
        2. Reduces system entropy
        3. Modifies state through observer effect
        4. Affects entangled states
        
        Args:
            state_id: Which state to measure
            basis: Which aspect to reveal
            observation_context: Optional metadata
        
        Returns:
            Collapsed probability value [0, 1]
        """
        if state_id not in self.ensemble.states:
            return 0.0
        
        state = self.ensemble.states[state_id]
        
        # Extract amplitude based on basis
        if basis == MeasurementBasis.MALICE_BASIS:
            amplitude = state.maliciousness
        elif basis == MeasurementBasis.PERSISTENCE_BASIS:
            amplitude = state.persistence
        elif basis == MeasurementBasis.TRANSMISSIBILITY_BASIS:
            amplitude = state.transmissibility
        else:  # HOLISTIC_BASIS
            amplitude = self._compute_holistic_superposition(state)
        
        # Measurement collapses superposition
        pre_measurement_entropy = self._compute_entropy(state)
        collapsed_value = amplitude.probability()
        
        # Apply collapse
        amplitude.coherence = min(1.0, amplitude.coherence + 0.2)
        state.uncertainty.magnitude *= 0.7
        
        post_measurement_entropy = self._compute_entropy(state)
        uncertainty_reduction = pre_measurement_entropy - post_measurement_entropy
        
        # Compute irreversibility
        irreversibility = abs(collapsed_value - amplitude.magnitude) * (1.0 - amplitude.coherence)
        
        # Record measurement
        event = MeasurementEvent(
            state_id=state_id,
            basis=basis,
            collapsed_value=collapsed_value,
            uncertainty_reduction=uncertainty_reduction,
            observer_id=observation_context.get("observer", "") if observation_context else "",
            irreversibility_index=irreversibility
        )
        self.measurement_history.append(event)
        self.measurement_count += 1
        
        # Track trajectory
        if state_id not in self.state_trajectory:
            self.state_trajectory[state_id] = []
        self.state_trajectory[state_id].append((datetime.utcnow(), collapsed_value))
        
        # Apply observer effect
        self._apply_observer_effect(state, collapsed_value, basis)
        
        state.observation_count += 1
        
        return collapsed_value
    
    def measure_and_decide_threat_level(self, state_id: str) -> Tuple[str, float, Dict]:
        """
        Perform complete threat assessment through sequential measurement.
        
        Returns: (threat_level, confidence, measurement_details)
        """
        if state_id not in self.ensemble.states:
            return "UNKNOWN", 0.0, {}
        
        state = self.ensemble.states[state_id]
        
        # Sequential measurement reveals threat
        malice_measure = self.measure_state(state_id, MeasurementBasis.MALICE_BASIS)
        persistence_measure = self.measure_state(state_id, MeasurementBasis.PERSISTENCE_BASIS)
        transmit_measure = self.measure_state(state_id, MeasurementBasis.TRANSMISSIBILITY_BASIS)
        
        # Collapse to decision
        net_threat = (malice_measure * 0.5 + 
                     persistence_measure * 0.3 + 
                     transmit_measure * 0.2)
        
        # Determine level
        if net_threat < 0.2:
            level = "BENIGN"
        elif net_threat < 0.4:
            level = "SUSPICIOUS"
        elif net_threat < 0.6:
            level = "MALICIOUS"
        elif net_threat < 0.8:
            level = "CRITICAL"
        else:
            level = "IMMINENT_THREAT"
        
        # Confidence
        confidence = (malice_measure * state.maliciousness.coherence +
                     persistence_measure * state.persistence.coherence +
                     transmit_measure * state.transmissibility.coherence) / 3.0
        
        return level, net_threat, {
            "malice": malice_measure,
            "persistence": persistence_measure,
            "transmissibility": transmit_measure,
            "confidence": confidence,
            "measurement_count": len([m for m in self.measurement_history if m.state_id == state_id])
        }
    
    def _compute_holistic_superposition(self, state: ThreatStateVector) -> QuantumAmplitude:
        """Compute superposition of all amplitudes for holistic measurement."""
        mag_complex = state.maliciousness.to_complex() * 0.5
        pers_complex = state.persistence.to_complex() * 0.3
        trans_complex = state.transmissibility.to_complex() * 0.2
        
        superposition = mag_complex + pers_complex + trans_complex
        net_mag = abs(superposition)
        net_phase = np.angle(superposition)
        
        return QuantumAmplitude(
            magnitude=min(net_mag, 1.0),
            phase=net_phase,
            coherence=state.uncertainty.coherence
        )
    
    def _compute_entropy(self, state: ThreatStateVector) -> float:
        """Compute Shannon entropy of state's probability distribution."""
        probs = [
            state.maliciousness.probability(),
            state.persistence.probability(),
            state.transmissibility.probability(),
            state.uncertainty.probability(),
        ]
        
        probs = [p for p in probs if p > 1e-10]
        if not probs:
            return 0.0
        
        entropy = -sum(p * np.log2(p) for p in probs)
        return entropy
    
    def _apply_observer_effect(self, state: ThreatStateVector, 
                               collapsed_value: float, basis: MeasurementBasis) -> None:
        """Apply observer effect: measurement changes system state."""
        effect_strength = self.observer_effect_coefficient
        
        if basis == MeasurementBasis.MALICE_BASIS:
            state.maliciousness.magnitude += (collapsed_value - state.maliciousness.magnitude) * effect_strength * 0.5
        elif basis == MeasurementBasis.PERSISTENCE_BASIS:
            state.persistence.magnitude += (collapsed_value - state.persistence.magnitude) * effect_strength * 0.5
        elif basis == MeasurementBasis.TRANSMISSIBILITY_BASIS:
            state.transmissibility.magnitude += (collapsed_value - state.transmissibility.magnitude) * effect_strength * 0.5
        
        # Phase shift
        phase_shift = collapsed_value * np.pi / 4
        state.maliciousness.phase = (state.maliciousness.phase + phase_shift) % (2 * np.pi)
    
    def get_measurement_statistics(self) -> Dict:
        """Analyze measurement patterns across the system."""
        stats = {
            "total_measurements": self.measurement_count,
            "states_measured": len(self.state_trajectory),
            "average_uncertainty_reduction": 0.0,
            "average_irreversibility": 0.0,
            "measurement_basis_distribution": {
                "malice": 0,
                "persistence": 0,
                "transmit": 0,
                "holistic": 0,
            }
        }
        
        if self.measurement_history:
            stats["average_uncertainty_reduction"] = np.mean(
                [m.uncertainty_reduction for m in self.measurement_history]
            )
            stats["average_irreversibility"] = np.mean(
                [m.irreversibility_index for m in self.measurement_history]
            )
            
            # Count basis usage
            for measurement in self.measurement_history:
                basis_key = measurement.basis.value
                if basis_key == "malice":
                    stats["measurement_basis_distribution"]["malice"] += 1
                elif basis_key == "persistence":
                    stats["measurement_basis_distribution"]["persistence"] += 1
                elif basis_key == "transmit":
                    stats["measurement_basis_distribution"]["transmit"] += 1
                else:
                    stats["measurement_basis_distribution"]["holistic"] += 1
        
        return stats


__all__ = [
    'QuantumAmplitude',
    'ThreatStateVector',
    'ThreatStateEnsemble',
    'ThreatMeasurementEngine',
    'MeasurementBasis',
    'MeasurementEvent',
    'ObservableProperty',
]
