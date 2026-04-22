"""
Threat Detection Services

Enhanced two-stage threat detection pipeline:
1. CatBoost-based anomaly detection and attack classification
2. Comprehensive threat analysis and reporting
"""

import asyncio
import json
import numpy as np
import pandas as pd
import joblib
import catboost as cb
from sklearn.preprocessing import LabelEncoder, StandardScaler
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import logging
from pathlib import Path

from threat_detection.models import (
    NetworkPacket, 
    AnomalyReport, 
    ThreatAlert, 
    ThreatLevel, 
    AttackType,
    SIEMEvent,
    ThreatIntelligence
)

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for threat detection services"""
    def __init__(self, message: str, error_code: str = "THREAT_DETECTION_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ModelLoadError(ServiceError):
    """Model loading specific errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "MODEL_LOAD_ERROR", details)


class CatBoostAnomalyDetector:
    """
    Stage 1: CatBoost-based two-step anomaly detection
    1. Binary classification: Benign vs Attack
    2. Multiclass classification: Attack type classification
    """
    
    def __init__(self, model_path: Optional[str] = None):
        # Use the models saved from our notebook
        self.model_base_path = Path(model_path) if model_path else Path("../notebooks/models/cicids_basic")
        
        # Models and preprocessors
        self.binary_model = None
        self.multiclass_model = None
        self.scaler = None
        self.label_encoder = None
        
        # Feature names (must match the training data)
        self.feature_names = [
            'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
            'Total Length of Fwd Packets', 'Total Length of Bwd Packets', 'Fwd Packet Length Max',
            'Fwd Packet Length Min', 'Fwd Packet Length Mean', 'Fwd Packet Length Std',
            'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
            'Bwd Packet Length Std', 'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean',
            'Flow IAT Std', 'Flow IAT Max', 'Flow IAT Min', 'Fwd IAT Total', 'Fwd IAT Mean',
            'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min', 'Bwd IAT Total', 'Bwd IAT Mean',
            'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min', 'Fwd PSH Flags', 'Bwd PSH Flags',
            'Fwd URG Flags', 'Bwd URG Flags', 'Fwd Header Length', 'Bwd Header Length',
            'Fwd Packets/s', 'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length',
            'Packet Length Mean', 'Packet Length Std', 'Packet Length Variance', 'FIN Flag Count',
            'SYN Flag Count', 'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count',
            'URG Flag Count', 'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio',
            'Average Packet Size', 'Avg Fwd Segment Size', 'Avg Bwd Segment Size',
            'Fwd Header Length.1', 'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk',
            'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk',
            'Bwd Avg Bulk Rate', 'Subflow Fwd Packets', 'Subflow Fwd Bytes',
            'Subflow Bwd Packets', 'Subflow Bwd Bytes', 'Init_Win_bytes_forward',
            'Init_Win_bytes_backward', 'act_data_pkt_fwd', 'min_seg_size_forward',
            'Active Mean', 'Active Std', 'Active Max', 'Active Min', 'Idle Mean',
            'Idle Std', 'Idle Max', 'Idle Min'
        ]
        
    async def initialize(self):
        """Initialize the CatBoost models and preprocessors"""
        try:
            logger.info(f"Loading CatBoost models from {self.model_base_path}")
            
            # Load binary classifier
            binary_model_path = self.model_base_path / "binary_classifier_basic.cbm"
            if binary_model_path.exists():
                self.binary_model = cb.CatBoostClassifier()
                self.binary_model.load_model(str(binary_model_path))
                logger.info("Binary classifier loaded successfully")
            else:
                logger.warning(f"Binary model not found: {binary_model_path}")
                
            # Load multiclass classifier
            multiclass_model_path = self.model_base_path / "multiclass_classifier_basic.cbm"
            if multiclass_model_path.exists():
                self.multiclass_model = cb.CatBoostClassifier()
                self.multiclass_model.load_model(str(multiclass_model_path))
                logger.info("Multiclass classifier loaded successfully")
            else:
                logger.warning(f"Multiclass model not found: {multiclass_model_path}")
                
            # Load scaler
            scaler_path = self.model_base_path / "scaler_basic.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                logger.info("Feature scaler loaded successfully")
            else:
                logger.warning(f"Scaler not found: {scaler_path}")
                
            # Load label encoder
            label_encoder_path = self.model_base_path / "label_encoder_basic.pkl"
            if label_encoder_path.exists():
                self.label_encoder = joblib.load(label_encoder_path)
                logger.info("Label encoder loaded successfully")
            else:
                logger.warning(f"Label encoder not found: {label_encoder_path}")
                
            if not any([self.binary_model, self.multiclass_model]):
                logger.warning("No models loaded, falling back to statistical detection")
                await self._initialize_baseline()
                
        except Exception as e:
            logger.error(f"Error initializing CatBoost models: {e}")
            raise ModelLoadError(f"Failed to initialize CatBoost models: {e}")
    
    async def _initialize_baseline(self):
        """Initialize baseline statistics for fallback detection"""
        self.baseline_stats = {
            'payload_size_mean': 1024.0,
            'payload_size_std': 512.0,
            'port_range': (1, 65535),
            'normal_hours': list(range(8, 18)),  # Business hours
        }
        
    def extract_features(self, packet: NetworkPacket, context: Dict[str, Any] = None) -> np.ndarray:
        """Extract features from network packet to match CICIDS format"""
        context = context or {}
        
        # Create a feature vector that approximates CICIDS features
        # Note: This is a simplified mapping from NetworkPacket to CICIDS features
        # In production, you would need more sophisticated feature extraction
        
        features = np.zeros(len(self.feature_names))
        
        # Map available packet features to CICIDS features
        features[0] = float(packet.destination_port)  # Destination Port
        features[1] = 1000.0  # Flow Duration (approximate)
        features[2] = 1.0     # Total Fwd Packets
        features[3] = 0.0     # Total Backward Packets (unknown for single packet)
        features[4] = float(packet.payload_size)  # Total Length of Fwd Packets
        features[5] = 0.0     # Total Length of Bwd Packets
        features[6] = float(packet.payload_size)  # Fwd Packet Length Max
        features[7] = float(packet.payload_size)  # Fwd Packet Length Min
        features[8] = float(packet.payload_size)  # Fwd Packet Length Mean
        features[9] = 0.0     # Fwd Packet Length Std
        
        # Fill in time-based features
        features[16] = 1000.0  # Flow IAT Mean
        features[21] = 1000.0  # Fwd IAT Mean
        features[26] = 0.0     # Bwd IAT Mean
        
        # Port-based features
        features[34] = 20.0    # Fwd Header Length (typical TCP header)
        features[35] = 20.0    # Bwd Header Length
        
        # Packet size statistics
        features[37] = float(packet.payload_size)  # Min Packet Length
        features[38] = float(packet.payload_size)  # Max Packet Length
        features[39] = float(packet.payload_size)  # Packet Length Mean
        features[40] = 0.0     # Packet Length Std
        features[41] = 0.0     # Packet Length Variance
        
        # Protocol flags (simplified)
        if packet.protocol.upper() == 'TCP':
            features[44] = 1.0  # SYN Flag Count
            features[46] = 1.0  # ACK Flag Count
        
        # Window sizes (typical values)
        features[62] = 65535.0  # Init_Win_bytes_forward
        features[63] = 65535.0  # Init_Win_bytes_backward
        
        return features

    async def detect_anomaly(
        self, 
        packet: NetworkPacket, 
        context: Dict[str, Any] = None
    ) -> Optional[AnomalyReport]:
        """
        Two-step detection using CatBoost models:
        1. Binary classification (Benign vs Attack)
        2. If attack, classify attack type
        """
        try:
            features = self.extract_features(packet, context)
            
            if self.binary_model is not None:
                # Step 1: Binary classification
                is_attack, attack_confidence = await self._binary_classification(features)
                
                if is_attack:
                    # Step 2: Attack type classification
                    attack_type, type_confidence = await self._attack_classification(features)
                    
                    # Create anomaly report with attack details
                    return AnomalyReport(
                        id=str(uuid4()),
                        timestamp=datetime.utcnow(),
                        anomaly_score=attack_confidence,
                        confidence=type_confidence,
                        features={name: float(val) for name, val in zip(self.feature_names, features)},
                        reconstruction_error=attack_confidence,
                        baseline_deviation=attack_confidence,
                        attack_type=attack_type,
                        detection_method="CatBoost Two-Step"
                    )
                else:
                    return None  # Benign traffic
            else:
                # Fallback to statistical detection
                anomaly_score = self._statistical_anomaly_detection(features, packet)
                if anomaly_score > 0.7:  # Threshold for statistical detection
                    return AnomalyReport(
                        id=str(uuid4()),
                        timestamp=datetime.utcnow(),
                        anomaly_score=anomaly_score,
                        confidence=anomaly_score * 0.8,
                        features={name: float(val) for name, val in zip(self.feature_names, features)},
                        reconstruction_error=anomaly_score,
                        baseline_deviation=anomaly_score,
                        detection_method="Statistical Fallback"
                    )
                return None
            
        except Exception as e:
            logger.error(f"Error in CatBoost anomaly detection: {e}")
            return None
    
    async def _binary_classification(self, features: np.ndarray) -> Tuple[bool, float]:
        """Binary classification: Benign (0) vs Attack (1)"""
        try:
            # Reshape and scale features
            features_scaled = self._preprocess_features(features)
            
            # Get prediction and probability
            prediction = self.binary_model.predict(features_scaled)[0]
            probabilities = self.binary_model.predict_proba(features_scaled)[0]
            
            is_attack = bool(prediction == 1)
            confidence = float(probabilities[1] if is_attack else probabilities[0])
            
            return is_attack, confidence
            
        except Exception as e:
            logger.error(f"Error in binary classification: {e}")
            return False, 0.0
    
    async def _attack_classification(self, features: np.ndarray) -> Tuple[str, float]:
        """Multiclass attack type classification"""
        try:
            if self.multiclass_model is None or self.label_encoder is None:
                return "Unknown", 0.5
                
            # Reshape and scale features
            features_scaled = self._preprocess_features(features)
            
            # Get prediction and probability
            prediction = self.multiclass_model.predict(features_scaled)[0]
            probabilities = self.multiclass_model.predict_proba(features_scaled)[0]
            
            # Convert to attack type name
            if prediction < len(self.label_encoder.classes_):
                attack_type = self.label_encoder.classes_[prediction]
                confidence = float(np.max(probabilities))
            else:
                attack_type = "Unknown"
                confidence = 0.5
                
            return attack_type, confidence
            
        except Exception as e:
            logger.error(f"Error in attack classification: {e}")
            return "Unknown", 0.5
    
    def _preprocess_features(self, features: np.ndarray) -> np.ndarray:
        """Preprocess features for model input"""
        try:
            # Reshape to 2D array
            features_2d = features.reshape(1, -1)
            
            # Scale features if scaler is available
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features_2d)
            else:
                # Simple normalization fallback
                features_scaled = (features_2d - np.mean(features_2d)) / (np.std(features_2d) + 1e-8)
            
            return features_scaled
            
        except Exception as e:
            logger.error(f"Error preprocessing features: {e}")
            return features.reshape(1, -1)
    
    def _statistical_anomaly_detection(self, features: np.ndarray, packet: NetworkPacket) -> float:
        """Fallback statistical anomaly detection"""
        anomaly_indicators = []
        
        # Check payload size (index 4 in our feature vector)
        if len(features) > 4:
            payload_score = abs(features[4] - self.baseline_stats['payload_size_mean']) / self.baseline_stats['payload_size_std']
            anomaly_indicators.append(min(payload_score / 3, 1.0))
        
        # Check unusual ports
        if packet.source_port > 50000 or packet.destination_port > 50000:
            anomaly_indicators.append(0.3)
        
        # Check time-based anomalies
        if packet.timestamp.hour not in self.baseline_stats['normal_hours']:
            anomaly_indicators.append(0.2)
        
        return min(np.mean(anomaly_indicators) if anomaly_indicators else 0.0, 1.0)


