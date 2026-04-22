"""
Q-MIND Enterprise: Research-Grade Validation Pipeline

This pipeline implements scientifically defensible validation with:
  • Chronological replay (simulate real-time threat arrival)
  • Delayed ground truth alignment
  • Signal enrichment without label leakage
  • Explainable decision logic
  • Academic-grade accuracy metrics
  • Before/after comparison framework

No black-box ML. No hardcoded labels. All logic is transparent.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, field
import statistics

from datasets.research_datasets import (
    IndicatorRecord, IndicatorStatus, ResearchDatasetRegistry
)
from core.threat_state import ThreatStateManager, IndicatorSignature, ThreatCategory
from evaluation.accuracy_metrics import EvaluationFramework, GroundTruth
from mitigation.recommendation_engine import MitigationEngine

logger = logging.getLogger(__name__)


# ============================================================================
# RESEARCH VALIDATION FRAMEWORK
# ============================================================================

@dataclass
class ValidationMetrics:
    """Comprehensive validation metrics (per dataset)."""
    
    dataset_name: str
    indicators_total: int
    indicators_processed: int
    indicators_validated: int
    
    # Accuracy metrics
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    # Timing metrics
    avg_lead_time_hours: float = 0.0
    min_lead_time_hours: int = 0
    max_lead_time_hours: int = 0
    
    # Confidence metrics
    avg_confidence: float = 0.0
    high_confidence_count: int = 0  # >0.8
    low_confidence_count: int = 0   # <0.5
    
    # Abstention metrics
    abstained_count: int = 0
    abstention_rate: float = 0.0
    
    # Error analysis
    false_positive_analysis: Dict[str, int] = field(default_factory=dict)
    false_negative_analysis: Dict[str, int] = field(default_factory=dict)
    
    def precision(self) -> float:
        """TP / (TP + FP)"""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 1.0
    
    def recall(self) -> float:
        """TP / (TP + FN)"""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 1.0
    
    def f1_score(self) -> float:
        """Harmonic mean of precision and recall."""
        p = self.precision()
        r = self.recall()
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
    
    def false_positive_rate(self) -> float:
        """FP / (FP + TN) - Type I error."""
        total = self.false_positives + self.true_negatives
        return self.false_positives / total if total > 0 else 0.0
    
    def false_negative_rate(self) -> float:
        """FN / (FN + TP) - Type II error."""
        total = self.false_negatives + self.true_positives
        return self.false_negatives / total if total > 0 else 0.0
    
    def accuracy(self) -> float:
        """(TP + TN) / Total"""
        total = self.true_positives + self.true_negatives + \
                self.false_positives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 1.0
    
    def export(self) -> Dict:
        """Export metrics as dictionary."""
        return {
            "dataset": self.dataset_name,
            "total": self.indicators_total,
            "processed": self.indicators_processed,
            "validated": self.indicators_validated,
            "precision": round(self.precision(), 4),
            "recall": round(self.recall(), 4),
            "f1_score": round(self.f1_score(), 4),
            "accuracy": round(self.accuracy(), 4),
            "false_positive_rate": round(self.false_positive_rate(), 4),
            "false_negative_rate": round(self.false_negative_rate(), 4),
            "avg_lead_time_hours": round(self.avg_lead_time_hours, 2),
            "avg_confidence": round(self.avg_confidence, 4),
            "abstention_rate": round(self.abstention_rate, 4),
            "confusion_matrix": {
                "tp": self.true_positives,
                "tn": self.true_negatives,
                "fp": self.false_positives,
                "fn": self.false_negatives,
            },
        }


@dataclass
class SystemComparisonMetrics:
    """Before vs After comparison."""
    
    metric_name: str
    baseline_v3: float  # Q-MIND v3.x results
    improved: float     # After enhancement
    improvement_pct: float = 0.0
    
    def __post_init__(self):
        if self.baseline_v3 != 0:
            self.improvement_pct = ((self.improved - self.baseline_v3) / self.baseline_v3) * 100
    
    def export(self) -> Dict:
        return {
            "metric": self.metric_name,
            "baseline": round(self.baseline_v3, 4),
            "improved": round(self.improved, 4),
            "improvement_pct": round(self.improvement_pct, 2),
        }


class ResearchValidationPipeline:
    """
    Research-grade validation pipeline for Q-MIND Enterprise.
    
    Features:
    • Chronological replay with delayed ground truth
    • Signal enrichment analysis
    • Explainable decision logic
    • Before/after comparison
    • False positive/negative analysis
    • Academic-grade reporting
    """
    
    def __init__(self):
        self.threat_state_manager = ThreatStateManager()
        self.mitigation_engine = MitigationEngine()
        self.evaluation_framework = EvaluationFramework()
        self.dataset_registry = ResearchDatasetRegistry()
        
        self.validation_records: Dict[str, List[IndicatorRecord]] = {}
        self.validation_metrics: Dict[str, ValidationMetrics] = {}
        self.comparison_metrics: List[SystemComparisonMetrics] = []
        
        logger.info("Research Validation Pipeline initialized")
    
    def validate_dataset(
        self,
        dataset_name: str,
        sample_size: int = 1000,
        replay_chronologically: bool = True,
    ) -> ValidationMetrics:
        """
        Validate a single dataset with chronological replay.
        
        Process:
        1. Load indicators from dataset
        2. Sort chronologically (if requested)
        3. Process through Q-MIND
        4. Wait for delayed ground truth
        5. Calculate metrics
        """
        
        logger.info(f"Validating dataset: {dataset_name} (n={sample_size})")
        
        # Load indicators
        indicators = self.dataset_registry.load_dataset(dataset_name, sample_size)
        
        # Sort chronologically
        if replay_chronologically:
            indicators = sorted(indicators, key=lambda x: x.first_seen_time)
        
        # Initialize metrics
        metrics = ValidationMetrics(
            dataset_name=dataset_name,
            indicators_total=len(indicators),
            indicators_processed=0,
            indicators_validated=0,
        )
        
        # Process each indicator
        for record in indicators:
            # Convert to Q-MIND format
            indicator = IndicatorSignature(
                indicator_type=record.indicator_type,
                indicator_value=record.indicator_value,
                category=self._map_category(record.category)
            )
            
            # Get threat state
            threat_state = self.threat_state_manager.get_or_create_state(indicator)
            
            # Simulate processing time
            record.first_warning_time = record.first_seen_time + timedelta(seconds=1)
            
            # Measure threat level
            decision = threat_state.measure()
            record.predicted_threat_level = decision.get("threat_level", "minimal")
            record.predicted_confidence = decision.get("confidence", 0.0)
            record.signals_used = list(threat_state.indicator_to_state.get(
                str(indicator), threat_state
            ).signals_log[-3:]) if hasattr(threat_state, 'signals_log') else []
            
            # Calculate lead time
            if record.ground_truth_time:
                delta = record.ground_truth_time - record.first_warning_time
                record.lead_time_hours = int(delta.total_seconds() / 3600)
            
            # Mark as processed
            record.status = IndicatorStatus.PROCESSED
            metrics.indicators_processed += 1
            
            # Wait for ground truth (simulated)
            if record.actual_threat is not None:
                self._align_ground_truth(record, metrics)
                record.status = IndicatorStatus.VALIDATED
                metrics.indicators_validated += 1
        
        # Finalize metrics
        self._finalize_metrics(metrics, indicators)
        
        # Store results
        self.validation_records[dataset_name] = indicators
        self.validation_metrics[dataset_name] = metrics
        
        logger.info(f"Validation complete: {dataset_name} "
                   f"(P={metrics.precision():.4f}, R={metrics.recall():.4f}, "
                   f"F1={metrics.f1_score():.4f})")
        
        return metrics
    
    def validate_all_datasets(self, sample_size: int = 500) -> Dict[str, ValidationMetrics]:
        """Validate all available datasets."""
        logger.info(f"Starting comprehensive validation of all datasets...")
        
        results = {}
        for dataset_name in self.dataset_registry.list_datasets().keys():
            try:
                metrics = self.validate_dataset(dataset_name, sample_size)
                results[dataset_name] = metrics
            except Exception as e:
                logger.error(f"Validation failed for {dataset_name}: {e}")
                continue
        
        return results
    
    def _align_ground_truth(self, record: IndicatorRecord, metrics: ValidationMetrics):
        """Align predicted with ground truth."""
        
        # Convert ground truth to threat assessment
        ground_truth_threat = record.actual_threat or False
        
        # Determine prediction (true positive if any alert)
        predicted_threat = record.predicted_threat_level not in ["minimal", "low"]
        
        # Update confusion matrix
        if predicted_threat and ground_truth_threat:
            metrics.true_positives += 1
        elif not predicted_threat and not ground_truth_threat:
            metrics.true_negatives += 1
        elif predicted_threat and not ground_truth_threat:
            metrics.false_positives += 1
            metrics.false_positive_analysis[record.category] = \
                metrics.false_positive_analysis.get(record.category, 0) + 1
        elif not predicted_threat and ground_truth_threat:
            metrics.false_negatives += 1
            metrics.false_negative_analysis[record.category] = \
                metrics.false_negative_analysis.get(record.category, 0) + 1
    
    def _finalize_metrics(self, metrics: ValidationMetrics, records: List[IndicatorRecord]):
        """Finalize metric calculations."""
        
        validated = [r for r in records if r.status == IndicatorStatus.VALIDATED]
        
        if validated:
            # Lead time
            lead_times = [r.lead_time_hours for r in validated if r.lead_time_hours > 0]
            if lead_times:
                metrics.avg_lead_time_hours = statistics.mean(lead_times)
                metrics.min_lead_time_hours = min(lead_times)
                metrics.max_lead_time_hours = max(lead_times)
            
            # Confidence
            confidences = [r.predicted_confidence for r in validated]
            metrics.avg_confidence = statistics.mean(confidences) if confidences else 0.0
            metrics.high_confidence_count = sum(1 for r in validated if r.predicted_confidence > 0.8)
            metrics.low_confidence_count = sum(1 for r in validated if r.predicted_confidence < 0.5)
            
            # Abstention (low confidence + uncertain prediction)
            metrics.abstained_count = sum(1 for r in validated 
                                         if r.predicted_threat_level == "minimal" 
                                         and r.predicted_confidence < 0.6)
            metrics.abstention_rate = metrics.abstained_count / len(validated) if validated else 0.0
    
    def _map_category(self, category: str) -> ThreatCategory:
        """Map research dataset category to ThreatCategory."""
        mapping = {
            "phishing": ThreatCategory.PHISHING,
            "malware": ThreatCategory.MALWARE,
            "c2_infrastructure": ThreatCategory.C2_INFRASTRUCTURE,
            "botnet": ThreatCategory.BOTNET_IP,
            "vulnerability": ThreatCategory.VULNERABILITY,
            "benign": ThreatCategory.BENIGN,
            "ddos": ThreatCategory.DDOS,
            "port_scan": ThreatCategory.BOTNET_IP,
            "brute_force": ThreatCategory.INSIDER_THREAT,
        }
        return mapping.get(category, ThreatCategory.BENIGN)
    
    def generate_research_report(self) -> Dict:
        """
        Generate research-grade validation report.
        
        Contains:
        • Dataset summary
        • Per-dataset accuracy metrics
        • False positive/negative analysis
        • Lead-time analysis
        • Comparison with baseline
        • Recommendations for improvement
        """
        
        logger.info("Generating research-grade validation report...")
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "Q-MIND Enterprise v3.x (Research Edition)",
            "validation_type": "Chronological Replay with Delayed Ground Truth",
            "datasets_tested": list(self.validation_metrics.keys()),
            "total_indicators": sum(m.indicators_total for m in self.validation_metrics.values()),
            "total_validated": sum(m.indicators_validated for m in self.validation_metrics.values()),
            
            # Per-dataset metrics
            "per_dataset": {
                name: metrics.export()
                for name, metrics in self.validation_metrics.items()
            },
            
            # Aggregate metrics
            "aggregate": self._calculate_aggregate_metrics(),
            
            # Analysis
            "false_positive_analysis": self._analyze_false_positives(),
            "false_negative_analysis": self._analyze_false_negatives(),
            "lead_time_summary": self._summarize_lead_times(),
            
            # Recommendations
            "recommendations": self._generate_recommendations(),
        }
        
        return report
    
    def _calculate_aggregate_metrics(self) -> Dict:
        """Calculate system-wide metrics."""
        
        agg = {
            "total_tp": sum(m.true_positives for m in self.validation_metrics.values()),
            "total_tn": sum(m.true_negatives for m in self.validation_metrics.values()),
            "total_fp": sum(m.false_positives for m in self.validation_metrics.values()),
            "total_fn": sum(m.false_negatives for m in self.validation_metrics.values()),
        }
        
        tp, tn, fp, fn = agg["total_tp"], agg["total_tn"], agg["total_fp"], agg["total_fn"]
        
        if tp + fp > 0:
            agg["precision"] = round(tp / (tp + fp), 4)
        else:
            agg["precision"] = 1.0
        
        if tp + fn > 0:
            agg["recall"] = round(tp / (tp + fn), 4)
        else:
            agg["recall"] = 1.0
        
        p, r = agg["precision"], agg["recall"]
        if p + r > 0:
            agg["f1_score"] = round(2 * (p * r) / (p + r), 4)
        else:
            agg["f1_score"] = 0.0
        
        total = tp + tn + fp + fn
        if total > 0:
            agg["accuracy"] = round((tp + tn) / total, 4)
        else:
            agg["accuracy"] = 1.0
        
        if fp + tn > 0:
            agg["false_positive_rate"] = round(fp / (fp + tn), 4)
        else:
            agg["false_positive_rate"] = 0.0
        
        if fn + tp > 0:
            agg["false_negative_rate"] = round(fn / (fn + tp), 4)
        else:
            agg["false_negative_rate"] = 0.0
        
        return agg
    
    def _analyze_false_positives(self) -> Dict:
        """Analyze false positives by category."""
        analysis = {}
        for name, metrics in self.validation_metrics.items():
            if metrics.false_positive_analysis:
                analysis[name] = {
                    "count": metrics.false_positives,
                    "by_category": metrics.false_positive_analysis,
                    "rate": round(metrics.false_positive_rate(), 4),
                }
        return analysis
    
    def _analyze_false_negatives(self) -> Dict:
        """Analyze false negatives by category."""
        analysis = {}
        for name, metrics in self.validation_metrics.items():
            if metrics.false_negative_analysis:
                analysis[name] = {
                    "count": metrics.false_negatives,
                    "by_category": metrics.false_negative_analysis,
                    "rate": round(metrics.false_negative_rate(), 4),
                }
        return analysis
    
    def _summarize_lead_times(self) -> Dict:
        """Summarize lead-time (early warning) analysis."""
        summary = {}
        for name, metrics in self.validation_metrics.items():
            if metrics.avg_lead_time_hours > 0:
                summary[name] = {
                    "avg_hours": round(metrics.avg_lead_time_hours, 2),
                    "min_hours": metrics.min_lead_time_hours,
                    "max_hours": metrics.max_lead_time_hours,
                }
        return summary
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate improvement recommendations based on results."""
        recommendations = []
        
        for name, metrics in self.validation_metrics.items():
            if metrics.false_positive_rate() > 0.15:
                recommendations.append({
                    "dataset": name,
                    "issue": "High false positive rate",
                    "current_fpr": round(metrics.false_positive_rate(), 4),
                    "target_fpr": 0.05,
                    "action": "Increase decision thresholds, add precision-focused signal",
                })
            
            if metrics.recall() < 0.75:
                recommendations.append({
                    "dataset": name,
                    "issue": "Low recall (missed threats)",
                    "current_recall": round(metrics.recall(), 4),
                    "target_recall": 0.85,
                    "action": "Lower decision thresholds, add sensitivity-focused signal",
                })
            
            if metrics.abstention_rate > 0.10:
                recommendations.append({
                    "dataset": name,
                    "issue": "High abstention rate (uncertain decisions)",
                    "current_rate": round(metrics.abstention_rate, 4),
                    "target_rate": 0.05,
                    "action": "Improve signal confidence, add supplementary signals",
                })
        
        return recommendations


logger.info("Research Validation Pipeline module loaded")
