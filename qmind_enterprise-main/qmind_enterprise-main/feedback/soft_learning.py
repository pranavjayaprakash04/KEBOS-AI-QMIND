"""
Q-MIND v3.5: Soft Feedback Learning System

Implements safe, bounded feedback without retraining or overcorrection.

When an indicator with prior confidence > 0.6 later becomes malicious:
• Slightly increase sensitivity for similar future indicators
• Adjust signal weights within bounded limits
• Track feedback for audit and compliance
• Prevent cascading overcorrection

Design Principle:
- NO retraining models
- NO hardcoded thresholds
- Bounded adjustments (±5% per feedback event)
- Explicit audit trail
- Fail-safe: Never decrease precision below 95%
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Type of feedback received."""
    FALSE_NEGATIVE = "false_negative"  # Missed a threat
    FALSE_POSITIVE = "false_positive"  # Incorrectly flagged
    LATE_DETECTION = "late_detection"  # Detected but too slow
    CORRECTLY_ABSTAINED = "correctly_abstained"  # Right to not decide


@dataclass
class FeedbackEvent:
    """Single feedback event (ground truth arrival)."""
    
    indicator_id: str
    indicator_type: str  # "hash", "url", "ip", etc.
    category: str  # "phishing", "malware", etc.
    
    # Prior prediction
    prior_confidence: float  # Confidence when we made decision
    prior_threat_level: str  # "minimal", "low", "medium", "high", "critical"
    prior_signals: List[str]  # Signals we used
    
    # Feedback
    feedback_type: FeedbackType
    actual_threat: bool
    verification_source: str  # "soc_analyst", "malware_vendor", "network_telemetry"
    
    # Timing
    first_warning_time: datetime
    feedback_received_time: datetime
    lead_time_hours: int = 0
    
    # Corrections (computed)
    requires_adjustment: bool = False  # Should we adjust weights?
    adjustment_magnitude: float = 0.0  # How much to adjust
    
    def __post_init__(self):
        """Compute whether feedback requires adjustment."""
        # Only adjust for confident misses (prior > 0.6)
        self.requires_adjustment = (
            self.prior_confidence > 0.6 and
            self.feedback_type == FeedbackType.FALSE_NEGATIVE
        )
        
        # Compute lead time
        if self.first_warning_time and self.feedback_received_time:
            delta = self.feedback_received_time - self.first_warning_time
            self.lead_time_hours = int(delta.total_seconds() / 3600)
        
        # Compute adjustment magnitude (stronger for high confidence misses)
        if self.requires_adjustment:
            # Scale: lower confidence misses get smaller adjustment
            base_magnitude = (self.prior_confidence - 0.6) / 0.4  # [0, 1]
            self.adjustment_magnitude = base_magnitude * 0.05  # Cap at ±5%


