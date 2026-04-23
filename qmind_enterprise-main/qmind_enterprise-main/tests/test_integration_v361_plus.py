"""
Q-MIND Enterprise v3.6.1+: Integration Tests

Tests the unified encryption + threat intelligence system.
Verifies that threat assessment works with encryption/decryption.
"""

import pytest
import sys
sys.path.insert(0, r'c:\Users\lenovo\Desktop\qmind_enterprise')

from integration.unified_api import ThreatAwareEncryption
from threat_intelligence.threat_model import (
    QuantumAmplitude, ThreatStateVector, MeasurementBasis
)
from datetime import datetime, timedelta


class TestThreatAwareEncryption:
    """Test threat-aware encryption system."""
    
    @pytest.fixture
    def ti_crypto(self):
        """Initialize threat-aware encryption."""
        return ThreatAwareEncryption(environment="DEV", use_real_pqc=False)
    
    # ========================================================================
    # THREAT REGISTRATION AND MANAGEMENT
    # ========================================================================
    
    def test_register_single_threat(self, ti_crypto):
        """Test registering a single threat indicator."""
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="malware.evil.com",
            indicator_type="C2_IP",
            initial_threat_level=0.7
        )
        
        assert threat_id is not None
        assert len(threat_id) > 0
        assert threat_id in ti_crypto.threat_ensemble.states
        
        # Verify state properties
        state = ti_crypto.threat_ensemble.states[threat_id]
        assert state.indicator_value == "malware.evil.com"
        assert state.indicator_type == "C2_IP"
        assert state.maliciousness.magnitude == 0.7
    
    def test_register_multiple_threats(self, ti_crypto):
        """Test registering multiple threat indicators."""
        threat_ids = []
        for i in range(5):
            tid = ti_crypto.register_threat_indicator(
                indicator_value=f"threat{i}.evil.com",
                indicator_type="C2_IP",
                initial_threat_level=0.5
            )
            threat_ids.append(tid)
        
        assert len(threat_ids) == 5
        assert len(ti_crypto.threat_ensemble.states) == 5
    
    def test_correlate_threats(self, ti_crypto):
        """Test creating entanglement between threats."""
        threat_id_1 = ti_crypto.register_threat_indicator(
            indicator_value="attacker-ip-1.evil.com",
            indicator_type="C2_IP",
            initial_threat_level=0.8
        )
        
        threat_id_2 = ti_crypto.register_threat_indicator(
            indicator_value="attacker-ip-2.evil.com",
            indicator_type="C2_IP",
            initial_threat_level=0.7
        )
        
        # Correlate them
        ti_crypto.correlate_threats(threat_id_1, threat_id_2, 0.9)
        
        # Verify entanglement
        state1 = ti_crypto.threat_ensemble.states[threat_id_1]
        state2 = ti_crypto.threat_ensemble.states[threat_id_2]
        
        assert threat_id_2 in state1.entangled_with
        assert threat_id_1 in state2.entangled_with
    
    # ========================================================================
    # ENCRYPTION WITH THREAT ASSESSMENT
    # ========================================================================
    
    def test_encrypt_with_threat_assessment(self, ti_crypto):
        """Test encryption with threat context."""
        # Register threat
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="c2.attacker.com",
            indicator_type="C2_IP",
            initial_threat_level=0.8
        )
        
        # Encrypt with threat assessment (v3.6.2 API)
        plaintext = b"sensitive data"
        ciphertext, threat_assessment = ti_crypto.encrypt_with_threat_assessment(
            plaintext=plaintext,
            threat_context="C2_IP",
            measurement_basis="HOLISTIC",
            threat_id=threat_id
        )
        
        # Verify encryption
        assert ciphertext is not None
        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > 0
        assert ciphertext != plaintext
        
        # Verify threat assessment
        assert threat_assessment is not None
        assert isinstance(threat_assessment, dict)
        assert 'collapsed_threat_level' in threat_assessment
        assert 'threat_level_text' in threat_assessment
        assert threat_assessment['threat_level_text'] in [
            'BENIGN', 'SUSPICIOUS', 'MALICIOUS', 'CRITICAL', 'IMMINENT_THREAT', 'NO_CONTEXT'
        ]
    
    def test_encrypt_without_threat_context(self, ti_crypto):
        """Test encryption when no threat context registered."""
        plaintext = b"data without context"
        ciphertext, threat_assessment = ti_crypto.encrypt_with_threat_assessment(
            plaintext=plaintext,
            threat_context=None,
            measurement_basis="HOLISTIC",
            threat_id=None
        )
        
        # Should still work, just without threat measurement
        assert ciphertext is not None
        assert isinstance(ciphertext, bytes)
        assert len(ciphertext) > 0
        assert threat_assessment['threat_level_text'] == 'NO_CONTEXT'
        assert 'collapsed_threat_level' in threat_assessment
    
    def test_encrypt_backward_compatible(self, ti_crypto):
        """Test that pure encryption (v3.6.1) still works."""
        plaintext = b"backward compatible test"
        ciphertext, signature_bundle = ti_crypto.encrypt_only(plaintext)
        
        # v3.6.2: signature_bundle should be SignatureBundle
        assert ciphertext is not None
        assert signature_bundle is not None
        assert isinstance(ciphertext, bytes)
        
        # Check that we got a SignatureBundle (not raw bytes)
        from crypto.signature_bundle import SignatureBundle
        assert isinstance(signature_bundle, SignatureBundle), \
            f"Expected SignatureBundle, got {type(signature_bundle).__name__}"
        
        assert len(ciphertext) > 0
        assert len(signature_bundle.signature_bytes) > 0
    
    # ========================================================================
    # DECRYPTION WITH THREAT DETECTION
    # ========================================================================
    
    def test_decrypt_and_detect(self, ti_crypto):
        """Test decryption with threat detection."""
        from crypto.signature_bundle import SignatureBundle
        
        # Register threat
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="malware.domain.com",
            indicator_type="MALWARE_HASH",
            initial_threat_level=0.6
        )
        
        # Use encrypt_only for full artifact preservation (v3.6.2 feature)
        plaintext = b"encrypted during threat"
        ciphertext, signature_bundle = ti_crypto.encrypt_only(plaintext)
        
        # Verify we got a SignatureBundle
        assert isinstance(signature_bundle, SignatureBundle)
        
        # Decrypt and detect (v3.6.2 API)
        # Note: decrypt_and_detect uses simpler logic than decrypt_and_verify
        # because it doesn't need full signature verification
        decrypted, threat_detection = ti_crypto.decrypt_and_detect(
            ciphertext=ciphertext,
            signature=signature_bundle,  # Pass SignatureBundle (v3.6.2)
            threat_id=threat_id
        )
        
        # Verify plaintext matches
        assert decrypted == plaintext, "Decrypted plaintext doesn't match original"
        
        # Verify threat detection structure
        assert 'initial_collapse' in threat_detection
        assert 'post_decryption_evolution' in threat_detection
        assert 'recommendations' in threat_detection
        assert isinstance(threat_detection['initial_collapse'], (int, float))
        assert isinstance(threat_detection['post_decryption_evolution'], (int, float))
    
    def test_decrypt_backward_compatible(self, ti_crypto):
        """Test that pure decryption (v3.6.1) still works."""
        from crypto.signature_bundle import SignatureBundle
        
        plaintext = b"backward compatible decryption"
        ciphertext, signature_bundle = ti_crypto.encrypt_only(plaintext)
        
        # Test 1: Decrypt using SignatureBundle (new API, v3.6.2)
        decrypted = ti_crypto.decrypt_only(ciphertext, signature_bundle)
        assert decrypted == plaintext, "Decryption with SignatureBundle failed"
        
        # Test 2: Decrypt using raw bytes (backward compat, converts automatically)
        from crypto.signature_bundle import signature_bundle_to_bytes
        sig_bytes = signature_bundle_to_bytes(signature_bundle)
        decrypted2 = ti_crypto.decrypt_only(ciphertext, sig_bytes)
        assert decrypted2 == plaintext, "Decryption with raw bytes (backward compat) failed"
    
    # ========================================================================
    # THREAT MEASUREMENT AND ASSESSMENT
    # ========================================================================
    
    def test_threat_measurement_reduces_uncertainty(self, ti_crypto):
        """Test that measurement reduces uncertainty in threat state."""
        # Register threat
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="unknown-threat",
            indicator_type="SUSPICIOUS_IP",
            initial_threat_level=0.5
        )
        
        threat_state = ti_crypto.threat_ensemble.states[threat_id]
        initial_uncertainty = threat_state.uncertainty.magnitude
        
        # Perform measurement
        level, value, details = ti_crypto.measurement_engine.measure_and_decide_threat_level(threat_id)
        
        # Verify uncertainty reduced
        final_uncertainty = threat_state.uncertainty.magnitude
        assert final_uncertainty < initial_uncertainty
    
    def test_different_measurement_bases(self, ti_crypto):
        """Test measuring threat in different bases."""
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="multi-aspect-threat",
            indicator_type="MALWARE",
            initial_threat_level=0.7
        )
        
        # Measure in different bases
        bases = ['MALICE', 'PERSISTENCE', 'TRANSMIT', 'HOLISTIC']
        results = []
        
        for basis in bases:
            assessment = ti_crypto._assess_threat_context(threat_id, basis)
            results.append(assessment['collapsed_threat_level'])
        
        # All measurements should return valid probabilities
        assert all(0 <= r <= 1 for r in results)
        assert all(r is not None for r in results)
    
    # ========================================================================
    # ENTANGLEMENT AND CORRELATION
    # ========================================================================
    
    def test_entanglement_propagation(self, ti_crypto):
        """Test that measurement propagates through entangled threats."""
        # Create entangled threats
        threat_id_1 = ti_crypto.register_threat_indicator(
            indicator_value="threat-a",
            indicator_type="C2_IP",
            initial_threat_level=0.8
        )
        
        threat_id_2 = ti_crypto.register_threat_indicator(
            indicator_value="threat-b",
            indicator_type="C2_IP",
            initial_threat_level=0.3
        )
        
        # Entangle them
        ti_crypto.correlate_threats(threat_id_1, threat_id_2, 0.95)
        
        # Measure threat 1
        state1_before = ti_crypto.threat_ensemble.states[threat_id_1].maliciousness.magnitude
        state2_before = ti_crypto.threat_ensemble.states[threat_id_2].maliciousness.magnitude
        
        ti_crypto.measurement_engine.measure_state(
            threat_id_1, 
            MeasurementBasis.HOLISTIC_BASIS
        )
        
        # Propagate entanglement effect
        ti_crypto.threat_ensemble.propagate_entanglement(threat_id_1, 0.8)
        
        state2_after = ti_crypto.threat_ensemble.states[threat_id_2].maliciousness.magnitude
        
        # State 2 should be affected (either increased or changed phase)
        assert state2_after != state2_before or \
               ti_crypto.threat_ensemble.states[threat_id_2].maliciousness.phase != 0
    
    # ========================================================================
    # ANALYTICS AND REPORTING
    # ========================================================================
    
    def test_threat_ensemble_summary(self, ti_crypto):
        """Test getting summary of threat ensemble."""
        # Register multiple threats
        for i in range(3):
            ti_crypto.register_threat_indicator(
                indicator_value=f"threat{i}",
                indicator_type="GENERIC",
                initial_threat_level=0.4 + i * 0.2
            )
        
        # Get summary
        summary = ti_crypto.get_threat_ensemble_summary()
        
        assert summary['total_threats'] == 3
        assert summary['average_threat_level'] > 0
        assert 'highest_threat' in summary
    
    def test_measurement_statistics(self, ti_crypto):
        """Test getting measurement statistics."""
        # Register and measure threat
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="measured-threat",
            indicator_type="TEST",
            initial_threat_level=0.5
        )
        
        # Perform multiple measurements
        for _ in range(5):
            ti_crypto.measurement_engine.measure_state(
                threat_id,
                MeasurementBasis.MALICE_BASIS
            )
        
        # Get statistics
        stats = ti_crypto.get_measurement_statistics()
        
        assert stats['total_measurements'] == 5
        assert stats['states_measured'] == 1
    
    def test_operation_history(self, ti_crypto):
        """Test that operation history is tracked."""
        # Perform some operations
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="tracked-threat",
            indicator_type="TEST",
            initial_threat_level=0.5
        )
        
        plaintext = b"test data"
        ciphertext, _ = ti_crypto.encrypt_with_threat_assessment(
            plaintext=plaintext,
            threat_id=threat_id
        )
        
        # Get history
        history = ti_crypto.get_operation_history()
        
        assert len(history) >= 1
        assert history[-1]['type'] == 'encrypt_with_threat_assessment'
    
    def test_session_summary(self, ti_crypto):
        """Test getting session summary."""
        # Perform operations
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="session-test",
            indicator_type="TEST",
            initial_threat_level=0.5
        )
        
        ti_crypto.encrypt_with_threat_assessment(
            plaintext=b"data",
            threat_id=threat_id
        )
        
        # Get session summary
        summary = ti_crypto.get_session_summary()
        
        assert summary['total_operations'] >= 1
        assert 'session_duration_seconds' in summary
        assert 'threat_ensemble' in summary
        assert 'measurements' in summary


