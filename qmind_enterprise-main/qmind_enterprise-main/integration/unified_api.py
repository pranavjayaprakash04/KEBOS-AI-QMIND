"""
Q-MIND Enterprise v3.6.1+: Unified Encryption + Threat Intelligence API

Integrates v3.6.1 encryption system with quantum threat intelligence model.
Enables real-time threat assessment during cryptographic operations.

Provides:
1. encrypt_with_threat_assessment() - Encrypt while measuring threat
2. decrypt_and_detect() - Decrypt while tracking threat evolution
3. encrypt_only() - Pure encryption (backward compatible)

v3.6.2 Updates:
- SignatureBundle type enforcement
- API normalization for threat context
- Full type safety for all operations
"""

from crypto.enterprise_encryption_v3_6_1 import EnterpriseEncryptionV361, TrustZone, KeyPurpose
from crypto.signature_bundle import SignatureBundle, SignatureAlgorithmType, create_signature_bundle, bytes_to_signature_bundle
from threat_intelligence.threat_model import (
    ThreatStateVector, ThreatStateEnsemble, ThreatMeasurementEngine,
    MeasurementBasis, QuantumAmplitude
)
from typing import Dict, Tuple, Optional, List, Any, Union
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class ThreatAwareEncryption:
    """
    Unified encryption + threat intelligence system.
    
    Combines v3.6.1 cryptography with quantum threat model for:
    - Real-time threat assessment during operations
    - Threat-aware key derivation
    - Observer effect tracking
    - Entanglement monitoring
    """
    
    def __init__(self, environment: str = "PRODUCTION", use_real_pqc: bool = False):
        """
        Initialize threat-aware encryption system.
        
        Args:
            environment: Deployment environment (PRODUCTION, STAGING, DEVELOPMENT)
            use_real_pqc: Use real post-quantum crypto (requires liboqs)
        """
        # Import DeploymentEnvironment
        from crypto.enterprise_encryption_v3_6_1 import DeploymentEnvironment
        
        # Map string to enum
        env_map = {
            "PRODUCTION": DeploymentEnvironment.PRODUCTION,
            "STAGING": DeploymentEnvironment.STAGING,
            "DEVELOPMENT": DeploymentEnvironment.DEVELOPMENT,
            "DEV": DeploymentEnvironment.DEVELOPMENT,  # Alias
        }
        deployment_env = env_map.get(environment, DeploymentEnvironment.PRODUCTION)
        
        # Initialize encryption engine
        self.crypto = EnterpriseEncryptionV361(
            environment=deployment_env,
            enable_pqc=use_real_pqc
        )
        
        # Initialize threat intelligence
        self.threat_ensemble = ThreatStateEnsemble()
        self.measurement_engine = ThreatMeasurementEngine(self.threat_ensemble)
        
        # Operation tracking
        self.operations: List[Dict[str, Any]] = []
        self.session_start = datetime.utcnow()
        
        logger.info("ThreatAwareEncryption initialized")
    
    # ========================================================================
    # THREAT CONTEXT MANAGEMENT
    # ========================================================================
    
    def register_threat_indicator(self, 
                                  indicator_value: str,
                                  indicator_type: str,
                                  initial_threat_level: float = 0.5) -> str:
        """
        Register a threat indicator in the ensemble.
        
        Args:
            indicator_value: The actual indicator (IP, hash, URL, etc.)
            indicator_type: Type of indicator (C2_IP, MALWARE_HASH, etc.)
            initial_threat_level: Initial maliciousness [0, 1]
        
        Returns:
            Threat indicator ID for future reference
        """
        state = ThreatStateVector(
            indicator_value=indicator_value,
            indicator_type=indicator_type
        )
        
        # Initialize threat amplitude
        state.maliciousness = QuantumAmplitude(
            magnitude=initial_threat_level,
            phase=0.0,
            coherence=0.8
        )
        
        # Add to ensemble
        self.threat_ensemble.add_state(state)
        
        logger.info(f"Registered threat indicator: {indicator_type}={indicator_value}")
        return state.indicator_id
    
    def correlate_threats(self, threat_id_1: str, threat_id_2: str, 
                         correlation_strength: float) -> None:
        """
        Create entanglement between two threats (indicate correlation).
        
        Args:
            threat_id_1: First threat indicator ID
            threat_id_2: Second threat indicator ID
            correlation_strength: Strength of correlation [0, 1]
        """
        self.threat_ensemble.entangle_states(threat_id_1, threat_id_2, correlation_strength)
        logger.info(f"Entangled threats: {threat_id_1} <-> {threat_id_2} (strength={correlation_strength})")
    
    # ========================================================================
    # ENCRYPTION WITH THREAT ASSESSMENT
    # ========================================================================
    
    def encrypt_with_threat_assessment(self,
                                       plaintext: bytes,
                                       associated_data: Optional[bytes] = None,
                                       threat_context: Optional[str] = None,
                                       measurement_basis: str = "HOLISTIC",
                                       threat_id: Optional[str] = None) -> Tuple[bytes, Dict[str, Any]]:
        """
        Encrypt data while simultaneously assessing threat context.
        
        Real-time threat measurement occurs during key derivation.
        Encryption is threat-aware: threat level influences nonce generation.
        
        v3.6.2: Uses normalized API (encrypt_with_threat_context).
        
        Args:
            plaintext: Data to encrypt
            associated_data: Optional authenticated data
            threat_context: Type of threat (e.g., "C2_IP", "MALWARE")
            measurement_basis: Which aspect to measure
                - "MALICE": Measure maliciousness only
                - "PERSISTENCE": Measure persistence only
                - "TRANSMIT": Measure transmissibility only
                - "HOLISTIC": Full threat picture
            threat_id: ID of specific threat to measure
        
        Returns:
            (ciphertext, threat_assessment) where threat_assessment contains:
                - collapsed_threat_level: Measured threat probability
                - threat_level_text: BENIGN/SUSPICIOUS/MALICIOUS/CRITICAL
                - confidence: Confidence in measurement
                - persistence_probability: Likelihood of sustained threat
                - entangled_threats: List of correlated threat IDs
                - measurement_timestamp: When measurement occurred
                - observer_effect_applied: Whether state was modified
        """
        start_time = datetime.utcnow()
        
        # 1. MEASURE THREAT BEFORE ENCRYPTION
        threat_assessment = self._assess_threat_context(threat_id, measurement_basis)
        
        # 2. EVOLVE THREAT STATES (temporal dynamics)
        self.threat_ensemble.evolve_all_states(0.01)  # 10ms of evolution
        
        # 3. PERFORM ENCRYPTION using v3.6.2 normalized API
        threat_context_dict = {
            'threat_type': threat_context,
            'threat_id': threat_id,
            'assessment': threat_assessment
        } if threat_context else None
        
        ciphertext, metadata = self.crypto.encrypt_with_threat_context(
            plaintext=plaintext,
            threat_context=threat_context_dict,
            purpose=None,  # Will use default DATA_AT_REST
            tenant_id="default",
            trust_zone=TrustZone.INTERNAL  # Use enum value
        )
        
        # 4. PROPAGATE ENTANGLEMENT (measurement affects correlated threats)
        if threat_id and threat_id in self.threat_ensemble.states:
            threat_state = self.threat_ensemble.states[threat_id]
            self.threat_ensemble.propagate_entanglement(
                threat_id, 
                threat_assessment['collapsed_threat_level'],
                decay=0.8
            )
        
        # 5. RECORD OPERATION
        operation = {
            'type': 'encrypt_with_threat_assessment',
            'timestamp': start_time,
            'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
            'plaintext_size': len(plaintext),
            'ciphertext_size': len(ciphertext),
            'threat_assessment': threat_assessment,
        }
        self.operations.append(operation)
        
        logger.info(f"Encrypted {len(plaintext)} bytes with threat assessment: "
                   f"{threat_assessment['threat_level_text']}")
        
        return ciphertext, threat_assessment
    
    def _assess_threat_context(self, threat_id: Optional[str] = None,
                               measurement_basis: str = "HOLISTIC") -> Dict[str, Any]:
        """
        Perform threat assessment via quantum measurement.
        
        Returns threat assessment dictionary with measured properties.
        """
        if not threat_id or threat_id not in self.threat_ensemble.states:
            return self._get_empty_threat_assessment()
        
        # Convert measurement_basis string to enum
        basis_map = {
            'MALICE': MeasurementBasis.MALICE_BASIS,
            'PERSISTENCE': MeasurementBasis.PERSISTENCE_BASIS,
            'TRANSMIT': MeasurementBasis.TRANSMISSIBILITY_BASIS,
            'HOLISTIC': MeasurementBasis.HOLISTIC_BASIS,
        }
        basis = basis_map.get(measurement_basis, MeasurementBasis.HOLISTIC_BASIS)
        
        # Perform measurement
        threat_level_text, collapsed_value, details = self.measurement_engine.measure_and_decide_threat_level(threat_id)
        
        # Get entangled threats
        threat_state = self.threat_ensemble.states[threat_id]
        entangled_threats = list(threat_state.entangled_with)
        
        return {
            'collapsed_threat_level': collapsed_value,
            'threat_level_text': threat_level_text,
            'confidence': details.get('confidence', 0.0),
            'persistence_probability': details.get('persistence', 0.0),
            'transmissibility_probability': details.get('transmissibility', 0.0),
            'maliciousness_probability': details.get('malice', 0.0),
            'entangled_threats': entangled_threats,
            'measurement_timestamp': datetime.utcnow().isoformat(),
            'observer_effect_applied': True,
            'measurement_basis': measurement_basis,
            'indicator_type': threat_state.indicator_type,
            'indicator_value': threat_state.indicator_value,
            'observation_count': threat_state.observation_count
        }
    
    def _get_empty_threat_assessment(self) -> Dict[str, Any]:
        """Return empty threat assessment when no threat context."""
        return {
            'collapsed_threat_level': 0.0,
            'threat_level_text': 'NO_CONTEXT',
            'confidence': 0.0,
            'persistence_probability': 0.0,
            'transmissibility_probability': 0.0,
            'maliciousness_probability': 0.0,
            'entangled_threats': [],
            'measurement_timestamp': datetime.utcnow().isoformat(),
            'observer_effect_applied': False,
            'measurement_basis': 'NONE',
            'indicator_type': 'NONE',
            'indicator_value': 'NONE',
            'observation_count': 0
        }
    
    # ========================================================================
    # DECRYPTION WITH THREAT DETECTION
    # ========================================================================
    
    def decrypt_and_detect(self,
                          ciphertext: bytes,
                          signature: Union[SignatureBundle, bytes],
                          associated_data: Optional[bytes] = None,
                          threat_id: Optional[str] = None,
                          measurement_basis: str = "PERSISTENCE") -> Tuple[bytes, Dict[str, Any]]:
        """
        Decrypt data while tracking threat evolution and detection.
        
        Measures threat evolution during decryption.
        Detects changes in threat state that occurred since encryption.
        
        v3.6.2: Accepts SignatureBundle for type safety.
        
        Args:
            ciphertext: Encrypted data
            signature: Cryptographic signature (SignatureBundle or bytes)
            associated_data: Optional authenticated data
            threat_id: ID of threat to monitor
            measurement_basis: Which aspect to measure
        
        Returns:
            (plaintext, threat_detection) where threat_detection contains:
                - initial_collapse: Threat level at start of decryption
                - post_decryption_evolution: Threat level after decryption
                - threat_changed: Whether threat state evolved
                - new_entanglements: New threats detected during operation
                - persistence_prediction: Forecast of threat persistence
                - recommendations: Analyst recommendations
                - analyst_summary: Human-readable summary
        """
        start_time = datetime.utcnow()
        
        # v3.6.2: Type enforcement - ensure SignatureBundle
        sig_bundle = self._ensure_signature_bundle(signature)
        
        # 1. MEASURE THREAT BEFORE DECRYPTION
        initial_assessment = self._assess_threat_context(threat_id, measurement_basis)
        initial_collapse = initial_assessment['collapsed_threat_level']
        
        # 2. PERFORM DECRYPTION
        # Use decrypt_only which handles artifacts properly and supports threat context
        plaintext = self.decrypt_only(ciphertext, sig_bundle)
        
        # 3. MEASURE THREAT AFTER DECRYPTION
        # Threat may have evolved during our operation
        post_assessment = self._assess_threat_context(threat_id, measurement_basis)
        post_collapse = post_assessment['collapsed_threat_level']
        
        # 4. COMPUTE THREAT EVOLUTION
        threat_delta = post_collapse - initial_collapse
        threat_changed = abs(threat_delta) > 0.05  # >5% change significant
        
        # 5. PREDICT PERSISTENCE
        if threat_id and threat_id in self.threat_ensemble.states:
            threat_state = self.threat_ensemble.states[threat_id]
            persistence_prob = threat_state.persistence.probability()
            drift = threat_state.get_amplitude_drift()
        else:
            persistence_prob = 0.0
            drift = 0.0
        
        # 6. BUILD DETECTION REPORT
        threat_detection = {
            'initial_collapse': initial_collapse,
            'post_decryption_evolution': post_collapse,
            'threat_delta': threat_delta,
            'threat_changed': threat_changed,
            'new_entanglements': post_assessment.get('entangled_threats', []),
            'persistence_prediction': persistence_prob,
            'drift_velocity': drift,
            'measurement_basis': measurement_basis,
            'detection_timestamp': datetime.utcnow().isoformat(),
            'operation_duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
            'plaintext_size': len(plaintext) if plaintext else 0,
            'recommendations': self._generate_recommendations(post_collapse, persistence_prob, drift),
            'analyst_summary': self._generate_analyst_summary(
                initial_collapse, post_collapse, persistence_prob, 
                threat_id, threat_state=self.threat_ensemble.states.get(threat_id)
            )
        }
        
        # 7. RECORD OPERATION
        operation = {
            'type': 'decrypt_and_detect',
            'timestamp': start_time,
            'threat_detection': threat_detection
        }
        self.operations.append(operation)
        
        logger.info(f"Decrypted {len(plaintext)} bytes. Threat evolution: "
                   f"{initial_collapse:.3f} → {post_collapse:.3f}")
        
        return plaintext, threat_detection
    
    def _generate_recommendations(self, threat_level: float, 
                                  persistence: float, drift: float) -> List[str]:
        """Generate analyst recommendations based on threat metrics."""
        recommendations = []
        
        if threat_level > 0.8:
            recommendations.append("escalate_to_incident_response")
            recommendations.append("isolate_affected_systems")
        
        if threat_level > 0.6 and persistence > 0.7:
            recommendations.append("investigate_sustained_threat")
            recommendations.append("check_for_c2_communication")
        
        if drift > 0.1:  # Rapidly changing threat
            recommendations.append("monitor_closely_for_escalation")
        
        if len(recommendations) == 0:
            recommendations.append("continue_monitoring")
        
        return recommendations
    
    def _generate_analyst_summary(self, initial: float, final: float, 
                                 persistence: float, threat_id: Optional[str],
                                 threat_state: Optional[ThreatStateVector] = None) -> str:
        """Generate human-readable analyst summary."""
        parts = []
        
        if threat_id and threat_state:
            parts.append(f"Threat: {threat_state.indicator_type}={threat_state.indicator_value}")
        
        parts.append(f"Initial assessment: {self._threat_label(initial)}")
        parts.append(f"Post-operation assessment: {self._threat_label(final)}")
        
        if abs(final - initial) > 0.05:
            direction = "increased" if final > initial else "decreased"
            change = abs(final - initial)
            parts.append(f"Threat {direction} by {change:.1%}")
        else:
            parts.append("Threat remains stable")
        
        if persistence > 0.7:
            parts.append(f"High persistence ({persistence:.0%}): likely sustained threat")
        elif persistence < 0.3:
            parts.append(f"Low persistence ({persistence:.0%}): likely transient indicator")
        
        return " | ".join(parts)
    
    def _threat_label(self, level: float) -> str:
        """Convert threat level to label."""
        if level < 0.2:
            return "BENIGN"
        elif level < 0.4:
            return "SUSPICIOUS"
        elif level < 0.6:
            return "MALICIOUS"
        elif level < 0.8:
            return "CRITICAL"
        else:
            return "IMMINENT_THREAT"
    
    # ========================================================================
    # BACKWARD COMPATIBLE: Pure Encryption (v3.6.1)
    # ========================================================================
    
    def encrypt_only(self,
                    plaintext: bytes,
                    associated_data: Optional[bytes] = None) -> Tuple[bytes, Union[SignatureBundle, bytes]]:
        """
        Pure encryption without threat assessment (backward compatible).
        
        v3.6.2: Returns SignatureBundle for type safety.
        
        Args:
            plaintext: Data to encrypt
            associated_data: Optional authenticated data
        
        Returns:
            (ciphertext, signature_bundle)
        
        Note: Returns SignatureBundle, not raw bytes.
              Use signature_bundle.signature_bytes to get raw bytes if needed.
              Also stores full encrypted_artifact internally for later decryption.
        """
        # Import SignedEntityType from crypto module
        from crypto.pqc_signatures import SignedEntityType
        
        # encrypt_and_sign returns a dict
        artifact = self.crypto.encrypt_and_sign(
            plaintext=plaintext,
            entity_id="default",
            entity_type=SignedEntityType.MODEL_UPDATE,  # Generic type for backward compat
            purpose=KeyPurpose.DATA_AT_REST,
            tenant_id="default",
            trust_zone=TrustZone.INTERNAL
        )
        
        # Extract ciphertext from dict result
        ciphertext = bytes.fromhex(artifact['ciphertext'])
        sig_bytes = bytes.fromhex(artifact['signature'])
        
        # Store the full artifact for later decryption (v3.6.2 feature)
        # Attach it as metadata in the SignatureBundle
        sig_bundle = create_signature_bundle(
            signature_bytes=sig_bytes,
            algorithm=SignatureAlgorithmType.PQC_DILITHIUM_3,
            key_version=1,
            entity_type="encrypted_data",
            signer_id="v3.6.1"
        )
        
        # Store encrypted artifact in memory for this session (v3.6.2 enhancement)
        # This maps ciphertext to full artifact for decryption
        if not hasattr(self, '_encrypted_artifacts'):
            self._encrypted_artifacts = {}
        artifact_key = ciphertext[:32].hex()  # Use first 32 bytes as key
        self._encrypted_artifacts[artifact_key] = artifact
        
        # Store the key in the signature bundle metadata for retrieval
        sig_bundle.metadata['_artifact_key'] = artifact_key
        
        return ciphertext, sig_bundle
    
    def decrypt_only(self,
                    ciphertext: bytes,
                    signature: Union[SignatureBundle, bytes],
                    associated_data: Optional[bytes] = None) -> bytes:
        """
        Pure decryption without threat detection (backward compatible).
        
        v3.6.2: Accepts both SignatureBundle and raw bytes for compatibility.
        
        Args:
            ciphertext: Encrypted data
            signature: Signature (SignatureBundle or raw bytes for backward compat)
            associated_data: Optional authenticated data
        
        Returns:
            Decrypted plaintext
        """
        # Type enforcement: convert raw bytes to SignatureBundle if needed (for backward compat)
        if isinstance(signature, bytes):
            # Warn about deprecated bytes usage
            logger.warning(
                "decrypt_only called with raw bytes signature. "
                "Use SignatureBundle for v3.6.2+. Converting automatically for backward compatibility."
            )
            signature = bytes_to_signature_bundle(signature)
        
        # Type check: ensure we have SignatureBundle now
        if not isinstance(signature, SignatureBundle):
            raise TypeError(
                f"signature must be SignatureBundle or bytes, got {type(signature).__name__}. "
                "This is v3.6.2 which enforces type safety for signatures."
            )
        
        # Try to retrieve the stored encrypted artifact (v3.6.2 enhancement)
        artifact = None
        if hasattr(self, '_encrypted_artifacts') and 'method' in signature.metadata.get('_artifact_key', ''):
            artifact_key = signature.metadata.get('_artifact_key')
            if artifact_key and artifact_key in self._encrypted_artifacts:
                artifact = self._encrypted_artifacts[artifact_key]
        
        # If we don't have the artifact, try to find it by ciphertext
        if artifact is None and hasattr(self, '_encrypted_artifacts'):
            ciphertext_key = ciphertext[:32].hex()
            if ciphertext_key in self._encrypted_artifacts:
                artifact = self._encrypted_artifacts[ciphertext_key]
        
        # If we still don't have the artifact, we need to create a minimal one
        if artifact is None:
            # Create minimal artifact from components
            logger.warning(
                "Decrypting without full encrypted artifact. "
                "Using placeholders for missing metadata. "
                "For best results, use encrypt_with_threat_assessment or preserve full artifacts."
            )
            artifact = {
                'ciphertext': ciphertext.hex() if isinstance(ciphertext, bytes) else ciphertext,
                'signature': signature.signature_bytes.hex() if isinstance(signature.signature_bytes, bytes) else signature.signature_bytes,
                'nonce': '00' * 12,  # Placeholder
                'tag': '00' * 16,     # Placeholder
                'public_key': '00' * 32,  # Placeholder
                'metadata': {},
            }
        
        # Decrypt using the artifact
        try:
            plaintext, sig_valid = self.crypto.decrypt_and_verify(
                encrypted_artifact=artifact,
                purpose=KeyPurpose.DATA_AT_REST,
                tenant_id="default",
                trust_zone=TrustZone.INTERNAL
            )
            return plaintext
        except (ValueError, KeyError, AttributeError) as e:
            # If decrypt_and_verify fails, try simpler approach
            logger.error(f"decrypt_and_verify failed: {e}. Cannot complete decryption.")
            raise ValueError(
                f"Decryption failed: {e}. "
                "This may be because the encrypted artifact is incomplete or corrupted. "
                "For v3.6.2+, ensure full artifacts are preserved."
            ) from e
    
    # ========================================================================
    # TYPE ENFORCEMENT AND VALIDATION
    # ========================================================================
    
    @staticmethod
    def _ensure_signature_bundle(signature: Any) -> SignatureBundle:
        """
        Enforce that signature is a SignatureBundle (v3.6.2 type safety).
        
        Raises:
            TypeError: If signature is not SignatureBundle or bytes
        """
        if isinstance(signature, SignatureBundle):
            return signature
        elif isinstance(signature, bytes):
            # Backward compatibility: convert bytes to SignatureBundle
            return bytes_to_signature_bundle(signature, algorithm=SignatureAlgorithmType.LEGACY_V36)
        else:
            raise TypeError(
                f"Invalid signature type: {type(signature).__name__}. "
                f"Expected SignatureBundle or bytes. "
                f"This is required by v3.6.2 API normalization."
            )
    
    @staticmethod
    def _ensure_plaintext_bytes(data: Any) -> bytes:
        """Enforce that plaintext is bytes."""
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode('utf-8')
        else:
            raise TypeError(f"Plaintext must be bytes or str, got {type(data).__name__}")
    
    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================
    
    def get_threat_ensemble_summary(self) -> Dict[str, Any]:
        """Get summary of all threats in ensemble."""
        if not self.threat_ensemble.states:
            return {
                'total_threats': 0,
                'average_threat_level': 0.0,
                'highest_threat': None
            }
        
        states = list(self.threat_ensemble.states.values())
        threat_levels = [s.net_threat_amplitude() for s in states]
        
        highest_threat_state = max(states, key=lambda s: s.net_threat_amplitude())
        
        return {
            'total_threats': len(states),
            'average_threat_level': sum(threat_levels) / len(threat_levels),
            'max_threat_level': max(threat_levels),
            'highest_threat': {
                'id': highest_threat_state.indicator_id,
                'type': highest_threat_state.indicator_type,
                'value': highest_threat_state.indicator_value,
                'level': highest_threat_state.net_threat_amplitude(),
                'entangled_count': len(highest_threat_state.entangled_with)
            },
            'total_entanglements': sum(
                len(s.entangled_with) for s in states
            ) // 2  # Divide by 2 since each entanglement is bidirectional
        }
    
    def get_measurement_statistics(self) -> Dict[str, Any]:
        """Get statistics on threat measurements performed."""
        return self.measurement_engine.get_measurement_statistics()
    
    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get history of all encryption/decryption operations."""
        return self.operations
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of entire session."""
        session_duration = (datetime.utcnow() - self.session_start).total_seconds()
        
        return {
            'session_start': self.session_start.isoformat(),
            'session_duration_seconds': session_duration,
            'total_operations': len(self.operations),
            'encrypt_operations': len([o for o in self.operations if o['type'] == 'encrypt_with_threat_assessment']),
            'decrypt_operations': len([o for o in self.operations if o['type'] == 'decrypt_and_detect']),
            'threat_ensemble': self.get_threat_ensemble_summary(),
            'measurements': self.get_measurement_statistics()
        }


__all__ = [
    'ThreatAwareEncryption',
]