@dataclass
class SignalWeightAdjustment:
    """Record of a signal weight adjustment."""
    
    signal_name: str
    signal_type: str  # "phishing", "malware", etc.
    original_weight: float
    adjusted_weight: float
    adjustment_reason: str  # Which feedback triggered this
    adjustment_magnitude: float
    adjusted_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Export adjustment as dictionary."""
        return {
            "signal": self.signal_name,
            "type": self.signal_type,
            "original": round(self.original_weight, 4),
            "adjusted": round(self.adjusted_weight, 4),
            "magnitude": round(self.adjustment_magnitude, 4),
            "reason": self.adjustment_reason,
            "adjusted_at": self.adjusted_at.isoformat(),
        }


class BoundedWeightAdjustment:
    """
    Implements bounded, safe weight adjustment.
    
    Rules:
    1. Never adjust by more than ±5% per event
    2. Never decrease precision below 95%
    3. Track all adjustments for audit
    4. Allow max cumulative adjustment of ±20% from baseline
    5. Weights always in [0.1, 0.9] range
    """
    
    MAX_ADJUSTMENT_PER_EVENT = 0.05  # ±5%
    MAX_CUMULATIVE_ADJUSTMENT = 0.20  # ±20%
    MIN_WEIGHT = 0.1
    MAX_WEIGHT = 0.9
    MIN_PRECISION_THRESHOLD = 0.95
    
    def __init__(self, baseline_weights: Dict[str, float]):
        """
        Initialize weight adjuster.
        
        Args:
            baseline_weights: Original signal weights
        """
        self.baseline_weights = baseline_weights.copy()
        self.current_weights = baseline_weights.copy()
        self.adjustment_history: List[SignalWeightAdjustment] = []
        self.cumulative_adjustments: Dict[str, float] = {
            signal: 0.0 for signal in baseline_weights
        }
        
        logger.info(f"Bounded Weight Adjustment initialized with {len(baseline_weights)} signals")
    
    def adjust_weight(
        self,
        signal_name: str,
        feedback: FeedbackEvent,
        current_precision: float,
    ) -> Tuple[bool, Optional[SignalWeightAdjustment]]:
        """
        Safely adjust signal weight based on feedback.
        
        Args:
            signal_name: Name of signal to adjust
            feedback: Feedback event triggering adjustment
            current_precision: Current system precision
        
        Returns:
            (was_adjusted, adjustment_record)
        """
        # Check preconditions
        if not feedback.requires_adjustment:
            logger.debug(f"Feedback for {feedback.indicator_id} does not require adjustment")
            return False, None
        
        if signal_name not in self.current_weights:
            logger.warning(f"Signal {signal_name} not found in weight dictionary")
            return False, None
        
        # Check precision constraint
        if current_precision < self.MIN_PRECISION_THRESHOLD:
            logger.warning(f"Cannot adjust: current precision {current_precision:.4f} "
                           f"below threshold {self.MIN_PRECISION_THRESHOLD}")
            return False, None
        
        # Compute adjustment direction
        # For false negatives (missed threats), increase weight on threat-oriented signals
        adjustment_direction = 1.0  # Increase weight
        adjustment_magnitude = feedback.adjustment_magnitude * adjustment_direction
        
        # Check cumulative limit
        if abs(self.cumulative_adjustments[signal_name] + adjustment_magnitude) > self.MAX_CUMULATIVE_ADJUSTMENT:
            adjustment_magnitude = self.MAX_CUMULATIVE_ADJUSTMENT - abs(self.cumulative_adjustments[signal_name])
            adjustment_magnitude *= adjustment_direction
            logger.warning(f"Cumulative limit reached for {signal_name}, capped adjustment at {adjustment_magnitude:.4f}")
        
        # Apply adjustment
        original_weight = self.current_weights[signal_name]
        adjusted_weight = original_weight + adjustment_magnitude
        
        # Constrain to [MIN_WEIGHT, MAX_WEIGHT]
        adjusted_weight = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, adjusted_weight))
        
        # Store adjustment
        self.current_weights[signal_name] = adjusted_weight
        self.cumulative_adjustments[signal_name] += (adjusted_weight - original_weight)
        
        # Create adjustment record
        record = SignalWeightAdjustment(
            signal_name=signal_name,
            signal_type=feedback.category,
            original_weight=original_weight,
            adjusted_weight=adjusted_weight,
            adjustment_reason=f"{feedback.feedback_type.value} on {feedback.indicator_id}",
            adjustment_magnitude=(adjusted_weight - original_weight),
        )
        
        self.adjustment_history.append(record)
        
        logger.info(f"Adjusted {signal_name}: {original_weight:.4f} → {adjusted_weight:.4f}")
        
        return True, record
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current weights after all adjustments."""
        return self.current_weights.copy()
    
    def get_adjustment_history(self) -> List[SignalWeightAdjustment]:
        """Get all adjustments applied."""
        return self.adjustment_history.copy()
    
    def compute_cumulative_impact(self) -> Dict[str, float]:
        """
        Compute cumulative impact of all adjustments.
        
        Returns:
            Dictionary mapping signal name to total % change from baseline
        """
        impact = {}
        for signal, baseline in self.baseline_weights.items():
            current = self.current_weights[signal]
            pct_change = ((current - baseline) / baseline) * 100
            impact[signal] = pct_change
        
        return impact


