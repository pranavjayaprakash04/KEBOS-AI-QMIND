"""
Threat Detection Engine Module

Enhanced threat detection with CatBoost-based anomaly detection
and attack classification for network traffic analysis.
"""

from threat_detection.api import router
from threat_detection.models import ThreatAlert, NetworkPacket, AnomalyReport
# from threat_detection.services import ThreatDetectionService, TwoStageDetectionEngine, AutoencoderAnomalyDetector, AttackClassifier
from threat_detection.catboost_detector import CatBoostThreatDetector
from threat_detection.tasks import process_network_stream, analyze_threat_patterns

__all__ = [
    "router",
    "ThreatAlert",
    "NetworkPacket", 
    "AnomalyReport",
    "CatBoostThreatDetector",
    # "ThreatDetectionService",
    # "TwoStageDetectionEngine",
    # "AutoencoderAnomalyDetector",
    "AttackClassifier", 
    "process_network_stream",
    "analyze_threat_patterns"
]
