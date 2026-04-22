"""
================================================================================
Q-MIND ENTERPRISE v3.6 - METRICS MATURITY SYSTEM
================================================================================

Module: metrics_maturity.py

OVERVIEW:
    Replaces ambiguous global metrics with research-grade, category-specific
    metrics that eliminate misleading interpretations.

METRICS PHILOSOPHY:
    - Global accuracy is REMOVED (too ambiguous given class imbalance)
    - Category-wise recall/precision are PRIMARY
    - Alert fatigue and stability metrics are SECONDARY
    - All metrics are SCOPE-LABELED (confusion matrix definitions explicit)
    - All metrics are REPRODUCIBLE (no randomness)

METRIC CLASSES:
    1. Accuracy Metrics: Precision, recall, F1 per category
    2. Stability Metrics: Confidence volatility, decision stability index
    3. Operational Metrics: Alert noise rate, abstention rate, lead-time
    4. Resilience Metrics: Decision reversals, hysteresis locks, confidence damping

================================================================================
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict


class ThreatCategory(Enum):
    """Threat categories for metrics calculation."""
    
    MALWARE = "malware"
    PHISHING = "phishing"
    BOTNET = "botnet"
    C2_INFRASTRUCTURE = "c2"
    VULNERABILITY = "vulnerability"
    BENIGN = "benign"


@dataclass
class ConfusionMatrix:
    """Scope-labeled confusion matrix for single category."""
    
    category: ThreatCategory
    true_positives: int = 0       # Correct threat detection
    true_negatives: int = 0       # Correct benign detection
    false_positives: int = 0      # False threat alarm
    false_negatives: int = 0      # Missed threat (most critical)
    
    scope: str = ""               # Explicit scope: which dataset, time window, etc.
    timestamp: float = field(default_factory=time.time)
    
    def precision(self) -> float:
        """
        Precision = TP / (TP + FP)
        
        Meaning: Of all threats we detected, how many were actually threats?
        Relevance: Prevents alert fatigue (low FP)
        """
        total_positive = self.true_positives + self.false_positives
        return self.true_positives / total_positive if total_positive > 0 else 0.0
    
    def recall(self) -> float:
        """
        Recall = TP / (TP + FN)
        
        Meaning: Of all actual threats, how many did we catch?
        Relevance: Detects missed threats (most critical for security)
        """
        total_actual_positive = self.true_positives + self.false_negatives
        return self.true_positives / total_actual_positive if total_actual_positive > 0 else 0.0
    
    def f1_score(self) -> float:
        """
        F1 = 2 * (precision * recall) / (precision + recall)
        
        Meaning: Harmonic mean of precision/recall
        Relevance: Balances both concerns
        """
        prec = self.precision()
        rec = self.recall()
        total = prec + rec
        return 2 * prec * rec / total if total > 0 else 0.0
    
    def false_positive_rate(self) -> float:
        """
        FPR = FP / (FP + TN)
        
        Meaning: Of actual benign items, how many did we wrongly flag?
        Relevance: Measures alert fatigue
        """
        total_negative = self.false_positives + self.true_negatives
        return self.false_positives / total_negative if total_negative > 0 else 0.0
    
    def false_negative_rate(self) -> float:
        """
        FNR = FN / (FN + TP)
        
        Meaning: Of actual threats, how many did we miss?
        Relevance: Measures missed threats (worst-case scenario)
        """
        total_actual_positive = self.false_negatives + self.true_positives
        return self.false_negatives / total_actual_positive if total_actual_positive > 0 else 0.0
    
    def specificity(self) -> float:
        """
        Specificity = TN / (TN + FP)
        
        Meaning: Of actual benign items, how many did we correctly identify?
        Relevance: True negative rate (complement to FPR)
        """
        total_negative = self.true_negatives + self.false_positives
        return self.true_negatives / total_negative if total_negative > 0 else 0.0


@dataclass
class StabilityMetrics:
    """Decision stability and resilience metrics."""
    
    # Confidence metrics
    mean_confidence: float = 0.0        # Average decision confidence
    confidence_variance: float = 0.0    # Variance in decisions
    confidence_volatility: float = 0.0  # Rate of confidence changes
    
    # Decision stability
    decision_reversals: int = 0         # Times decision flipped threat<->benign
    hysteresis_locks: int = 0           # Times hysteresis prevented reversal
    rapid_collapses: int = 0            # Times Stage-2 collapsed too quickly
    
    # Agreement metrics
    signal_agreement_rate: float = 0.0  # % of times signals agreed
    single_signal_collapses: int = 0    # Times decision collapsed on 1 signal
    
    # Observation window quality
    min_observation_window_met: int = 0 # Times min window respected
    premature_decisions: int = 0        # Times Stage-2 called too early
    
    @property
    def decision_stability_index(self) -> float:
        """
        DSI = (1 - reversals_rate) * agreement_rate * window_quality_rate
        
        Range: [0.0, 1.0]
        Meaning: Overall stability of decision making
        Target: ≥0.85 for production
        """
        reversals_penalty = min(1.0, self.decision_reversals / 100.0)
        window_quality = 1.0 - min(1.0, self.premature_decisions / 50.0)
        dsi = (1.0 - reversals_penalty) * self.signal_agreement_rate * window_quality
        return max(0.0, min(1.0, dsi))


@dataclass
class OperationalMetrics:
    """Real-world operational metrics."""
    
    # Alert volume
    alerts_generated: int = 0           # Total Stage-2 alerts (blocking decisions)
    alerts_per_hour: float = 0.0        # Alert rate
    
    # Alert fatigue
    alert_noise_rate: float = 0.0       # % of alerts that are false positives
    alert_fatigue_index: float = 0.0    # Combined metric for alerter burden
    
    # Timing metrics
    mean_detection_latency: float = 0.0 # Avg time from first signal to Stage-2
    median_detection_latency: float = 0.0
    p95_detection_latency: float = 0.0  # 95th percentile (worst case)
    p99_detection_latency: float = 0.0
    
    # Confidence metrics
    abstention_rate: float = 0.0        # % of decisions deferred (not ready for Stage-2)
    mean_decision_confidence: float = 0.0
    
    # Lead-time improvement
    lead_time_improvement: float = 0.0  # vs baseline (hours)
    early_warning_rate: float = 0.0     # % detected before attack completes


@dataclass
class CategoryMetrics:
    """Complete metrics for single threat category."""
    
    category: ThreatCategory
    confusion_matrix: ConfusionMatrix = field(default_factory=lambda: ConfusionMatrix(category=ThreatCategory.MALWARE))
    stability: StabilityMetrics = field(default_factory=StabilityMetrics)
    operational: OperationalMetrics = field(default_factory=OperationalMetrics)
    
    # Time period
    start_time: float = field(default_factory=time.time)
    end_time: float = field(default_factory=time.time)
    sample_count: int = 0


class MetricsMaturitySystem:
    """
    Research-grade metrics system eliminating ambiguity.
    
    Key improvements over v3.5:
    - Removes global accuracy (class imbalance makes it meaningless)
    - Category-specific metrics for transparency
    - Stability metrics for adversarial resilience
    - Operational metrics for real-world deployment
    - All scope-labeled to prevent misinterpretation
    """
    
    def __init__(self):
        """Initialize metrics system."""
        self.category_metrics: Dict[ThreatCategory, CategoryMetrics] = {
            cat: CategoryMetrics(category=cat) for cat in ThreatCategory
        }
        self.observation_log: List[Dict] = []
        self.confidence_history: Dict[str, List[float]] = defaultdict(list)
    
    def record_observation(
        self,
        threat_id: str,
        category: ThreatCategory,
        ground_truth: bool,
        predicted_threat: bool,
        confidence: float,
        observation_count: int = 1,
    ):
        """
        Record threat decision outcome.
        
        Args:
            threat_id: Unique threat identifier
            category: Threat category
            ground_truth: Was it actually a threat?
            predicted_threat: Did we predict it as threat?
            confidence: Decision confidence [0.0, 1.0]
            observation_count: Number of signals
        """
        metrics = self.category_metrics[category]
        cm = metrics.confusion_matrix
        
        # Update confusion matrix
        if ground_truth:
            if predicted_threat:
                cm.true_positives += 1
            else:
                cm.false_negatives += 1
        else:
            if predicted_threat:
                cm.false_positives += 1
            else:
                cm.true_negatives += 1
        
        metrics.sample_count += 1
        
        # Track confidence
        self.confidence_history[threat_id].append(confidence)
        
        # Log for analysis
        self.observation_log.append({
            'threat_id': threat_id,
            'category': category.value,
            'ground_truth': ground_truth,
            'predicted': predicted_threat,
            'confidence': confidence,
            'observations': observation_count,
            'timestamp': time.time(),
        })
    
    def record_stability_event(
        self,
        threat_id: str,
        category: ThreatCategory,
        event_type: str,
        details: Optional[Dict] = None,
    ):
        """
        Record stability event.
        
        Args:
            threat_id: Threat identifier
            category: Threat category
            event_type: Type of event (reversal, lock, collapse, etc.)
            details: Additional event details
        """
        metrics = self.category_metrics[category]
        stab = metrics.stability
        
        if event_type == "decision_reversal":
            stab.decision_reversals += 1
        elif event_type == "hysteresis_lock":
            stab.hysteresis_locks += 1
        elif event_type == "rapid_collapse":
            stab.rapid_collapses += 1
        elif event_type == "single_signal_collapse":
            stab.single_signal_collapses += 1
        elif event_type == "premature_decision":
            stab.premature_decisions += 1
    
    def calculate_all_metrics(self, time_window: Optional[Tuple[float, float]] = None):
        """
        Calculate all metrics across all categories.
        
        Args:
            time_window: Optional (start_time, end_time) to filter
        """
        for category, metrics in self.category_metrics.items():
            self._calculate_category_metrics(metrics)
    
    def _calculate_category_metrics(self, metrics: CategoryMetrics):
        """Calculate metrics for single category."""
        cm = metrics.confusion_matrix
        
        # Stability calculation
        stab = metrics.stability
        total_samples = metrics.sample_count
        
        if total_samples > 0:
            stab.signal_agreement_rate = 1.0 - (stab.single_signal_collapses / total_samples)
            window_quality = 1.0 - (stab.premature_decisions / total_samples)
            reversals_rate = stab.decision_reversals / max(1, total_samples)
            stab.confidence_volatility = reversals_rate
        
        # Operational calculation
        op = metrics.operational
        
        total_positive_pred = cm.true_positives + cm.false_positives
        if total_positive_pred > 0:
            op.alert_noise_rate = cm.false_positives / total_positive_pred
            op.alert_fatigue_index = (
                op.alert_noise_rate * 0.7 +  # Noise component
                (stab.decision_reversals / 100.0) * 0.3  # Instability component
            )
    
    def get_category_report(self, category: ThreatCategory) -> Dict:
        """
        Generate report for single category.
        
        Args:
            category: Threat category
        
        Returns:
            Dictionary with all metrics and interpretations
        """
        metrics = self.category_metrics[category]
        cm = metrics.confusion_matrix
        stab = metrics.stability
        op = metrics.operational
        
        return {
            'category': category.value,
            'sample_count': metrics.sample_count,
            'time_range': (metrics.start_time, metrics.end_time),
            
            # Accuracy metrics
            'precision': cm.precision(),
            'recall': cm.recall(),
            'f1_score': cm.f1_score(),
            'specificity': cm.specificity(),
            'false_positive_rate': cm.false_positive_rate(),
            'false_negative_rate': cm.false_negative_rate(),
            
            # Confusion matrix (explicit scope)
            'confusion_matrix': {
                'true_positives': cm.true_positives,
                'true_negatives': cm.true_negatives,
                'false_positives': cm.false_positives,
                'false_negatives': cm.false_negatives,
                'scope': f"{category.value}_threats_and_benign_samples",
            },
            
            # Stability metrics
            'decision_stability_index': stab.decision_stability_index,
            'signal_agreement_rate': stab.signal_agreement_rate,
            'decision_reversals': stab.decision_reversals,
            'hysteresis_locks': stab.hysteresis_locks,
            'premature_decisions': stab.premature_decisions,
            
            # Operational metrics
            'alert_noise_rate': op.alert_noise_rate,
            'alert_fatigue_index': op.alert_fatigue_index,
            'abstention_rate': op.abstention_rate,
            'mean_detection_latency_seconds': op.mean_detection_latency,
        }
    
    def get_global_report(self, v35_baseline: Optional[Dict] = None) -> Dict:
        """
        Generate global report across all categories.
        
        Args:
            v35_baseline: v3.5 baseline metrics for comparison
        
        Returns:
            Comprehensive metrics report
        """
        # Aggregate metrics across categories
        total_cm = ConfusionMatrix(category=ThreatCategory.BENIGN, scope="all_categories")
        total_stability = StabilityMetrics()
        
        category_reports = {}
        
        for category in ThreatCategory:
            metrics = self.category_metrics[category]
            report = self.get_category_report(category)
            category_reports[category.value] = report
            
            # Aggregate
            cm = metrics.confusion_matrix
            total_cm.true_positives += cm.true_positives
            total_cm.true_negatives += cm.true_negatives
            total_cm.false_positives += cm.false_positives
            total_cm.false_negatives += cm.false_negatives
            
            stab = metrics.stability
            total_stability.decision_reversals += stab.decision_reversals
            total_stability.hysteresis_locks += stab.hysteresis_locks
            total_stability.premature_decisions += stab.premature_decisions
        
        # Global comparison (if baseline provided)
        comparison = {}
        if v35_baseline:
            for key in ['precision', 'recall', 'f1_score', 'false_positive_rate']:
                v36_val = total_cm.__getattribute__(key)() if callable(getattr(total_cm, key)) else getattr(total_cm, key)
                v35_val = v35_baseline.get(key, 0.0)
                comparison[key] = {
                    'v35': v35_val,
                    'v36': v36_val,
                    'improvement': v36_val - v35_val,
                    'percent_change': ((v36_val - v35_val) / v35_val * 100) if v35_val > 0 else 0.0,
                }
        
        return {
            'report_type': 'global_metrics_v3_6',
            'timestamp': time.time(),
            
            # Global confusion matrix
            'global_confusion_matrix': {
                'true_positives': total_cm.true_positives,
                'true_negatives': total_cm.true_negatives,
                'false_positives': total_cm.false_positives,
                'false_negatives': total_cm.false_negatives,
                'scope': 'all_threat_categories_and_benign',
            },
            
            # Global accuracy metrics (NOT global accuracy - scope is explicit)
            'global_precision': total_cm.precision(),
            'global_recall': total_cm.recall(),
            'global_f1': total_cm.f1_score(),
            
            # Stability (global)
            'global_decision_reversals': total_stability.decision_reversals,
            'global_hysteresis_locks': total_stability.hysteresis_locks,
            'global_premature_decisions': total_stability.premature_decisions,
            
            # Category-wise breakdown
            'category_reports': category_reports,
            
            # Comparison with v3.5 (if available)
            'v35_comparison': comparison,
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_metrics_system() -> MetricsMaturitySystem:
    """Factory function to create metrics system."""
    return MetricsMaturitySystem()


def print_category_report(report: Dict):
    """Pretty-print category metrics report."""
    print(f"\n{'='*70}")
    print(f"METRICS: {report['category'].upper()}")
    print(f"{'='*70}")
    print(f"Sample Count: {report['sample_count']}")
    print(f"\nAccuracy Metrics:")
    print(f"  Precision: {report['precision']:.4f}")
    print(f"  Recall: {report['recall']:.4f}")
    print(f"  F1-Score: {report['f1_score']:.4f}")
    print(f"  Specificity: {report['specificity']:.4f}")
    print(f"  FPR: {report['false_positive_rate']:.4f}")
    print(f"  FNR: {report['false_negative_rate']:.4f}")
    print(f"\nStability Metrics:")
    print(f"  Decision Stability Index: {report['decision_stability_index']:.4f}")
    print(f"  Signal Agreement Rate: {report['signal_agreement_rate']:.4f}")
    print(f"  Decision Reversals: {report['decision_reversals']}")
    print(f"  Hysteresis Locks: {report['hysteresis_locks']}")
    print(f"\nOperational Metrics:")
    print(f"  Alert Noise Rate: {report['alert_noise_rate']:.4f}")
    print(f"  Detection Latency: {report['mean_detection_latency_seconds']:.1f}s")


# ============================================================================
# END OF MODULE
# ============================================================================
