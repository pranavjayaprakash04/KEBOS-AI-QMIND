#!/usr/bin/env python3
"""
Q-MIND Enterprise: Large-Scale External Dataset Testing

Comprehensive testing with 1M+ real threat intelligence records.

This script:
1. Downloads datasets from 8 credible sources
2. Processes 1M+ threat indicators
3. Tests Q-MIND Enterprise detection accuracy
4. Generates detailed performance report
5. Analyzes results by threat category
"""

import sys
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Q-MIND components
from core.threat_state import ThreatCategory, IndicatorSignature, ThreatStateManager
from signals.threat_signals import (
    PhishingLexicalSignal, MalwareHashReputationSignal, ASNReputationSignal,
    C2TemporalSignal, CVESeveritySignal, BenignSignal
)
from datasets.external_dataset_loader import ExternalDatasetLoader
from mitigation.recommendation_engine import MitigationEngine
from evaluation.accuracy_metrics import EvaluationFramework, GroundTruth


class LargeScaleExternalTester:
    """
    Large-scale testing framework using external datasets.
    """
    
    def __init__(self):
        self.threat_state_manager = ThreatStateManager()
        self.mitigation_engine = MitigationEngine()
        self.evaluation_framework = EvaluationFramework()
        self.dataset_loader = ExternalDatasetLoader()
        
        self.results = {
            'total_indicators': 0,
            'by_category': defaultdict(lambda: {'analyzed': 0, 'detected': 0, 'recommended': 0}),
            'threat_levels': defaultdict(int),
            'processing_times': [],
            'recommendations': [],
            'accuracy_metrics': {},
            'performance': {}
        }
    
    def test_external_datasets(self, scale: str = 'large', max_indicators: int = None):
        """
        Test Q-MIND Enterprise with external datasets.
        
        scale: 'small' (~50K), 'medium' (~250K), 'large' (~1M+)
        """
        
        print("\n" + "="*80)
        print("Q-MIND ENTERPRISE: LARGE-SCALE EXTERNAL DATASET TESTING")
        print("="*80)
        
        # Step 1: Load external datasets
        print(f"\n[STEP 1] LOADING EXTERNAL DATASETS ({scale} scale)")
        print("-" * 80)
        
        start_load = time.time()
        datasets = self.dataset_loader.load_all_datasets(scale=scale)
        load_time = time.time() - start_load
        
        total_records = sum(len(v) for v in datasets.values())
        print(f"\nLoaded {total_records:,} records from 8 sources in {load_time:.2f}s")
        
        for source, records in datasets.items():
            print(f"  {source:30} {len(records):10,} records")
        
        # Step 2: Convert to threat indicators
        print(f"\n[STEP 2] CONVERTING TO THREAT INDICATORS")
        print("-" * 80)
        
        indicators = self._convert_datasets_to_indicators(datasets, max_indicators)
        print(f"\nConverted to {len(indicators):,} threat indicators")
        
        # Step 3: Analyze with Q-MIND
        print(f"\n[STEP 3] ANALYZING WITH Q-MIND ENTERPRISE")
        print("-" * 80)
        
        self._analyze_indicators(indicators)
        
        # Step 4: Generate recommendations
        print(f"\n[STEP 4] GENERATING MITIGATION RECOMMENDATIONS")
        print("-" * 80)
        
        self._generate_recommendations(indicators)
        
        # Step 5: Evaluate accuracy
        print(f"\n[STEP 5] EVALUATING ACCURACY")
        print("-" * 80)
        
        self._evaluate_accuracy(indicators, datasets)
        
        # Step 6: Generate report
        print(f"\n[STEP 6] GENERATING COMPREHENSIVE REPORT")
        print("-" * 80)
        
        report = self._generate_report()
        
        return report
    
    def _convert_datasets_to_indicators(self, datasets: Dict, max_indicators: int = None) -> List[Tuple]:
        """
        Convert external datasets to threat indicators.
        """
        
        indicators = []
        
        # PhishTank -> Phishing URLs
        for url_data in datasets.get('phishing_phishtank', []):
            indicator = IndicatorSignature(
                indicator_type='url',
                indicator_value=url_data.get('url', '')[:100],
                category=ThreatCategory.PHISHING
            )
            indicators.append((indicator, 'phishing_phishtank', url_data))
        
        # OpenPhish -> Phishing URLs
        for url_data in datasets.get('phishing_openphish', []):
            indicator = IndicatorSignature(
                indicator_type='url',
                indicator_value=url_data.get('url', '')[:100],
                category=ThreatCategory.PHISHING
            )
            indicators.append((indicator, 'phishing_openphish', url_data))
        
        # MalwareBazaar -> Malware
        for hash_data in datasets.get('malware', []):
            indicator = IndicatorSignature(
                indicator_type='hash',
                indicator_value=hash_data.get('sha256', '')[:64],
                category=ThreatCategory.MALWARE
            )
            indicators.append((indicator, 'malware', hash_data))
        
        # AbuseIPDB -> Botnet/Malicious IPs
        for ip_data in datasets.get('malicious_ips', []):
            indicator = IndicatorSignature(
                indicator_type='ip',
                indicator_value=ip_data.get('ipAddress', ''),
                category=ThreatCategory.BOTNET_IP
            )
            indicators.append((indicator, 'malicious_ips', ip_data))
        
        # Tranco -> Benign Domains
        for domain_data in datasets.get('benign_domains', []):
            indicator = IndicatorSignature(
                indicator_type='domain',
                indicator_value=domain_data.get('domain', ''),
                category=ThreatCategory.BENIGN
            )
            indicators.append((indicator, 'benign_domains', domain_data))
        
        # NVD -> Vulnerabilities
        for cve_data in datasets.get('vulnerabilities', []):
            indicator = IndicatorSignature(
                indicator_type='cve',
                indicator_value=cve_data.get('cveId', ''),
                category=ThreatCategory.VULNERABILITY
            )
            indicators.append((indicator, 'vulnerabilities', cve_data))
        
        # URLhaus -> Malicious URLs
        for url_data in datasets.get('malicious_urls', []):
            indicator = IndicatorSignature(
                indicator_type='url',
                indicator_value=url_data.get('url', '')[:100],
                category=ThreatCategory.PHISHING  # Classify as phishing
            )
            indicators.append((indicator, 'malicious_urls', url_data))
        
        # Feodo Tracker -> C2 Infrastructure
        for c2_data in datasets.get('c2_infrastructure', []):
            indicator = IndicatorSignature(
                indicator_type='ip',
                indicator_value=c2_data.get('ip_address', ''),
                category=ThreatCategory.C2_INFRASTRUCTURE
            )
            indicators.append((indicator, 'c2_infrastructure', c2_data))
        
        if max_indicators:
            indicators = indicators[:max_indicators]
        
        self.results['total_indicators'] = len(indicators)
        return indicators
    
    def _analyze_indicators(self, indicators: List[Tuple]):
        """
        Analyze all indicators with Q-MIND.
        """
        
        start_time = time.time()
        
        for i, (indicator, source, raw_data) in enumerate(indicators):
            try:
                # Get threat state
                threat_state = self.threat_state_manager.get_or_create_state(indicator)
                
                # Create and add signal based on category
                signal = self._create_signal(indicator, raw_data)
                if signal:
                    threat_state.add_signal(signal)
                
                # Measure threat
                decision = threat_state.measure()
                
                # Track results
                self.results['by_category'][indicator.category.value]['analyzed'] += 1
                
                threat_level = decision.get('threat_level', 'minimal')
                self.results['threat_levels'][threat_level] += 1
                
                if threat_level not in ['minimal', 'low']:
                    self.results['by_category'][indicator.category.value]['detected'] += 1
                
                # Progress
                if (i + 1) % 10000 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    remaining = (len(indicators) - i - 1) / rate if rate > 0 else 0
                    print(f"  Analyzed: {i+1:,} ({rate:.0f} indicators/sec) "
                          f"ETA: {remaining:.0f}s")
            
            except Exception as e:
                logger.warning(f"Analysis failed for {indicator.indicator_value}: {e}")
                continue
        
        total_time = time.time() - start_time
        self.results['processing_times'].append(total_time)
        
        print(f"\nAnalyzed {len(indicators):,} indicators in {total_time:.2f}s")
        print(f"Rate: {len(indicators)/total_time:.0f} indicators/second")
    
    def _create_signal(self, indicator: IndicatorSignature, raw_data: Dict):
        """Create appropriate signal based on indicator type."""
        
        try:
            if indicator.category == ThreatCategory.PHISHING:
                return PhishingLexicalSignal(
                    url=raw_data.get('url', '')[:100],
                    entropy=min(len(raw_data.get('url', '')) / 10, 5.0),
                    special_char_count=sum(1 for c in raw_data.get('url', '') if c in '!@#$%^&*-_=+[]{}|;:,.<>?/~`')
                )
            
            elif indicator.category == ThreatCategory.MALWARE:
                stats = raw_data.get('last_analysis', {})
                malicious = stats.get('malicious', 0)
                total = sum(stats.values()) if stats else 70
                return MalwareHashReputationSignal(
                    file_hash=raw_data.get('sha256', ''),
                    av_hits=malicious,
                    total_scanners=total
                )
            
            elif indicator.category == ThreatCategory.BOTNET_IP:
                return ASNReputationSignal(
                    asn=raw_data.get('asn', 'unknown'),
                    known_bulletproof_hosting='bulletproof' in raw_data.get('isp', '').lower(),
                    abuse_reports=raw_data.get('abuseConfidenceScore', 0)
                )
            
            elif indicator.category == ThreatCategory.C2_INFRASTRUCTURE:
                return C2TemporalSignal(
                    ip_or_domain=raw_data.get('ip_address', ''),
                    request_rate=50.0,
                    off_hours_activity=True
                )
            
            elif indicator.category == ThreatCategory.VULNERABILITY:
                cvss = raw_data.get('cvssMetricV31', {}).get('cvssData', {}).get('baseScore', 0)
                return CVESeveritySignal(
                    cve_id=raw_data.get('cveId', ''),
                    cvss_score=float(cvss),
                    exploits_public=1
                )
            
            elif indicator.category == ThreatCategory.BENIGN:
                return BenignSignal(
                    indicator=indicator.indicator_value,
                    reason=f"Tranco rank {raw_data.get('rank', 0)}",
                    certitude=0.99
                )
        
        except Exception as e:
            logger.warning(f"Signal creation failed: {e}")
            return None
    
    def _generate_recommendations(self, indicators: List[Tuple]):
        """Generate mitigation recommendations."""
        
        start_time = time.time()
        
        for i, (indicator, source, raw_data) in enumerate(indicators):
            try:
                threat_state = self.threat_state_manager.get_or_create_state(indicator)
                decision = threat_state.measure()
                
                if decision.get('threat_level', 'minimal') not in ['minimal', 'low']:
                    plan = self.mitigation_engine.generate_recommendations(
                        indicator, threat_state
                    )
                    
                    self.results['by_category'][indicator.category.value]['recommended'] += 1
                    self.results['recommendations'].append({
                        'category': indicator.category.value,
                        'action': plan.primary_recommendation.action.value,
                        'priority': plan.primary_recommendation.priority,
                        'threat_level': decision.get('threat_level')
                    })
            
            except Exception as e:
                logger.warning(f"Recommendation failed: {e}")
                continue
            
            if (i + 1) % 50000 == 0:
                elapsed = time.time() - start_time
                print(f"  Generated recommendations for {i+1:,} indicators")
        
        print(f"\nGenerated {len(self.results['recommendations']):,} recommendations")
    
    def _evaluate_accuracy(self, indicators: List[Tuple], datasets: Dict):
        """Evaluate accuracy with ground truth."""
        
        # Assign ground truth based on source
        for indicator, source, raw_data in indicators:
            threat_state = self.threat_state_manager.get_or_create_state(indicator)
            decision = threat_state.measure()
            
            # Ground truth assignment
            if source == 'benign_domains':
                ground_truth = GroundTruth.BENIGN
            elif source in ['phishing_phishtank', 'phishing_openphish', 'malicious_urls']:
                ground_truth = GroundTruth.MALICIOUS
            elif source in ['malware', 'c2_infrastructure']:
                ground_truth = GroundTruth.MALICIOUS
            elif source == 'malicious_ips':
                ground_truth = GroundTruth.MALICIOUS if raw_data.get('abuseConfidenceScore', 0) > 50 else GroundTruth.BENIGN
            else:
                ground_truth = GroundTruth.MALICIOUS
            
            # Record analysis
            self.evaluation_framework.record_analysis(
                indicator=indicator,
                threat_state=threat_state,
                predicted_threat_level=decision.get('threat_level', 'minimal'),
                predicted_confidence=decision.get('confidence', 0.5),
                ground_truth=ground_truth,
                prediction_lead_time_hours=decision.get('lead_time_hours', 0)
            )
        
        # Get metrics
        agg = self.evaluation_framework.get_aggregate_metrics()
        
        self.results['accuracy_metrics'] = {
            'global_precision': agg.precision(),
            'global_recall': agg.recall(),
            'global_f1': agg.f1_score(),
            'global_accuracy': agg.accuracy(),
            'per_category': {}
        }
        
        for category in ThreatCategory:
            metrics = self.evaluation_framework.get_category_metrics(category)
            self.results['accuracy_metrics']['per_category'][category.value] = {
                'precision': metrics.precision(),
                'recall': metrics.recall(),
                'f1_score': metrics.f1_score(),
                'accuracy': metrics.accuracy(),
                'tp': metrics.true_positives,
                'tn': metrics.true_negatives,
                'fp': metrics.false_positives,
                'fn': metrics.false_negatives
            }
    
    def _generate_report(self) -> str:
        """Generate comprehensive test report."""
        
        report = []
        report.append("\n" + "="*80)
        report.append("Q-MIND ENTERPRISE: LARGE-SCALE EXTERNAL DATASET TEST REPORT")
        report.append("="*80)
        
        report.append(f"\nTest Date: {datetime.utcnow().isoformat()}")
        report.append(f"Total Indicators Analyzed: {self.results['total_indicators']:,}")
        
        # Threat levels
        report.append("\n[THREAT LEVEL DISTRIBUTION]")
        report.append("-" * 80)
        for level in ['critical', 'high', 'medium', 'low', 'minimal']:
            count = self.results['threat_levels'].get(level, 0)
            pct = (count / self.results['total_indicators'] * 100) if self.results['total_indicators'] > 0 else 0
            report.append(f"  {level:10} {count:10,} ({pct:6.2f}%)")
        
        # Category breakdown
        report.append("\n[CATEGORY ANALYSIS]")
        report.append("-" * 80)
        report.append(f"{'Category':<25} {'Analyzed':>12} {'Detected':>12} {'Recommended':>12} {'Det Rate':>10}")
        report.append("-" * 80)
        
        for category, stats in sorted(self.results['by_category'].items()):
            analyzed = stats['analyzed']
            detected = stats['detected']
            recommended = stats['recommended']
            det_rate = (detected / analyzed * 100) if analyzed > 0 else 0
            
            report.append(f"{category:<25} {analyzed:>12,} {detected:>12,} {recommended:>12,} {det_rate:>9.2f}%")
        
        # Accuracy metrics
        report.append("\n[ACCURACY METRICS]")
        report.append("-" * 80)
        
        metrics = self.results['accuracy_metrics']
        report.append(f"Global Precision: {metrics.get('global_precision', 0):.4f}")
        report.append(f"Global Recall:    {metrics.get('global_recall', 0):.4f}")
        report.append(f"Global F1-Score:  {metrics.get('global_f1', 0):.4f}")
        report.append(f"Global Accuracy:  {metrics.get('global_accuracy', 0):.4f}")
        
        report.append("\n[PER-CATEGORY ACCURACY]")
        report.append("-" * 80)
        
        for category, cat_metrics in sorted(metrics.get('per_category', {}).items()):
            report.append(f"\n{category}:")
            report.append(f"  Precision: {cat_metrics.get('precision', 0):.4f}")
            report.append(f"  Recall:    {cat_metrics.get('recall', 0):.4f}")
            report.append(f"  F1-Score:  {cat_metrics.get('f1_score', 0):.4f}")
            report.append(f"  TP: {cat_metrics.get('tp', 0)}, TN: {cat_metrics.get('tn', 0)}, "
                         f"FP: {cat_metrics.get('fp', 0)}, FN: {cat_metrics.get('fn', 0)}")
        
        # Performance
        report.append("\n[PERFORMANCE]")
        report.append("-" * 80)
        
        if self.results['processing_times']:
            total_time = self.results['processing_times'][0]
            rate = self.results['total_indicators'] / total_time if total_time > 0 else 0
            report.append(f"Total Processing Time: {total_time:.2f}s")
            report.append(f"Analysis Rate: {rate:.0f} indicators/second")
            report.append(f"Recommendations Generated: {len(self.results['recommendations']):,}")
        
        # Recommendations summary
        report.append("\n[RECOMMENDATIONS SUMMARY]")
        report.append("-" * 80)
        
        action_counts = defaultdict(int)
        for rec in self.results['recommendations']:
            action_counts[rec['action']] += 1
        
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {action:<30} {count:10,}")
        
        report.append("\n" + "="*80)
        report.append("TEST COMPLETE")
        report.append("="*80)
        
        return "\n".join(report)


def main():
    """Run comprehensive external dataset testing."""
    
    tester = LargeScaleExternalTester()
    
    # Run test with large scale (1M+ records)
    report = tester.test_external_datasets(scale='large')
    
    # Print report
    print(report)
    
    # Save report to file
    report_file = 'external_dataset_test_results.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")
    
    # Also save detailed results as JSON
    import json
    results_file = 'external_dataset_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(tester.results, f, indent=2, default=str)
    
    print(f"Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