class AttackClassifier:
    """
    Stage 2: Attack type classification and threat mapping
    Maps CatBoost attack types to MITRE ATT&CK framework
    """
    
    def __init__(self):
        # Attack type mapping from CICIDS labels to MITRE ATT&CK
        self.attack_patterns = {
            'Bot': AttackType.COMMAND_CONTROL,
            'DDoS': AttackType.IMPACT,
            'DoS Hulk': AttackType.IMPACT,
            'DoS GoldenEye': AttackType.IMPACT,
            'DoS slowloris': AttackType.IMPACT,
            'DoS Slowhttptest': AttackType.IMPACT,
            'FTP-Patator': AttackType.CREDENTIAL_ACCESS,
            'SSH-Patator': AttackType.CREDENTIAL_ACCESS,
            'PortScan': AttackType.DISCOVERY,
            'Web Attack � Brute Force': AttackType.CREDENTIAL_ACCESS,
            'Web Attack � XSS': AttackType.INITIAL_ACCESS,
            'Web Attack  Brute Force': AttackType.CREDENTIAL_ACCESS,
            'Web Attack  XSS': AttackType.INITIAL_ACCESS,
            'Infiltration': AttackType.LATERAL_MOVEMENT,
            'Heartbleed': AttackType.INITIAL_ACCESS,
        }
        
    async def initialize(self):
        """Initialize the attack classification model"""
        # Since we're using the CatBoost detection, no additional initialization needed
        logger.info("Attack classifier initialized (using CatBoost attack types)")
        
    async def classify_attack(
        self, 
        packet: NetworkPacket, 
        anomaly_report: AnomalyReport,
        context: Dict[str, Any] = None
    ) -> Tuple[AttackType, float]:
        """
        Map CatBoost attack type to MITRE ATT&CK framework
        Returns (attack_type, confidence_score)
        """
        try:
            # Get attack type from anomaly report
            catboost_attack_type = anomaly_report.attack_type
            confidence = anomaly_report.confidence
            
            if catboost_attack_type and catboost_attack_type in self.attack_patterns:
                # Map to MITRE ATT&CK
                mitre_attack_type = self.attack_patterns[catboost_attack_type]
                return mitre_attack_type, confidence
            else:
                # Fallback to rule-based classification
                return self._rule_based_classification(packet, anomaly_report, context)
                
        except Exception as e:
            logger.error(f"Error in attack classification: {e}")
            return AttackType.DISCOVERY, 0.5  # Default safe classification
    
    def _rule_based_classification(
        self, 
        packet: NetworkPacket, 
        anomaly_report: AnomalyReport,
        context: Dict[str, Any] = None
    ) -> Tuple[AttackType, float]:
        """Rule-based attack classification fallback"""
        context = context or {}
        
        # Port-based classification
        if packet.destination_port in [22, 23]:  # SSH, Telnet
            return AttackType.CREDENTIAL_ACCESS, 0.6
        elif packet.destination_port in [80, 443, 8080]:  # HTTP, HTTPS
            return AttackType.INITIAL_ACCESS, 0.6
        elif packet.destination_port in [21, 25, 110, 143]:  # FTP, SMTP, POP3, IMAP
            return AttackType.COLLECTION, 0.6
        elif packet.destination_port > 1024:
            return AttackType.DISCOVERY, 0.5
        
        # Traffic pattern-based classification
        packet_rate = context.get('packet_rate', 0)
        if packet_rate > 100:  # High packet rate
            return AttackType.IMPACT, 0.7  # Likely DDoS
        elif packet_rate > 10:
            return AttackType.DISCOVERY, 0.6  # Likely scanning
        
        # Default classification
        return AttackType.DISCOVERY, 0.5