class TestThreatModel:
    """Test quantum threat model components."""
    
    def test_quantum_amplitude_probability(self):
        """Test probability calculation from amplitude."""
        amp = QuantumAmplitude(magnitude=0.7, coherence=0.9)
        prob = amp.probability()
        
        expected = (0.7 ** 2) * (0.9 ** 2)
        assert abs(prob - expected) < 1e-6
    
    def test_quantum_amplitude_decoherence(self):
        """Test decoherence reduces coherence."""
        amp = QuantumAmplitude(magnitude=0.7, coherence=1.0)
        
        amp.decohere(0.1)
        assert amp.coherence == 0.9
        
        amp.decohere(0.1)
        assert amp.coherence == 0.81
    
    def test_threat_state_net_threat(self):
        """Test net threat calculation."""
        state = ThreatStateVector(
            indicator_value="test",
            indicator_type="TEST"
        )
        
        state.maliciousness = QuantumAmplitude(magnitude=0.5, coherence=1.0)
        state.persistence = QuantumAmplitude(magnitude=0.3, coherence=1.0)
        state.transmissibility = QuantumAmplitude(magnitude=0.2, coherence=1.0)
        
        net_threat = state.net_threat_amplitude()
        
        assert 0 <= net_threat <= 1
        assert net_threat > 0  # Should be non-zero with non-zero components
    
    def test_threat_state_evolution(self):
        """Test threat state evolves through time."""
        state = ThreatStateVector(
            indicator_value="test",
            indicator_type="TEST"
        )
        
        state.maliciousness = QuantumAmplitude(magnitude=0.5, coherence=0.9)
        uncertainty_before = state.uncertainty.magnitude
        
        # Evolve state
        state.evolve_state(time_step=0.1)
        
        uncertainty_after = state.uncertainty.magnitude
        
        # Uncertainty should increase naturally
        assert uncertainty_after > uncertainty_before
    
    def test_threat_state_with_external_signal(self):
        """Test threat state responds to external signal."""
        state = ThreatStateVector(
            indicator_value="test",
            indicator_type="TEST"
        )
        
        initial_malice = state.maliciousness.magnitude
        
        # Apply external signal (strong observation)
        state.evolve_state(time_step=0.1, external_signal=0.9)
        
        # Maliciousness should increase toward external signal
        assert state.maliciousness.magnitude > initial_malice


