from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import math


class ThreatCategory(Enum):
    """10-category threat classification"""
    C2_INFRASTRUCTURE = "C2_Infrastructure"
    BOTNET_IP = "Botnet_IP"
    PHISHING = "Phishing"
    MALWARE = "Malware"
    CREDENTIAL_LEAK = "Credential_Leak"
    DDoS = "DDoS"
    INSIDER_THREAT = "Insider_Threat"
    SUPPLY_CHAIN = "Supply_Chain"
    CVE_EXPLOITATION = "CVE_Exploitation"
    BENIGN = "Benign"


@dataclass
class SignalResult:
    """Probabilistic signal result from QMind"""
    threat_id: str
    category: ThreatCategory
    confidence: float  # 0.0 to 1.0
    supplier_trust: float  # 0.0 to 1.0
    decayed_confidence: float  # 0.0 to 1.0
    feed_source: str
    timestamp: float
    adversarial_stability: float  # 0.0 to 1.0


class SignalScorer:
    """
    10-category probabilistic signal engine with adversarial stability scoring.
    """
    
    # India-calibrated decay rates (λ) based on 90+ day median dwell time
    DECAY_RATES = {
        ThreatCategory.C2_INFRASTRUCTURE: 1/90,  # 90-day calibration
        ThreatCategory.SUPPLY_CHAIN: 1/90,
        ThreatCategory.INSIDER_THREAT: 1/90,
        ThreatCategory.BOTNET_IP: 1/45,
        ThreatCategory.PHISHING: 1/30,
        ThreatCategory.MALWARE: 1/30,
        ThreatCategory.CREDENTIAL_LEAK: 1/30,
        ThreatCategory.DDoS: 1/7,
        ThreatCategory.CVE_EXPLOITATION: 1/14,
        ThreatCategory.BENIGN: 1/1,
    }
    
    def __init__(self):
        pass
    
    def calculate_decay(
        self,
        category: ThreatCategory,
        hours_elapsed: float
    ) -> float:
        """
        Calculate signal decay using exponential decay: e^(-λt)
        India-calibrated λ values for longer dwell times
        """
        lambda_decay = self.DECAY_RATES.get(category, 1/30)
        decay_factor = math.exp(-lambda_decay * hours_elapsed)
        return decay_factor
    
    def calculate_adversarial_stability(
        self,
        confidence: float,
        supplier_trust: float,
        feed_count: int
    ) -> float:
        """
        Calculate adversarial stability score.
        Higher score = more stable against adversarial manipulation.
        """
        # Base stability from supplier trust
        stability = supplier_trust * 0.5
        
        # Boost from multi-feed corroboration
        if feed_count >= 3:
            stability += 0.3
        elif feed_count >= 2:
            stability += 0.1
        
        # Confidence contribution
        stability += confidence * 0.2
        
        return min(stability, 1.0)
    
    def score_signal(
        self,
        threat_id: str,
        category: ThreatCategory,
        raw_confidence: float,
        supplier_trust: float,
        feed_source: str,
        hours_since_detection: float = 0.0,
        feed_count: int = 1
    ) -> SignalResult:
        """
        Score a threat signal with decay and adversarial stability.
        High-confidence inputs (≥0.85) are preserved from decay reduction.
        """
        # Apply time decay, but preserve high-confidence inputs
        decay_factor = self.calculate_decay(category, hours_since_detection)
        decayed_confidence = raw_confidence * decay_factor
        
        # Preserve high-confidence inputs from decay reduction
        # If raw confidence is ≥0.85, ensure final confidence doesn't drop below 0.85
        if raw_confidence >= 0.85 and decayed_confidence < 0.85:
            decayed_confidence = 0.85
        
        # Calculate adversarial stability
        adversarial_stability = self.calculate_adversarial_stability(
            raw_confidence,
            supplier_trust,
            feed_count
        )
        
        import time
        return SignalResult(
            threat_id=threat_id,
            category=category,
            confidence=raw_confidence,
            supplier_trust=supplier_trust,
            decayed_confidence=decayed_confidence,
            feed_source=feed_source,
            timestamp=time.time(),
            adversarial_stability=adversarial_stability
        )