class TwoStageDetectionEngine:
    """
    Main detection engine coordinating the two-stage pipeline:
    1. Autoencoder anomaly detection
    2. Attack classification for anomalies
    """
    
    def __init__(self):
        self.anomaly_detector = CatBoostAnomalyDetector()
        self.attack_classifier = AttackClassifier()
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize both detection stages"""
        try:
            await self.anomaly_detector.initialize()
            await self.attack_classifier.initialize()
            self.is_initialized = True
            logger.info("Two-stage detection engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize detection engine: {e}")
            raise
    
    async def process_packet(
        self, 
        packet: NetworkPacket, 
        context: Dict[str, Any] = None
    ) -> Optional[ThreatAlert]:
        """
        Process a single packet through the two-stage detection pipeline
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Stage 1: Anomaly Detection
            anomaly_report = await self.anomaly_detector.detect_anomaly(packet, context)
            
            if anomaly_report is None:
                # Not anomalous, no threat
                return None
            
            # Stage 2: Attack Classification (only for anomalous packets)
            attack_type, confidence = await self.attack_classifier.classify_attack(
                packet, anomaly_report, context
            )
            
            # Determine threat level based on anomaly score and attack type
            threat_level = self._determine_threat_level(anomaly_report.anomaly_score, attack_type)
            
            # Create comprehensive threat alert
            threat_alert = await self._create_threat_alert(
                packet, anomaly_report, attack_type, threat_level, confidence, context
            )
            
            return threat_alert
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            return None
    
    def _determine_threat_level(self, anomaly_score: float, attack_type: AttackType) -> ThreatLevel:
        """Determine threat level based on anomaly score and attack type"""
        # High-impact attacks
        if attack_type in [AttackType.IMPACT, AttackType.EXFILTRATION, AttackType.CREDENTIAL_ACCESS]:
            if anomaly_score > 0.8:
                return ThreatLevel.CRITICAL
            elif anomaly_score > 0.6:
                return ThreatLevel.HIGH
            else:
                return ThreatLevel.MEDIUM
        
        # Medium-impact attacks
        elif attack_type in [AttackType.LATERAL_MOVEMENT, AttackType.PRIVILEGE_ESCALATION, AttackType.COMMAND_CONTROL]:
            if anomaly_score > 0.7:
                return ThreatLevel.HIGH
            elif anomaly_score > 0.5:
                return ThreatLevel.MEDIUM
            else:
                return ThreatLevel.LOW
        
        # Low-impact attacks (reconnaissance, discovery)
        else:
            if anomaly_score > 0.8:
                return ThreatLevel.MEDIUM
            else:
                return ThreatLevel.LOW
    
    async def _create_threat_alert(
        self,
        packet: NetworkPacket,
        anomaly_report: AnomalyReport,
        attack_type: AttackType,
        threat_level: ThreatLevel,
        confidence: float,
        context: Dict[str, Any] = None
    ) -> ThreatAlert:
        """Create comprehensive threat alert"""
        context = context or {}
        
        # Generate threat description
        threat_description = self._generate_threat_description(attack_type, anomaly_report, context)
        
        # Determine attack vector
        attack_vector = self._determine_attack_vector(packet, attack_type)
        
        # Get MITRE ATT&CK mapping
        mitre_id = self._get_mitre_attack_id(attack_type)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(attack_type, threat_level)
        
        # Identify affected assets
        affected_assets = [packet.destination_ip]
        if context.get('unique_destinations', 1) > 1:
            affected_assets.extend(context.get('destination_ips', [])[:5])  # Limit to 5
        
        return ThreatAlert(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            threat_level=threat_level,
            attack_type=attack_type,
            confidence_score=confidence,
            source_packets=[packet],
            anomaly_reports=[anomaly_report],
            threat_description=threat_description,
            attack_vector=attack_vector,
            mitre_attack_id=mitre_id,
            recommended_actions=recommendations,
            affected_assets=affected_assets,
            network_segment=context.get('network_segment'),
            detection_method="Two-Stage ML Pipeline",
            processing_time_ms=0.0,  # Will be calculated by caller
            false_positive_probability=1.0 - confidence
        )
    
    def _generate_threat_description(
        self, 
        attack_type: AttackType, 
        anomaly_report: AnomalyReport,
        context: Dict[str, Any]
    ) -> str:
        """Generate human-readable threat description"""
        descriptions = {
            AttackType.RECONNAISSANCE: f"Reconnaissance activity detected with anomaly score {anomaly_report.anomaly_score:.2f}",
            AttackType.DISCOVERY: f"Network discovery/scanning detected affecting {context.get('unique_destinations', 1)} targets",
            AttackType.CREDENTIAL_ACCESS: f"Potential brute-force or credential harvesting attack detected",
            AttackType.LATERAL_MOVEMENT: f"Lateral movement activity detected across network segments",
            AttackType.EXFILTRATION: f"Data exfiltration attempt detected with large payload transfer",
            AttackType.IMPACT: f"High-volume traffic suggesting DDoS or system impact attack",
            AttackType.COMMAND_CONTROL: f"Command and control communication detected",
            AttackType.PRIVILEGE_ESCALATION: f"Privilege escalation attempt detected",
        }
        return descriptions.get(attack_type, f"Suspicious {attack_type.value} activity detected")
    
    def _determine_attack_vector(self, packet: NetworkPacket, attack_type: AttackType) -> str:
        """Determine primary attack vector"""
        if packet.destination_port in [80, 443, 8080, 8443]:
            return "Web Application"
        elif packet.destination_port in [22, 3389]:
            return "Remote Access"
        elif packet.destination_port in [135, 139, 445]:
            return "File Sharing/SMB"
        elif packet.destination_port in [21, 23]:
            return "Legacy Protocols"
        elif packet.destination_port < 1024:
            return "System Services"
        else:
            return "Network Protocol"
    
    def _get_mitre_attack_id(self, attack_type: AttackType) -> Optional[str]:
        """Map attack type to MITRE ATT&CK technique ID"""
        mitre_mapping = {
            AttackType.RECONNAISSANCE: "TA0043",
            AttackType.DISCOVERY: "TA0007",
            AttackType.CREDENTIAL_ACCESS: "TA0006",
            AttackType.LATERAL_MOVEMENT: "TA0008",
            AttackType.EXFILTRATION: "TA0010",
            AttackType.IMPACT: "TA0040",
            AttackType.COMMAND_CONTROL: "TA0011",
            AttackType.PRIVILEGE_ESCALATION: "TA0004",
        }
        return mitre_mapping.get(attack_type)
    
    def _generate_recommendations(self, attack_type: AttackType, threat_level: ThreatLevel) -> List[str]:
        """Generate specific recommendations based on attack type and severity"""
        base_recommendations = [
            "Monitor affected systems for additional suspicious activity",
            "Review firewall and access control rules",
            "Update threat intelligence feeds"
        ]
        
        specific_recommendations = {
            AttackType.RECONNAISSANCE: [
                "Implement rate limiting on exposed services",
                "Review external attack surface"
            ],
            AttackType.DISCOVERY: [
                "Block source IP if confirmed malicious",
                "Implement network segmentation"
            ],
            AttackType.CREDENTIAL_ACCESS: [
                "Force password reset for affected accounts",
                "Enable multi-factor authentication",
                "Review authentication logs"
            ],
            AttackType.LATERAL_MOVEMENT: [
                "Isolate affected network segments",
                "Review privileged account access",
                "Audit system configurations"
            ],
            AttackType.EXFILTRATION: [
                "Block data transfer to external destinations",
                "Review data classification and protection",
                "Investigate potential data compromise"
            ],
            AttackType.IMPACT: [
                "Implement DDoS protection measures",
                "Scale infrastructure resources",
                "Activate incident response procedures"
            ]
        }
        
        recommendations = base_recommendations.copy()
        recommendations.extend(specific_recommendations.get(attack_type, []))
        
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            recommendations.insert(0, "Activate incident response team immediately")
            recommendations.append("Consider isolating affected systems")
        
        return recommendations


