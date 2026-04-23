#!/usr/bin/env python3
"""
Q-MIND Enterprise: Main Orchestration Script

Demonstrates complete end-to-end workflow:
1. Ingest threat data from 7 sources
2. Apply threat signals (10 categories)
3. Generate threat assessments
4. Provide mitigation recommendations
5. Track accuracy with ground truth
6. Evaluate system performance

Usage:
    python run_enterprise.py --mode demo
    python run_enterprise.py --mode api
    python run_enterprise.py --mode test
"""

import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import core components
from core.threat_state import (
    ThreatCategory, IndicatorSignature, ThreatState, ThreatStateManager
)
from signals.threat_signals import SignalWeightManager
from datasets.adapters import DatasetRegistry
from mitigation.recommendation_engine import MitigationEngine
from evaluation.accuracy_metrics import EvaluationFramework, GroundTruth


class Q_MIND_Enterprise_Orchestrator:
    """
    Main orchestration class for enterprise platform.
    
    Coordinates all components: datasets, signals, threat detection,
    mitigation recommendations, and accuracy evaluation.
    """
    
    def __init__(self):
        """Initialize all enterprise components."""
        logger.info("Initializing Q-MIND Enterprise Platform...")
        
        self.threat_state_manager = ThreatStateManager()
        self.signal_weight_manager = SignalWeightManager()
        self.dataset_registry = DatasetRegistry()
        self.mitigation_engine = MitigationEngine()
        self.evaluation_framework = EvaluationFramework()
        
        self.analysis_count = 0
        self.recommendation_count = 0
        
        logger.info("Q-MIND Enterprise Platform initialized successfully")
    
    def demo_mode(self):
        """
        Demonstration mode: Full workflow example.
        
        Shows:
        1. Dataset ingestion
        2. Threat analysis
        3. Mitigation recommendations
        4. Accuracy evaluation
        """
        
        logger.info("="*70)
        logger.info("Q-MIND ENTERPRISE DEMONSTRATION")
        logger.info("="*70)
        
        # Step 1: Ingest threat data from all sources
        logger.info("\n[STEP 1] INGESTING THREAT DATA FROM 7 SOURCES")
        logger.info("-" * 70)
        
        all_indicators = []
        dataset_results = self.dataset_registry.fetch_all()
        
        for adapter_name, normalized_data in dataset_results.items():
            logger.info(f"  {adapter_name}: {len(normalized_data)} indicators")
            all_indicators.extend(normalized_data)
        
        logger.info(f"\nTotal indicators ingested: {len(all_indicators)}")
        
        # Step 2: Analyze threats
        logger.info("\n[STEP 2] ANALYZING THREATS")
        logger.info("-" * 70)
        
        analysis_results = []
        
        for i, (indicator, signal) in enumerate(all_indicators[:15]):  # Demo first 15
            # Get or create threat state
            threat_state = self.threat_state_manager.get_or_create_state(indicator)
            
            # Add signal
            threat_state.add_signal(signal)
            
            # Measure threat
            decision = threat_state.measure()
            
            self.analysis_count += 1
            analysis_results.append({
                'indicator': indicator,
                'threat_state': threat_state,
                'decision': decision,
                'signal': signal
            })
            
            threat_level = decision.get('threat_level', 'minimal')
            confidence = decision.get('confidence', 0.0)
            
            logger.info(f"  [{i+1}] {indicator.category.value:20} "
                       f"{threat_level:10} (conf={confidence:.2f}) "
                       f"{indicator.indicator_value[:30]}...")
        
        # Step 3: Generate recommendations
        logger.info("\n[STEP 3] GENERATING MITIGATION RECOMMENDATIONS")
        logger.info("-" * 70)
        
        for result in analysis_results:
            plan = self.mitigation_engine.generate_recommendations(
                indicator=result['indicator'],
                threat_state=result['threat_state']
            )
            
            self.recommendation_count += 1
            
            primary = plan.primary_recommendation
            logger.info(f"  {plan.plan_id}: {primary.action.value:20} "
                       f"Priority={primary.priority} "
                       f"Reversible={primary.reversibility.value}")
        
        # Step 4: Evaluate accuracy
        logger.info("\n[STEP 4] RECORDING GROUND TRUTH & EVALUATING ACCURACY")
        logger.info("-" * 70)
        
        # Simulate ground truth feedback
        for i, result in enumerate(analysis_results):
            # Assume 80% of high/medium threat predictions are correct
            decision = result['decision']
            threat_level = decision.get('threat_level', 'minimal')
            
            if threat_level in ['high', 'medium'] and i % 5 != 0:
                ground_truth = GroundTruth.MALICIOUS  # Correct
            else:
                ground_truth = GroundTruth.BENIGN  # To diversify
            
            # Record analysis
            self.evaluation_framework.record_analysis(
                indicator=result['indicator'],
                threat_state=result['threat_state'],
                predicted_threat_level=threat_level,
                predicted_confidence=decision.get('confidence', 0.5),
                ground_truth=ground_truth,
                prediction_lead_time_hours=decision.get('lead_time_hours', 0)
            )
        
        # Get metrics
        agg = self.evaluation_framework.get_aggregate_metrics()
        
        logger.info(f"  Precision: {agg.precision():.4f}")
        logger.info(f"  Recall: {agg.recall():.4f}")
        logger.info(f"  F1-Score: {agg.f1_score():.4f}")
        logger.info(f"  Accuracy: {agg.accuracy():.4f}")
        
        # Step 5: Summary
        logger.info("\n[STEP 5] ENTERPRISE PLATFORM SUMMARY")
        logger.info("-" * 70)
        logger.info(f"  Total Indicators Analyzed: {self.analysis_count}")
        logger.info(f"  Total Recommendations: {self.recommendation_count}")
        logger.info(f"  Threat Categories Covered: 10")
        logger.info(f"  Data Sources Active: 7")
        logger.info(f"  Global F1-Score: {agg.f1_score():.4f}")
        
        logger.info("\n" + "="*70)
        logger.info("DEMONSTRATION COMPLETE")
        logger.info("="*70)
    
    def api_mode(self):
        """
        API mode: Start the FastAPI server.
        
        Serves the enterprise threat intelligence API.
        """
        logger.info("Starting Q-MIND Enterprise API Server...")
        logger.info("="*70)
        
        try:
            from api.enterprise_api import create_api
            import uvicorn
            
            app = create_api()
            
            logger.info("API Server Configuration:")
            logger.info("  Host: 0.0.0.0")
            logger.info("  Port: 8000")
            logger.info("  Reload: True")
            logger.info("\nAvailable Endpoints:")
            logger.info("  POST /analyze - Analyze threat indicator")
            logger.info("  POST /recommend - Get mitigation recommendations")
            logger.info("  POST /feedback - Submit ground truth feedback")
            logger.info("  GET /metrics - System accuracy metrics")
            logger.info("  GET /health - Health check")
            logger.info("\nStarting server...")
            
            uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
        
        except ImportError as e:
            logger.error(f"Failed to import API module: {e}")
            logger.info("Install FastAPI: pip install fastapi uvicorn")
            sys.exit(1)
    
    def test_mode(self):
        """Test mode: Run test suite."""
        logger.info("Running Q-MIND Enterprise Test Suite...")
        logger.info("="*70)
        
        try:
            from tests.test_enterprise import run_all_tests
            success = run_all_tests()
            sys.exit(0 if success else 1)
        except ImportError as e:
            logger.error(f"Failed to import test module: {e}")
            sys.exit(1)
    
    def benchmark_mode(self):
        """Benchmark mode: Performance testing."""
        logger.info("Running Q-MIND Enterprise Benchmark...")
        logger.info("="*70)
        
        import time
        
        # Benchmark 1: Dataset ingestion speed
        logger.info("\n[BENCHMARK 1] Dataset Ingestion Speed")
        start = time.time()
        results = self.dataset_registry.fetch_all()
        total_records = sum(len(v) for v in results.values())
        elapsed = time.time() - start
        
        logger.info(f"  Total records: {total_records}")
        logger.info(f"  Time: {elapsed:.2f} seconds")
        logger.info(f"  Rate: {total_records/elapsed:.0f} records/sec")
        
        # Benchmark 2: Threat analysis speed
        logger.info("\n[BENCHMARK 2] Threat Analysis Speed")
        start = time.time()
        count = 0
        
        for indicators in results.values():
            for indicator, signal in indicators:
                threat_state = self.threat_state_manager.get_or_create_state(indicator)
                threat_state.add_signal(signal)
                decision = threat_state.measure()
                count += 1
        
        elapsed = time.time() - start
        logger.info(f"  Total analyses: {count}")
        logger.info(f"  Time: {elapsed:.2f} seconds")
        logger.info(f"  Rate: {count/elapsed:.0f} analyses/sec")
        
        # Benchmark 3: Recommendation generation
        logger.info("\n[BENCHMARK 3] Recommendation Generation Speed")
        start = time.time()
        recs = 0
        
        for indicators in results.values():
            for indicator, signal in indicators[:5]:  # Sample to keep demo fast
                threat_state = self.threat_state_manager.get_or_create_state(indicator)
                threat_state.add_signal(signal)
                plan = self.mitigation_engine.generate_recommendations(
                    indicator, threat_state
                )
                recs += 1
        
        elapsed = time.time() - start
        logger.info(f"  Total recommendations: {recs}")
        logger.info(f"  Time: {elapsed:.2f} seconds")
        logger.info(f"  Rate: {recs/elapsed:.0f} recommendations/sec")
        
        logger.info("\n" + "="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Q-MIND Enterprise: Unified Threat Intelligence Platform"
    )
    
    parser.add_argument(
        '--mode',
        choices=['demo', 'api', 'test', 'benchmark'],
        default='demo',
        help='Execution mode'
    )
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = Q_MIND_Enterprise_Orchestrator()
    
    # Run selected mode
    if args.mode == 'demo':
        orchestrator.demo_mode()
    elif args.mode == 'api':
        orchestrator.api_mode()
    elif args.mode == 'test':
        orchestrator.test_mode()
    elif args.mode == 'benchmark':
        orchestrator.benchmark_mode()


if __name__ == "__main__":
    main()