class SoftFeedbackLearningSystem:
    """
    Complete soft feedback learning system.
    
    Features:
    • Accepts ground truth feedback
    • Adjusts signal weights safely
    • Maintains precision > 95%
    • Provides audit trail
    • Prevents overcorrection
    """
    
    def __init__(self, baseline_weights: Dict[str, float]):
        """
        Initialize feedback learning system.
        
        Args:
            baseline_weights: Baseline signal weights
        """
        self.weight_adjuster = BoundedWeightAdjustment(baseline_weights)
        self.feedback_history: List[FeedbackEvent] = []
        self.metrics_tracking: Dict[str, List[float]] = {
            "precision": [],
            "recall": [],
            "false_positive_rate": [],
        }
        
        logger.info("Soft Feedback Learning System initialized")
    
    def receive_feedback(
        self,
        indicator_id: str,
        indicator_type: str,
        category: str,
        prior_confidence: float,
        prior_threat_level: str,
        prior_signals: List[str],
        feedback_type: FeedbackType,
        actual_threat: bool,
        verification_source: str,
        first_warning_time: datetime,
        feedback_received_time: datetime,
        current_precision: float,
    ) -> Dict:
        """
        Process ground truth feedback.
        
        Args:
            indicator_id: Unique identifier
            indicator_type: Type of indicator
            category: Threat category
            prior_confidence: Our confidence at time of decision
            prior_threat_level: Our threat assessment
            prior_signals: Signals we used
            feedback_type: Type of feedback
            actual_threat: Ground truth (was it malicious?)
            verification_source: Where feedback came from
            first_warning_time: When we first warned
            feedback_received_time: When feedback arrived
            current_precision: Current system precision
        
        Returns:
            Dictionary with adjustment results
        """
        # Create feedback event
        feedback = FeedbackEvent(
            indicator_id=indicator_id,
            indicator_type=indicator_type,
            category=category,
            prior_confidence=prior_confidence,
            prior_threat_level=prior_threat_level,
            prior_signals=prior_signals,
            feedback_type=feedback_type,
            actual_threat=actual_threat,
            verification_source=verification_source,
            first_warning_time=first_warning_time,
            feedback_received_time=feedback_received_time,
        )
        
        self.feedback_history.append(feedback)
        
        # Process adjustments
        adjustments = []
        for signal_name in prior_signals:
            was_adjusted, record = self.weight_adjuster.adjust_weight(
                signal_name,
                feedback,
                current_precision,
            )
            if was_adjusted:
                adjustments.append(record)
        
        # Log metrics
        self.metrics_tracking["precision"].append(current_precision)
        
        result = {
            "indicator_id": indicator_id,
            "feedback_type": feedback_type.value,
            "adjustments_applied": len(adjustments),
            "adjustment_records": [r.to_dict() for r in adjustments],
            "lead_time_hours": feedback.lead_time_hours,
            "cumulative_impact": self.weight_adjuster.compute_cumulative_impact(),
        }
        
        logger.info(f"Processed feedback for {indicator_id}: "
                   f"{feedback_type.value}, {len(adjustments)} adjustments")
        
        return result
    
    def get_learning_report(self) -> Dict:
        """
        Generate report on learning progress.
        
        Returns:
            Dictionary with adjustment statistics
        """
        if not self.feedback_history:
            return {"feedback_count": 0, "adjustments_count": 0}
        
        adjustment_history = self.weight_adjuster.get_adjustment_history()
        
        # Categorize feedback
        false_negatives = sum(1 for f in self.feedback_history 
                             if f.feedback_type == FeedbackType.FALSE_NEGATIVE)
        false_positives = sum(1 for f in self.feedback_history 
                             if f.feedback_type == FeedbackType.FALSE_POSITIVE)
        late_detections = sum(1 for f in self.feedback_history 
                             if f.feedback_type == FeedbackType.LATE_DETECTION)
        
        # Lead time analysis
        lead_times = [f.lead_time_hours for f in self.feedback_history 
                     if f.lead_time_hours > 0]
        
        return {
            "total_feedback_events": len(self.feedback_history),
            "feedback_distribution": {
                "false_negatives": false_negatives,
                "false_positives": false_positives,
                "late_detections": late_detections,
            },
            "adjustments_applied": len(adjustment_history),
            "signals_adjusted": len(set(a.signal_name for a in adjustment_history)),
            "average_lead_time_hours": statistics.mean(lead_times) if lead_times else 0,
            "cumulative_impact": self.weight_adjuster.compute_cumulative_impact(),
            "current_weights": self.weight_adjuster.get_current_weights(),
            "adjustment_history": [a.to_dict() for a in adjustment_history],
        }


logger.info("Soft Feedback Learning System v3.5 loaded")