# Legacy compatibility - keeping old class names but pointing to new implementation
class AnomalyDetectionEngine(CatBoostAnomalyDetector):
    """Legacy compatibility wrapper"""
    def __init__(self):
        super().__init__()
        logger.warning("AnomalyDetectionEngine is deprecated, use CatBoostAnomalyDetector instead")


class ThreatAnalysisEngine:
    """
    Enhanced threat analysis engine that works with the two-stage detection system.
    Provides additional analysis and context for detected threats.
    """
    
    def __init__(self):
        self.detection_engine = TwoStageDetectionEngine()
        
    async def initialize(self):
        """Initialize the analysis engine"""
        await self.detection_engine.initialize()
        
    async def analyze_packets(
        self, 
        packets: List[NetworkPacket]
    ) -> List[ThreatAlert]:
        """
        Analyze a batch of packets for threats
        """
        threats = []
        
        # Calculate context for all packets
        context = self._calculate_batch_context(packets)
        
        # Process each packet through the two-stage pipeline
        for packet in packets:
            packet_context = self._get_packet_context(packet, packets, context)
            threat_alert = await self.detection_engine.process_packet(packet, packet_context)
            
            if threat_alert:
                threats.append(threat_alert)
        
        return threats
    
    def _calculate_batch_context(self, packets: List[NetworkPacket]) -> Dict[str, Any]:
        """Calculate context metrics for the entire batch"""
        if not packets:
            return {}
        
        # Time span calculation
        timestamps = [p.timestamp for p in packets]
        time_span = (max(timestamps) - min(timestamps)).total_seconds()
        
        # Traffic metrics
        total_bytes = sum(p.payload_size for p in packets)
        packet_rate = len(packets) / (time_span + 1)
        byte_rate = total_bytes / (time_span + 1)
        
        # Network metrics
        source_ips = list(set(p.source_ip for p in packets))
        dest_ips = list(set(p.destination_ip for p in packets))
        protocols = list(set(p.protocol for p in packets))
        
        return {
            'total_packets': len(packets),
            'time_span': time_span,
            'packet_rate': packet_rate,
            'byte_rate': byte_rate,
            'unique_sources': len(source_ips),
            'unique_destinations': len(dest_ips),
            'source_ips': source_ips,
            'destination_ips': dest_ips,
            'protocols': protocols,
            'total_bytes': total_bytes
        }
    
    def _get_packet_context(
        self, 
        packet: NetworkPacket, 
        all_packets: List[NetworkPacket],
        batch_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get specific context for individual packet"""
        # Find related packets (same source or destination)
        related_packets = [
            p for p in all_packets 
            if p.source_ip == packet.source_ip or p.destination_ip == packet.destination_ip
        ]
        
        context = batch_context.copy()
        context.update({
            'related_packet_count': len(related_packets),
            'packet_sequence_position': all_packets.index(packet) if packet in all_packets else 0,
        })
        
        return context


class ThreatDetectionService:
    """
    Main service class for the enhanced two-stage threat detection system
    """
    
    def __init__(self):
        self.analysis_engine = ThreatAnalysisEngine()
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the threat detection service"""
        try:
            await self.analysis_engine.initialize()
            self.is_initialized = True
            logger.info("Threat detection service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize threat detection service: {e}")
            raise
    
    async def detect_threats(self, packets: List[NetworkPacket]) -> List[ThreatAlert]:
        """
        Main entry point for threat detection
        Process packets through the two-stage detection pipeline
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            start_time = time.time()
            
            # Process packets through enhanced analysis
            threats = await self.analysis_engine.analyze_packets(packets)
            
            # Update processing time for each threat
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            for threat in threats:
                threat.processing_time_ms = processing_time / len(threats) if threats else processing_time
            
            logger.info(f"Processed {len(packets)} packets, detected {len(threats)} threats")
            return threats
            
        except Exception as e:
            logger.error(f"Error in threat detection: {e}")
            return []
    
    async def detect_single_threat(self, packet: NetworkPacket) -> Optional[ThreatAlert]:
        """Process a single packet for threat detection"""
        threats = await self.detect_threats([packet])
        return threats[0] if threats else None
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the detection system"""
        return {
            'service': 'threat_detection',
            'status': 'healthy' if self.is_initialized else 'initializing',
            'detection_pipeline': 'two_stage_ml',
            'stages': {
                'stage_1': 'autoencoder_anomaly_detection',
                'stage_2': 'attack_classification'
            },
            'models': {
                'autoencoder': 'loaded' if self.analysis_engine.detection_engine.anomaly_detector.model else 'fallback',
                'classifier': 'loaded' if self.analysis_engine.detection_engine.attack_classifier.model else 'fallback'
            }
        }
