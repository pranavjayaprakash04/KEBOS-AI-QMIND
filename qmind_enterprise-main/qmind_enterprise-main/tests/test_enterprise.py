"""
Q-MIND Enterprise: Comprehensive Test Suite

Tests cover:
- Multi-category threat detection (10 categories)
- Signal processing and decay
- Threat state evolution
- Mitigation recommendations
- Accuracy evaluation and ground truth alignment
- API integration
- Dataset adapters
"""

import unittest
import logging
from datetime import datetime, timedelta

from core.threat_state import (
    ThreatCategory, ThreatAmplitude, IndicatorSignature, ThreatState,
    SignalContribution, GroundTruthRecord, ThreatStateManager
)
from signals.threat_signals import (
    PhishingLexicalSignal, MalwareHashReputationSignal, C2TemporalSignal,
    ASNReputationSignal, CVESeveritySignal, BenignSignal, SignalWeightManager
)
from datasets.adapters import (
    PhishTankAdapter, MalwareBazaarAdapter, AbuseIPDBAdapter,
    TrancoAdapter, NVDAdapter, DatasetRegistry
)
from mitigation.recommendation_engine import (
    MitigationEngine, MitigationAction, ActionReversibility
)
from evaluation.accuracy_metrics import (
    EvaluationFramework, GroundTruth, AnalysisRecord, CategoryMetrics
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestThreatStateMultiCategory(unittest.TestCase):
    """Test threat state management across 10 categories."""
    
    def setUp(self):
        self.manager = ThreatStateManager()
    
    def test_phishing_threat_state(self):
        """Test phishing category threat state."""
        indicator = IndicatorSignature(
            indicator_type="url",
            indicator_value="http://fake-paypal.xyz",
            category=ThreatCategory.PHISHING
        )
        
        state = self.manager.get_or_create_state(indicator)
        self.assertIsNotNone(state)
        self.assertEqual(state.amplitudes["benign"], 0.8)  # Neutral assumption
        self.assertEqual(state.amplitudes["suspicious"], 0.1)
        self.assertEqual(state.amplitudes["malicious"], 0.1)
    
    def test_malware_threat_state(self):
        """Test malware category threat state."""
        indicator = IndicatorSignature(
            indicator_type="hash",
            indicator_value="d41d8cd98f00b204e9800998ecf8427e",
            category=ThreatCategory.MALWARE
        )
        
        state = self.manager.get_or_create_state(indicator)
        self.assertIsNotNone(state)
        self.assertEqual(state.category, ThreatCategory.MALWARE)
    
    def test_all_10_categories(self):
        """Verify all 10 threat categories are supported."""
        expected_categories = [
            ThreatCategory.PHISHING,
            ThreatCategory.MALWARE,
            ThreatCategory.C2_INFRASTRUCTURE,
            ThreatCategory.BOTNET_IP,
            ThreatCategory.CREDENTIAL_LEAK,
            ThreatCategory.SUPPLY_CHAIN,
            ThreatCategory.INSIDER_THREAT,
            ThreatCategory.DDOS,
            ThreatCategory.VULNERABILITY,
            ThreatCategory.BENIGN,
        ]
        
        self.assertEqual(len(ThreatCategory), len(expected_categories))
        for category in expected_categories:
            self.assertIn(category, ThreatCategory)


class TestSignalProcessing(unittest.TestCase):
    """Test signal types and processing for different categories."""
    
    def test_phishing_lexical_signal(self):
        """Test phishing lexical analysis signal."""
        signal = PhishingLexicalSignal(
            url="http://paypal-update.com",
            entropy=3.5,
            special_char_count=2
        )
        
        self.assertEqual(signal.signal_type.value, "lexical")
        self.assertGreater(signal.strength, 0)
        self.assertEqual(signal.confidence, 0.75)
    
    def test_malware_hash_signal(self):
        """Test malware hash reputation signal."""
        signal = MalwareHashReputationSignal(
            file_hash="abc123",
            av_hits=45,
            total_scanners=70
        )
        
        self.assertEqual(signal.signal_type.value, "hash_reputation")
        self.assertGreater(signal.strength, 0.6)  # 45/70 = ~0.64
        self.assertGreater(signal.confidence, 0.8)
    
    def test_c2_temporal_signal(self):
        """Test C2 infrastructure temporal signal."""
        signal = C2TemporalSignal(
            ip_or_domain="192.0.2.1",
            request_rate=75.0,
            off_hours_activity=True
        )
        
        self.assertEqual(signal.signal_type.value, "temporal")
        self.assertGreater(signal.strength, 0.7)
    
    def test_signal_weight_management(self):
        """Test dynamic signal weighting."""
        manager = SignalWeightManager()
        
        # Initial weight
        initial = manager.get_weight(signal_type=signal := __import__(
            'signals.threat_signals', fromlist=['SignalType']).SignalType.LEXICAL)
        self.assertEqual(initial, 1.0)
        
        # Boost weight
        manager.boost_weight(signal)
        boosted = manager.get_weight(signal)
        self.assertGreater(boosted, 1.0)
        
        # Penalize weight
        manager.penalize_weight(signal)
        penalized = manager.get_weight(signal)
        self.assertLess(penalized, boosted)


class TestDatasetAdapters(unittest.TestCase):
    """Test dataset adapter implementations."""
    
    def test_phishtank_adapter(self):
        """Test PhishTank adapter."""
        adapter = PhishTankAdapter()
        results = adapter.fetch_and_normalize()
        
        self.assertGreater(len(results), 0)
        for indicator, signal in results:
            self.assertEqual(indicator.category, ThreatCategory.PHISHING)
            self.assertIsNotNone(signal)
    
    def test_malwarebazaar_adapter(self):
        """Test MalwareBazaar adapter."""
        adapter = MalwareBazaarAdapter()
        results = adapter.fetch_and_normalize()
        
        self.assertGreater(len(results), 0)
        for indicator, signal in results:
            self.assertEqual(indicator.category, ThreatCategory.MALWARE)
    
    def test_abuseipdb_adapter(self):
        """Test AbuseIPDB adapter."""
        adapter = AbuseIPDBAdapter()
        results = adapter.fetch_and_normalize()
        
        self.assertGreater(len(results), 0)
        for indicator, signal in results:
            self.assertIn(indicator.category, [
                ThreatCategory.BOTNET_IP,
                ThreatCategory.C2_INFRASTRUCTURE
            ])
    
    def test_tranco_adapter(self):
        """Test Tranco benign domain adapter."""
        adapter = TrancoAdapter()
        results = adapter.fetch_and_normalize()
        
        self.assertGreater(len(results), 0)
        for indicator, signal in results:
            self.assertEqual(indicator.category, ThreatCategory.BENIGN)
    
    def test_nvd_adapter(self):
        """Test NVD vulnerability adapter."""
        adapter = NVDAdapter()
        results = adapter.fetch_and_normalize()
        
        self.assertGreater(len(results), 0)
        for indicator, signal in results:
            self.assertEqual(indicator.category, ThreatCategory.VULNERABILITY)
    
    def test_dataset_registry(self):
        """Test dataset registry."""
        registry = DatasetRegistry()
        
        # Check all adapters registered
        adapters = registry.list_adapters()
        expected = ["PhishTank", "OpenPhish", "MalwareBazaar", "AbuseIPDB",
                   "Tranco", "NVD", "FeodoTracker"]
        for expected_adapter in expected:
            self.assertIn(expected_adapter, adapters)


class TestMitigationEngine(unittest.TestCase):
    """Test mitigation recommendation generation."""
    
    def setUp(self):
        self.engine = MitigationEngine()
        self.manager = ThreatStateManager()
    
    def test_phishing_recommendations(self):
        """Test phishing mitigation recommendations."""
        indicator = IndicatorSignature(
            indicator_type="url",
            indicator_value="http://phishing.com",
            category=ThreatCategory.PHISHING
        )
        
        threat_state = self.manager.get_or_create_state(indicator)
        
        # Add signal to raise threat level
        signal = PhishingLexicalSignal(
            url="http://phishing.com",
            entropy=4.0,
            special_char_count=5
        )
        threat_state.add_signal(signal)
        
        # Generate recommendations
        plan = self.engine.generate_recommendations(indicator, threat_state)
        
        self.assertIsNotNone(plan.primary_recommendation)
        self.assertEqual(plan.primary_recommendation.action, MitigationAction.BLOCK_URL)
        self.assertGreater(len(plan.secondary_recommendations), 0)
    
    def test_malware_recommendations(self):
        """Test malware mitigation recommendations."""
        indicator = IndicatorSignature(
            indicator_type="hash",
            indicator_value="abc123",
            category=ThreatCategory.MALWARE
        )
        
        threat_state = self.manager.get_or_create_state(indicator)
        signal = MalwareHashReputationSignal(
            file_hash="abc123",
            av_hits=60,
            total_scanners=70
        )
        threat_state.add_signal(signal)
        
        plan = self.engine.generate_recommendations(indicator, threat_state)
        
        self.assertEqual(plan.primary_recommendation.action, MitigationAction.BLOCK_HASH)
    
    def test_recommendation_reversibility_tracking(self):
        """Test that reversibility is properly classified."""
        indicator = IndicatorSignature(
            indicator_type="cve",
            indicator_value="CVE-2024-0001",
            category=ThreatCategory.VULNERABILITY
        )
        
        threat_state = self.manager.get_or_create_state(indicator)
        signal = CVESeveritySignal(
            cve_id="CVE-2024-0001",
            cvss_score=9.8,
            exploits_public=1
        )
        threat_state.add_signal(signal)
        
        plan = self.engine.generate_recommendations(indicator, threat_state)
        
        # Patching should be marked reversible with effort
        primary = plan.primary_recommendation
        self.assertIn(
            primary.reversibility,
            [ActionReversibility.FULLY_REVERSIBLE,
             ActionReversibility.REVERSIBLE_WITH_EFFORT]
        )


class TestEvaluationFramework(unittest.TestCase):
    """Test accuracy evaluation and metrics."""
    
    def setUp(self):
        self.framework = EvaluationFramework()
        self.manager = ThreatStateManager()
    
    def test_true_positive_detection(self):
        """Test true positive classification."""
        indicator = IndicatorSignature(
            indicator_type="url",
            indicator_value="http://phishing.com",
            category=ThreatCategory.PHISHING
        )
        
        threat_state = self.manager.get_or_create_state(indicator)
        
        # Predict high threat
        record = self.framework.record_analysis(
            indicator=indicator,
            threat_state=threat_state,
            predicted_threat_level="high",
            predicted_confidence=0.85,
            ground_truth=GroundTruth.MALICIOUS
        )
        
        self.assertTrue(record.is_true_positive())
    
    def test_false_positive_detection(self):
        """Test false positive classification."""
        indicator = IndicatorSignature(
            indicator_type="domain",
            indicator_value="google.com",
            category=ThreatCategory.BENIGN
        )
        
        threat_state = self.manager.get_or_create_state(indicator)
        
        # Predict high threat (wrong)
        record = self.framework.record_analysis(
            indicator=indicator,
            threat_state=threat_state,
            predicted_threat_level="high",
            predicted_confidence=0.75,
            ground_truth=GroundTruth.BENIGN
        )
        
        self.assertTrue(record.is_false_positive())
    
    def test_category_metrics_calculation(self):
        """Test per-category metrics."""
        indicator1 = IndicatorSignature(
            indicator_type="url",
            indicator_value="phishing1.com",
            category=ThreatCategory.PHISHING
        )
        
        threat_state1 = self.manager.get_or_create_state(indicator1)
        
        # Record 10 TP and 2 FP for phishing category
        for i in range(10):
            self.framework.record_analysis(
                indicator=indicator1,
                threat_state=threat_state1,
                predicted_threat_level="high",
                predicted_confidence=0.85,
                ground_truth=GroundTruth.MALICIOUS
            )
        
        for i in range(2):
            self.framework.record_analysis(
                indicator=indicator1,
                threat_state=threat_state1,
                predicted_threat_level="high",
                predicted_confidence=0.85,
                ground_truth=GroundTruth.BENIGN
            )
        
        metrics = self.framework.get_category_metrics(ThreatCategory.PHISHING)
        self.assertEqual(metrics.true_positives, 10)
        self.assertEqual(metrics.false_positives, 2)
        
        # Precision = 10 / (10 + 2) = 0.833
        self.assertAlmostEqual(metrics.precision(), 10/12, places=2)
    
    def test_aggregate_metrics(self):
        """Test system-wide metrics."""
        # Create mixed indicators across categories
        categories = [
            (ThreatCategory.PHISHING, "url", "phishing.com"),
            (ThreatCategory.MALWARE, "hash", "abc123"),
            (ThreatCategory.VULNERABILITY, "cve", "CVE-2024-0001"),
        ]
        
        for category, ind_type, ind_value in categories:
            indicator = IndicatorSignature(
                indicator_type=ind_type,
                indicator_value=ind_value,
                category=category
            )
            
            threat_state = self.manager.get_or_create_state(indicator)
            
            # Record 5 TP per category
            for i in range(5):
                self.framework.record_analysis(
                    indicator=indicator,
                    threat_state=threat_state,
                    predicted_threat_level="high",
                    predicted_confidence=0.85,
                    ground_truth=GroundTruth.MALICIOUS
                )
        
        agg = self.framework.get_aggregate_metrics()
        self.assertEqual(agg.global_tp, 15)
        self.assertGreater(agg.f1_score(), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for full pipeline."""
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline from indicator to recommendation."""
        
        # Setup components
        manager = ThreatStateManager()
        engine = MitigationEngine()
        eval_fw = EvaluationFramework()
        
        # Create phishing indicator
        indicator = IndicatorSignature(
            indicator_type="url",
            indicator_value="http://fake-amazon.xyz",
            category=ThreatCategory.PHISHING
        )
        
        # Get threat state
        threat_state = manager.get_or_create_state(indicator)
        
        # Add signal
        signal = PhishingLexicalSignal(
            url="http://fake-amazon.xyz",
            entropy=4.5,
            special_char_count=4
        )
        threat_state.add_signal(signal)
        
        # Measure
        decision = threat_state.measure()
        self.assertIn("threat_level", decision)
        self.assertIn("confidence", decision)
        
        # Generate recommendation
        plan = engine.generate_recommendations(indicator, threat_state)
        self.assertIsNotNone(plan.primary_recommendation)
        
        # Record for evaluation
        record = eval_fw.record_analysis(
            indicator=indicator,
            threat_state=threat_state,
            predicted_threat_level=decision["threat_level"],
            predicted_confidence=decision["confidence"],
            ground_truth=GroundTruth.MALICIOUS  # Actual outcome
        )
        
        self.assertTrue(record.is_true_positive())


def run_all_tests():
    """Run complete test suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestThreatStateMultiCategory))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestDatasetAdapters))
    suite.addTests(loader.loadTestsFromTestCase(TestMitigationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestEvaluationFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUITE SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
