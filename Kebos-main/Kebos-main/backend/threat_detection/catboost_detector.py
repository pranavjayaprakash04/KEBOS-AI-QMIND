"""
CatBoost-based Threat Detection Service

This module provides threat detection using the trained CatBoost models
from the CICIDS 2017 dataset analysis.
"""

import json
import numpy as np
import pandas as pd
import joblib
import catboost as cb
import os
from sklearn.preprocessing import LabelEncoder, StandardScaler
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import logging
from pathlib import Path

from threat_detection.models import (
    NetworkPacket, 
    AnomalyReport, 
    ThreatAlert, 
    ThreatLevel, 
    AttackType
)

logger = logging.getLogger(__name__)


class CatBoostThreatDetector:
    """
    CatBoost-based threat detection system
    
    This class implements a two-step threat detection pipeline:
    1. Binary classification: Benign vs Attack
    2. Multiclass classification: Attack type identification
    """
    
    def __init__(self, model_base_path: Optional[str] = None):
        """Initialize the CatBoost threat detector"""
        # Use environment variable or provided path, fallback to relative path from backend dir
        if model_base_path:
            self.model_base_path = Path(model_base_path)
        else:
            # Try environment variable first
            env_path = os.getenv('CATBOOST_MODEL_PATH')
            if env_path:
                self.model_base_path = Path(env_path)
            else:
                # Default to models directory relative to backend
                self.model_base_path = Path(__file__).parent.parent / "models"
        
        # Models and preprocessors
        self.binary_model = None
        self.multiclass_model = None
        self.scaler = None
        self.label_encoder = None
        self.metadata = None
        
        # Attack type mapping from CICIDS to MITRE ATT&CK
        self.attack_type_mapping = {
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
        
        # Feature names (must match the training data exactly - 88 features)
        self.feature_names = [
            "Source Port", "Destination Port", "Protocol", "Flow Duration", "Total Fwd Packets",
            "Total Backward Packets", "Total Length of Fwd Packets", "Total Length of Bwd Packets",
            "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
            "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean", "Bwd Packet Length Std",
            "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
            "Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Total",
            "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Fwd PSH Flags", "Bwd PSH Flags",
            "Fwd URG Flags", "Bwd URG Flags", "Fwd Header Length", "Bwd Header Length", "Fwd Packets/s",
            "Bwd Packets/s", "Min Packet Length", "Max Packet Length", "Packet Length Mean", "Packet Length Std",
            "Packet Length Variance", "FIN Flag Count", "SYN Flag Count", "RST Flag Count", "PSH Flag Count",
            "ACK Flag Count", "URG Flag Count", "CWE Flag Count", "ECE Flag Count", "Down/Up Ratio",
            "Average Packet Size", "Avg Fwd Segment Size", "Avg Bwd Segment Size", "Fwd Header Length.1",
            "Fwd Avg Bytes/Bulk", "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate", "Bwd Avg Bytes/Bulk",
            "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate", "Subflow Fwd Packets", "Subflow Fwd Bytes",
            "Subflow Bwd Packets", "Subflow Bwd Bytes", "Init_Win_bytes_forward", "Init_Win_bytes_backward",
            "act_data_pkt_fwd", "min_seg_size_forward", "Active Mean", "Active Std", "Active Max", "Active Min",
            "Idle Mean", "Idle Std", "Idle Max", "Idle Min", "features_mean", "features_std", "features_max",
            "features_min", "Source Port_log", "Destination Port_log", "Protocol_log", "Total Fwd Packets_log"
        ]
        
    async def initialize(self):
        """Initialize all models and preprocessors"""
        try:
            logger.info(f"Initializing CatBoost threat detector from {self.model_base_path}")
            
            # Load binary classifier
            binary_model_path = self.model_base_path / "binary_classifier_basic.cbm"
            if binary_model_path.exists():
                self.binary_model = cb.CatBoostClassifier()
                self.binary_model.load_model(str(binary_model_path))
                logger.info("Binary classifier loaded successfully")
            else:
                logger.error(f"Binary model not found: {binary_model_path}")
                
            # Load multiclass classifier
            multiclass_model_path = self.model_base_path / "multiclass_classifier_basic.cbm"
            if multiclass_model_path.exists():
                self.multiclass_model = cb.CatBoostClassifier()
                self.multiclass_model.load_model(str(multiclass_model_path))
                logger.info("Multiclass classifier loaded successfully")
            else:
                logger.error(f"Multiclass model not found: {multiclass_model_path}")
                
            # Load scaler
            scaler_path = self.model_base_path / "scaler_basic.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                logger.info("Feature scaler loaded successfully")
            else:
                logger.error(f"Scaler not found: {scaler_path}")
                
            # Load label encoder
            label_encoder_path = self.model_base_path / "label_encoder_basic.pkl"
            if label_encoder_path.exists():
                self.label_encoder = joblib.load(label_encoder_path)
                logger.info("Label encoder loaded successfully")
            else:
                logger.error(f"Label encoder not found: {label_encoder_path}")
                
            # Load metadata
            metadata_path = self.model_base_path / "model_metadata_basic.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                logger.info("Model metadata loaded successfully")
            else:
                logger.warning(f"Metadata not found: {metadata_path}")
                
            # Verify models are loaded
            if not any([self.binary_model, self.multiclass_model]):
                raise Exception("No models were successfully loaded")
                
            logger.info("CatBoost threat detector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CatBoost threat detector: {e}")
            raise
    
    def extract_features(self, packet: NetworkPacket, context: Dict[str, Any] = None) -> np.ndarray:
        """
        Extract features from NetworkPacket to match CICIDS format exactly
        
        Note: This creates a simplified feature vector from a single packet.
        In production, you would need flow-based feature calculation.
        """
        context = context or {}
        
        # Initialize feature vector with 88 features
        features = np.zeros(88)
        
        try:
            # Basic packet features [0-2]
            features[0] = float(packet.source_port)          # Source Port
            features[1] = float(packet.destination_port)     # Destination Port  
            features[2] = float(hash(packet.protocol) % 1000) # Protocol (encoded)
            
            # Flow features [3-7] 
            features[3] = 1000.0                             # Flow Duration (estimated)
            features[4] = 1.0                                # Total Fwd Packets
            features[5] = 0.0                                # Total Backward Packets
            features[6] = float(packet.payload_size)         # Total Length of Fwd Packets
            features[7] = 0.0                                # Total Length of Bwd Packets
            
            # Forward packet length stats [8-11]
            features[8] = float(packet.payload_size)         # Fwd Packet Length Max
            features[9] = float(packet.payload_size)         # Fwd Packet Length Min
            features[10] = float(packet.payload_size)        # Fwd Packet Length Mean
            features[11] = 0.0                               # Fwd Packet Length Std
            
            # Backward packet length stats [12-15] (zeros for single packet)
            features[12] = 0.0                               # Bwd Packet Length Max
            features[13] = 0.0                               # Bwd Packet Length Min
            features[14] = 0.0                               # Bwd Packet Length Mean
            features[15] = 0.0                               # Bwd Packet Length Std
            
            # Flow rate features [16-17]
            features[16] = float(packet.payload_size) / 1.0  # Flow Bytes/s
            features[17] = 1.0                               # Flow Packets/s
            
            # Inter-arrival time features [18-31] (estimated)
            features[18] = 1000.0                            # Flow IAT Mean
            features[19] = 100.0                             # Flow IAT Std
            features[20] = 2000.0                            # Flow IAT Max
            features[21] = 500.0                             # Flow IAT Min
            features[22] = 1000.0                            # Fwd IAT Total
            features[23] = 1000.0                            # Fwd IAT Mean
            features[24] = 0.0                               # Fwd IAT Std
            features[25] = 1000.0                            # Fwd IAT Max
            features[26] = 1000.0                            # Fwd IAT Min
            features[27] = 0.0                               # Bwd IAT Total
            features[28] = 0.0                               # Bwd IAT Mean
            features[29] = 0.0                               # Bwd IAT Std
            features[30] = 0.0                               # Bwd IAT Max
            features[31] = 0.0                               # Bwd IAT Min
            
            # Flag features [32-35]
            features[32] = 0.0                               # Fwd PSH Flags
            features[33] = 0.0                               # Bwd PSH Flags
            features[34] = 0.0                               # Fwd URG Flags
            features[35] = 0.0                               # Bwd URG Flags
            
            # Header length features [36-37]
            features[36] = 20.0                              # Fwd Header Length
            features[37] = 20.0                              # Bwd Header Length
            
            # Packet rate features [38-39]
            features[38] = 1.0                               # Fwd Packets/s
            features[39] = 0.0                               # Bwd Packets/s
            
            # Packet length statistics [40-44]
            features[40] = float(packet.payload_size)        # Min Packet Length
            features[41] = float(packet.payload_size)        # Max Packet Length
            features[42] = float(packet.payload_size)        # Packet Length Mean
            features[43] = 0.0                               # Packet Length Std
            features[44] = 0.0                               # Packet Length Variance
            
            # TCP flag counts [45-52]
            if packet.protocol.upper() == 'TCP':
                features[45] = 0.0                           # FIN Flag Count
                features[46] = 1.0                           # SYN Flag Count
                features[47] = 0.0                           # RST Flag Count
                features[48] = 0.0                           # PSH Flag Count
                features[49] = 1.0                           # ACK Flag Count
                features[50] = 0.0                           # URG Flag Count
                features[51] = 0.0                           # CWE Flag Count
                features[52] = 0.0                           # ECE Flag Count
            
            # Additional features [53-55]
            features[53] = 0.0                               # Down/Up Ratio
            features[54] = float(packet.payload_size)        # Average Packet Size
            features[55] = float(packet.payload_size)        # Avg Fwd Segment Size
            features[56] = 0.0                               # Avg Bwd Segment Size
            
            # Header and bulk features [57-63]
            features[57] = 20.0                              # Fwd Header Length.1
            features[58] = 0.0                               # Fwd Avg Bytes/Bulk
            features[59] = 0.0                               # Fwd Avg Packets/Bulk
            features[60] = 0.0                               # Fwd Avg Bulk Rate
            features[61] = 0.0                               # Bwd Avg Bytes/Bulk
            features[62] = 0.0                               # Bwd Avg Packets/Bulk
            features[63] = 0.0                               # Bwd Avg Bulk Rate
            
            # Subflow features [64-67]
            features[64] = 1.0                               # Subflow Fwd Packets
            features[65] = float(packet.payload_size)        # Subflow Fwd Bytes
            features[66] = 0.0                               # Subflow Bwd Packets
            features[67] = 0.0                               # Subflow Bwd Bytes
            
            # Window and activity features [68-79]
            features[68] = 65535.0                           # Init_Win_bytes_forward
            features[69] = 65535.0                           # Init_Win_bytes_backward
            features[70] = 1.0                               # act_data_pkt_fwd
            features[71] = 20.0                              # min_seg_size_forward
            features[72] = 0.0                               # Active Mean
            features[73] = 0.0                               # Active Std
            features[74] = 0.0                               # Active Max
            features[75] = 0.0                               # Active Min
            features[76] = 0.0                               # Idle Mean
            features[77] = 0.0                               # Idle Std
            features[78] = 0.0                               # Idle Max
            features[79] = 0.0                               # Idle Min
            
            # Statistical features [80-83] - calculated from the base features
            non_zero_features = features[features != 0]
            if len(non_zero_features) > 0:
                features[80] = np.mean(non_zero_features)    # features_mean
                features[81] = np.std(non_zero_features)     # features_std
                features[82] = np.max(non_zero_features)     # features_max
                features[83] = np.min(non_zero_features)     # features_min
            
            # Log transform features [84-87]
            features[84] = np.log1p(features[0])             # Source Port_log
            features[85] = np.log1p(features[1])             # Destination Port_log
            features[86] = np.log1p(features[2])             # Protocol_log
            features[87] = np.log1p(features[4])             # Total Fwd Packets_log
            
            # Apply context-based adjustments if available
            if 'packet_rate' in context:
                features[17] = context['packet_rate']        # Flow Packets/s
                features[38] = context['packet_rate']        # Fwd Packets/s
            
            if 'byte_rate' in context:
                features[16] = context['byte_rate']          # Flow Bytes/s
                
        except Exception as e:
            logger.warning(f"Error extracting features: {e}")
            
        return features
    
    async def detect_threat(
        self, 
        packet: NetworkPacket, 
        context: Dict[str, Any] = None
    ) -> Optional[ThreatAlert]:
        """
        Main threat detection method
        
        Returns ThreatAlert if a threat is detected, None otherwise
        """
        try:
            # Extract features
            features = self.extract_features(packet, context)
            
            # Step 1: Binary classification (Benign vs Attack)
            is_attack, attack_confidence = await self._binary_classification(features)
            
            if not is_attack:
                return None  # No threat detected
            
            # Step 2: Attack type classification
            attack_type_name, type_confidence = await self._attack_classification(features)
            
            # Map to MITRE ATT&CK framework
            attack_type = self.attack_type_mapping.get(attack_type_name, AttackType.DISCOVERY)
            
            # Determine threat level
            threat_level = self._determine_threat_level(attack_confidence, attack_type)
            
            # Create threat alert
            threat_alert = ThreatAlert(
                id=str(uuid4()),
                timestamp=datetime.utcnow(),
                threat_level=threat_level,
                attack_type=attack_type,
                confidence_score=min(attack_confidence, type_confidence),
                source_packets=[packet],
                anomaly_reports=[],
                threat_description=f"CatBoost detected {attack_type_name} attack with {attack_confidence:.2%} confidence",
                attack_vector=f"Network traffic to port {packet.destination_port}",
                mitre_attack_id=self._get_mitre_id(attack_type),
                recommended_actions=self._get_recommendations(attack_type),
                affected_assets=[packet.destination_ip],
                detection_method="CatBoost Two-Step Classification",
                processing_time_ms=0.0,
                false_positive_probability=1.0 - min(attack_confidence, type_confidence)
            )
            
            return threat_alert
            
        except Exception as e:
            logger.error(f"Error in threat detection: {e}")
            return None
    
    async def _binary_classification(self, features: np.ndarray) -> Tuple[bool, float]:
        """Binary classification: Benign (0) vs Attack (1)"""
        try:
            if self.binary_model is None:
                return False, 0.0
                
            # Preprocess features
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
                
            # Preprocess features
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
                mean_val = np.mean(features_2d)
                std_val = np.std(features_2d)
                features_scaled = (features_2d - mean_val) / (std_val + 1e-8)
            
            return features_scaled
            
        except Exception as e:
            logger.error(f"Error preprocessing features: {e}")
            return features.reshape(1, -1)
    
    def _determine_threat_level(self, confidence: float, attack_type: AttackType) -> ThreatLevel:
        """Determine threat level based on confidence and attack type"""
        # High-impact attacks
        if attack_type in [AttackType.IMPACT, AttackType.EXFILTRATION, AttackType.CREDENTIAL_ACCESS]:
            if confidence > 0.8:
                return ThreatLevel.CRITICAL
            elif confidence > 0.6:
                return ThreatLevel.HIGH
            else:
                return ThreatLevel.MEDIUM
        
        # Medium-impact attacks
        elif attack_type in [AttackType.LATERAL_MOVEMENT, AttackType.PRIVILEGE_ESCALATION, AttackType.COMMAND_CONTROL]:
            if confidence > 0.7:
                return ThreatLevel.HIGH
            elif confidence > 0.5:
                return ThreatLevel.MEDIUM
            else:
                return ThreatLevel.LOW
        
        # Low-impact attacks (reconnaissance, discovery)
        else:
            if confidence > 0.8:
                return ThreatLevel.MEDIUM
            else:
                return ThreatLevel.LOW
    
    def _get_mitre_id(self, attack_type: AttackType) -> str:
        """Get MITRE ATT&CK technique ID"""
        mitre_mapping = {
            AttackType.RECONNAISSANCE: "T1595",
            AttackType.DISCOVERY: "T1046", 
            AttackType.INITIAL_ACCESS: "T1190",
            AttackType.CREDENTIAL_ACCESS: "T1110",
            AttackType.LATERAL_MOVEMENT: "T1021",
            AttackType.COMMAND_CONTROL: "T1071",
            AttackType.EXFILTRATION: "T1041",
            AttackType.IMPACT: "T1498"
        }
        return mitre_mapping.get(attack_type, "T1001")
    
    def _get_recommendations(self, attack_type: AttackType) -> List[str]:
        """Get recommended actions based on attack type"""
        recommendations = {
            AttackType.DISCOVERY: [
                "Monitor for additional scanning activities",
                "Review firewall rules for the source IP",
                "Check system logs for successful connections"
            ],
            AttackType.CREDENTIAL_ACCESS: [
                "Immediately check for successful logins from source IP",
                "Consider blocking source IP if confirmed malicious",
                "Review and strengthen authentication mechanisms",
                "Monitor for account compromise indicators"
            ],
            AttackType.IMPACT: [
                "Implement rate limiting for affected services",
                "Consider DDoS mitigation strategies",
                "Monitor system resources and performance",
                "Prepare incident response procedures"
            ],
            AttackType.COMMAND_CONTROL: [
                "Block communication to/from source IP",
                "Investigate for signs of system compromise",
                "Check for malware or unauthorized software",
                "Review network traffic for C2 indicators"
            ]
        }
        
        return recommendations.get(attack_type, [
            "Monitor the affected system closely",
            "Review security logs for additional indicators",
            "Consider implementing additional security controls"
        ])
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the CatBoost detector"""
        return {
            'service': 'catboost_threat_detector',
            'status': 'healthy' if self.binary_model and self.multiclass_model else 'degraded',
            'models': {
                'binary_classifier': 'loaded' if self.binary_model else 'not_loaded',
                'multiclass_classifier': 'loaded' if self.multiclass_model else 'not_loaded',
                'scaler': 'loaded' if self.scaler else 'not_loaded',
                'label_encoder': 'loaded' if self.label_encoder else 'not_loaded'
            },
            'feature_count': len(self.feature_names),
            'attack_types_supported': len(self.attack_type_mapping),
            'metadata': self.metadata
        }


# Global instance for use across the application
catboost_detector = CatBoostThreatDetector()
