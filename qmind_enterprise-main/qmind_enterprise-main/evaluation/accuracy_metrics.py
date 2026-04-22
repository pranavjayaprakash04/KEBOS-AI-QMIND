"""
Q-MIND Enterprise: Accuracy Evaluation Framework

Multi-category accuracy metrics with ground truth alignment.

Metrics tracked:
- Precision: Of all alerts we raised, how many were true positives?
- Recall: Of all true threats, how many did we detect?
- F1-Score: Harmonic mean balancing precision and recall
- False Positive Rate: Type I error rate
- False Negative Rate: Type II error rate
- Lead Time: How much advance warning before threat materialization
- Abstention Rate: How often do we say "I don't know"?

Benchmarks per threat category to ensure balanced performance.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime, timedelta
import logging
import math

from core.threat_state import ThreatCategory, ThreatState, IndicatorSignature

logger = logging.getLogger(__name__)


class GroundTruth(str, Enum):
    """Ground truth label for an indicator."""
    MALICIOUS = "malicious"
    SUSPICIOUS = "suspicious"
    BENIGN = "benign"
    UNKNOWN = "unknown"


@dataclass
class AnalysisRecord:
    """Single threat analysis with ground truth outcome."""
    
    indicator: IndicatorSignature
    threat_state: ThreatState
    
    # What we predicted
    predicted_threat_level: str  # critical, high, medium, low, minimal
    predicted_confidence: float  # [0, 1]
    predicted_at: datetime = field(default_factory=datetime.utcnow)
    
    # What actually happened (ground truth)
    ground_truth: GroundTruth = GroundTruth.UNKNOWN
    ground_truth_at: Optional[datetime] = None  # When did we learn the truth?
    ground_truth_delay_hours: int = 0  # T+24h, T+48h, etc.
    
    # Lead time calculation
    prediction_lead_time_hours: int = 0
    
    def is_true_positive(self) -> bool:
        """Was our prediction correct and threatening?"""
        return (self.predicted_threat_level in ["critical", "high", "medium"] and
                self.ground_truth == GroundTruth.MALICIOUS)
    
    def is_true_negative(self) -> bool:
        """Was our prediction correct and benign?"""
        return (self.predicted_threat_level in ["low", "minimal"] and
                self.ground_truth == GroundTruth.BENIGN)
    
    def is_false_positive(self) -> bool:
        """Did we cry wolf?"""
        return (self.predicted_threat_level in ["critical", "high", "medium"] and
                self.ground_truth == GroundTruth.BENIGN)
    
    def is_false_negative(self) -> bool:
        """Did we miss a threat?"""
        return (self.predicted_threat_level in ["low", "minimal"] and
                self.ground_truth == GroundTruth.MALICIOUS)
    
    def is_abstained(self) -> bool:
        """Did we refuse to make a decision?"""
        return self.ground_truth == GroundTruth.UNKNOWN


@dataclass
class CategoryMetrics:
    """Accuracy metrics for a single threat category."""
    
    category: ThreatCategory
    
    # Confusion matrix
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    abstentions: int = 0
    
    # Recording
    records: List[AnalysisRecord] = field(default_factory=list)
    
    def precision(self) -> float:
        """TP / (TP + FP): Of all alerts, how many were correct?"""
        total = self.true_positives + self.false_positives
        if total == 0:
            return 1.0  # No alerts = perfect precision
        return self.true_positives / total
    
    def recall(self) -> float:
        """TP / (TP + FN): Of all threats, how many did we catch?"""
        total = self.true_positives + self.false_negatives
        if total == 0:
            return 1.0  # No threats = perfect recall
        return self.true_positives / total
    
    def f1_score(self) -> float:
        """Harmonic mean of precision and recall."""
        p = self.precision()
        r = self.recall()
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
    
    def false_positive_rate(self) -> float:
        """FP / (FP + TN): Type I error rate."""
        total = self.false_positives + self.true_negatives
        if total == 0:
            return 0.0
        return self.false_positives / total
    
    def false_negative_rate(self) -> float:
        """FN / (FN + TP): Type II error rate (missed threats)."""
        total = self.false_negatives + self.true_positives
        if total == 0:
            return 0.0
        return self.false_negatives / total
    
    def average_lead_time_hours(self) -> float:
        """Average advance warning time for TP."""
        if self.true_positives == 0:
            return 0.0
        tp_records = [r for r in self.records if r.is_true_positive()]
        if not tp_records:
            return 0.0
        return sum(r.prediction_lead_time_hours for r in tp_records) / len(tp_records)
    
    def abstention_rate(self) -> float:
        """How often did we decline to make a decision?"""
        total = len(self.records)
        if total == 0:
            return 0.0
        return self.abstentions / total
    
    def accuracy(self) -> float:
        """(TP + TN) / Total: Overall correctness."""
        total = self.true_positives + self.true_negatives + \
                self.false_positives + self.false_negatives
        if total == 0:
            return 1.0
        return (self.true_positives + self.true_negatives) / total
    
    def add_record(self, record: AnalysisRecord):
        """Record analysis outcome."""
        self.records.append(record)
        
        if record.is_true_positive():
            self.true_positives += 1
        elif record.is_true_negative():
            self.true_negatives += 1
        elif record.is_false_positive():
            self.false_positives += 1
        elif record.is_false_negative():
            self.false_negatives += 1
        elif record.is_abstained():
            self.abstentions += 1
    
    def export(self) -> Dict:
        """Export metrics to dictionary."""
        return {
            "category": self.category.value,
            "precision": round(self.precision(), 4),
            "recall": round(self.recall(), 4),
            "f1_score": round(self.f1_score(), 4),
            "accuracy": round(self.accuracy(), 4),
            "false_positive_rate": round(self.false_positive_rate(), 4),
            "false_negative_rate": round(self.false_negative_rate(), 4),
            "average_lead_time_hours": round(self.average_lead_time_hours(), 2),
            "abstention_rate": round(self.abstention_rate(), 4),
            "confusion_matrix": {
                "true_positives": self.true_positives,
                "true_negatives": self.true_negatives,
                "false_positives": self.false_positives,
                "false_negatives": self.false_negatives,
                "abstentions": self.abstentions,
            },
            "total_records": len(self.records),
        }


@dataclass
class AggregateMetrics:
    """Overall system accuracy metrics across all categories."""
    
    category_metrics: Dict[ThreatCategory, CategoryMetrics] = field(default_factory=dict)
    
    # Global counts
    global_tp: int = 0
    global_tn: int = 0
    global_fp: int = 0
    global_fn: int = 0
    global_abstentions: int = 0
    
    def precision(self) -> float:
        """Global precision across all categories."""
        total = self.global_tp + self.global_fp
        if total == 0:
            return 1.0
        return self.global_tp / total
    
    def recall(self) -> float:
        """Global recall across all categories."""
        total = self.global_tp + self.global_fn
        if total == 0:
            return 1.0
        return self.global_tp / total
    
    def f1_score(self) -> float:
        """Global F1-score."""
        p = self.precision()
        r = self.recall()
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
    
    def accuracy(self) -> float:
        """Global accuracy."""
        total = self.global_tp + self.global_tn + self.global_fp + self.global_fn
        if total == 0:
            return 1.0
        return (self.global_tp + self.global_tn) / total
    
    def add_category_metrics(self, metrics: CategoryMetrics):
        """Register category metrics."""
        self.category_metrics[metrics.category] = metrics
        
        # Update global counts
        self.global_tp += metrics.true_positives
        self.global_tn += metrics.true_negatives
        self.global_fp += metrics.false_positives
        self.global_fn += metrics.false_negatives
        self.global_abstentions += metrics.abstentions
    
    def export(self) -> Dict:
        """Export all metrics."""
        return {
            "global": {
                "precision": round(self.precision(), 4),
                "recall": round(self.recall(), 4),
                "f1_score": round(self.f1_score(), 4),
                "accuracy": round(self.accuracy(), 4),
                "confusion_matrix": {
                    "true_positives": self.global_tp,
                    "true_negatives": self.global_tn,
                    "false_positives": self.global_fp,
                    "false_negatives": self.global_fn,
                    "abstentions": self.global_abstentions,
                },
            },
            "per_category": {
                cat.value: metrics.export()
                for cat, metrics in self.category_metrics.items()
            },
        }


# ============================================================================
# EVALUATION FRAMEWORK
# ============================================================================

class EvaluationFramework:
    """
    Central evaluation system tracking accuracy across all threat categories.
    
    Enables:
    - Per-category benchmarking
    - Global system performance
    - Lead-time analysis
    - Ground truth feedback loops
    """
    
    def __init__(self):
        # Initialize per-category metrics
        self.category_metrics: Dict[ThreatCategory, CategoryMetrics] = {}
        for category in ThreatCategory:
            self.category_metrics[category] = CategoryMetrics(category=category)
        
        self.aggregate = AggregateMetrics()
        self.record_count = 0
        self.evaluation_history = []
    
    def record_analysis(
        self,
        indicator: IndicatorSignature,
        threat_state: ThreatState,
        predicted_threat_level: str,
        predicted_confidence: float,
        ground_truth: GroundTruth = GroundTruth.UNKNOWN,
        ground_truth_at: Optional[datetime] = None,
        prediction_lead_time_hours: int = 0,
    ) -> AnalysisRecord:
        """
        Record an analysis with its outcome.
        
        Called twice:
        1. At prediction time (ground_truth=UNKNOWN)
        2. When ground truth arrives (ground_truth=actual value)
        """
        
        # Calculate ground truth delay if we know it
        ground_truth_delay_hours = 0
        if ground_truth_at:
            delay = ground_truth_at - datetime.utcnow()
            ground_truth_delay_hours = int(delay.total_seconds() / 3600)
        
        record = AnalysisRecord(
            indicator=indicator,
            threat_state=threat_state,
            predicted_threat_level=predicted_threat_level,
            predicted_confidence=predicted_confidence,
            predicted_at=datetime.utcnow(),
            ground_truth=ground_truth,
            ground_truth_at=ground_truth_at,
            ground_truth_delay_hours=ground_truth_delay_hours,
            prediction_lead_time_hours=prediction_lead_time_hours,
        )
        
        # Record in appropriate category
        self.category_metrics[indicator.category].add_record(record)
        self.aggregate.add_category_metrics(self.category_metrics[indicator.category])
        
        self.record_count += 1
        self.evaluation_history.append(record)
        
        logger.debug(f"Recorded analysis: {indicator.category.value} "
                    f"{predicted_threat_level} (conf={predicted_confidence:.2f})")
        
        return record
    
    def get_category_metrics(self, category: ThreatCategory) -> CategoryMetrics:
        """Get metrics for specific category."""
        return self.category_metrics.get(category)
    
    def get_aggregate_metrics(self) -> AggregateMetrics:
        """Get system-wide metrics."""
        return self.aggregate
    
    def get_evaluation_report(self) -> Dict:
        """Generate comprehensive evaluation report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_records": self.record_count,
            "aggregate": self.aggregate.export(),
        }
    
    def per_category_summary(self) -> Dict[str, Dict]:
        """Summary of each category's performance."""
        summary = {}
        for category, metrics in self.category_metrics.items():
            summary[category.value] = metrics.export()
        return summary
    
    def identify_weak_categories(self, threshold: float = 0.8) -> List[ThreatCategory]:
        """
        Identify threat categories with F1-score below threshold.
        
        Useful for targeting improvement efforts.
        """
        weak = []
        for category, metrics in self.category_metrics.items():
            if metrics.f1_score() < threshold:
                weak.append(category)
        return weak
    
    def calculate_maturity_score(self) -> float:
        """
        Calculate overall system maturity [0, 1].
        
        Based on:
        - F1-score (primary)
        - Consistency across categories
        - Lead time adequacy
        """
        
        # Need minimum records to be meaningful
        if self.record_count < 100:
            return 0.0
        
        # Base on global F1-score
        f1 = self.aggregate.f1_score()
        
        # Penalize category variance
        f1_scores = [m.f1_score() for m in self.category_metrics.values() if m.records]
        if f1_scores:
            variance = sum((f - sum(f1_scores) / len(f1_scores)) ** 2 
                          for f in f1_scores) / len(f1_scores)
            consistency_penalty = math.sqrt(variance)  # Standard deviation
            f1 = f1 * (1 - 0.1 * consistency_penalty)
        
        # Check lead time adequacy (for critical threats)
        lead_times = [m.average_lead_time_hours() 
                     for m in self.category_metrics.values()]
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
        if avg_lead_time < 6:  # Want at least 6 hours warning
            f1 = f1 * 0.9
        
        return max(0.0, min(1.0, f1))


logger.info("Q-MIND Enterprise: Evaluation framework initialized")