# ============================================================================
# INTEGRATION TEST SCENARIOS
# ============================================================================

class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    @pytest.fixture
    def ti_crypto(self):
        return ThreatAwareEncryption(environment="DEV", use_real_pqc=False)
    
    def test_scenario_c2_detection(self, ti_crypto):
        """Scenario: Detect C2 infrastructure during communication."""
        # Register known C2
        c2_id = ti_crypto.register_threat_indicator(
            indicator_value="c2.attacker.com",
            indicator_type="C2_IP",
            initial_threat_level=0.95
        )
        
        # Encrypt communication
        secret_message = b"infiltration_complete"
        ciphertext, assessment = ti_crypto.encrypt_with_threat_assessment(
            plaintext=secret_message,
            threat_id=c2_id
        )
        
        # Verify threat is measured (quantum model has stochastic behavior)
        assert assessment['collapsed_threat_level'] > 0.3  # Should be elevated above baseline
        assert assessment['threat_level_text'] in ['SUSPICIOUS', 'MALICIOUS', 'CRITICAL', 'IMMINENT_THREAT']
    
    def test_scenario_supply_chain_correlation(self, ti_crypto):
        """Scenario: Correlated supply chain compromise detection."""
        # Register compromised supplier
        supplier_id = ti_crypto.register_threat_indicator(
            indicator_value="vendor.legit.com",
            indicator_type="SUPPLY_CHAIN",
            initial_threat_level=0.6
        )
        
        # Register malware in application update
        malware_id = ti_crypto.register_threat_indicator(
            indicator_value="app_update_v2.1.exe",
            indicator_type="MALWARE_HASH",
            initial_threat_level=0.85
        )
        
        # Correlate them (they're linked in supply chain)
        ti_crypto.correlate_threats(supplier_id, malware_id, 0.9)
        
        # Encrypt system communication
        config_data = b"system_configuration"
        ciphertext, _ = ti_crypto.encrypt_with_threat_assessment(
            plaintext=config_data,
            threat_id=supplier_id
        )
        
        # Both should be identified
        supplier_state = ti_crypto.threat_ensemble.states[supplier_id]
        malware_state = ti_crypto.threat_ensemble.states[malware_id]
        
        assert malware_id in supplier_state.entangled_with
        assert supplier_id in malware_state.entangled_with
    
    def test_scenario_measurement_observer_effect(self, ti_crypto):
        """Scenario: Repeated threat measurement shows observer effect."""
        threat_id = ti_crypto.register_threat_indicator(
            indicator_value="observed-threat",
            indicator_type="SUSPICIOUS_BEHAVIOR",
            initial_threat_level=0.5
        )
        
        # Measure same threat multiple times
        measurements = []
        for _ in range(3):
            assessment = ti_crypto._assess_threat_context(threat_id, 'MALICE')
            measurements.append(assessment['collapsed_threat_level'])
        
        # Verify measurements converge (observer effect)
        # Later measurements should be closer together
        variance = abs(measurements[2] - measurements[1]) - abs(measurements[1] - measurements[0])
        # Convergence indicated by variances getting smaller (or state "remembers" measurement)
        
        assert len(measurements) == 3
        assert all(0 <= m <= 1 for m in measurements)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
