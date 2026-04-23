#!/usr/bin/env python3
"""
Q-MIND Enterprise: Execute Large-Scale External Dataset Testing

This master script:
1. Validates environment
2. Downloads 1M+ real threat intelligence records
3. Tests Q-MIND Enterprise comprehensively
4. Generates detailed performance report
5. Exports results for analysis
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def check_environment():
    """Check if Python environment is properly configured."""
    print("\n[ENVIRONMENT CHECK]")
    print("-" * 80)
    
    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"✓ Python version: {py_version}")
    
    # Check required packages
    required_packages = [
        'requests', 'numpy', 'pandas', 'fastapi', 'uvicorn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def run_external_dataset_tests():
    """Run comprehensive external dataset testing."""
    
    print("\n[RUNNING COMPREHENSIVE EXTERNAL DATASET TESTS]")
    print("-" * 80)
    
    try:
        # Import and run tester
        sys.path.insert(0, os.getcwd())
        
        from run_external_dataset_tests import LargeScaleExternalTester
        
        tester = LargeScaleExternalTester()
        
        # Run test with large scale
        print("\nInitiating large-scale external dataset testing...")
        print("This will analyze 1M+ real threat intelligence records")
        
        start_time = time.time()
        report = tester.test_external_datasets(scale='large')
        total_time = time.time() - start_time
        
        # Print report
        print(report)
        
        # Save results
        report_file = 'EXTERNAL_DATASET_TEST_RESULTS.txt'
        with open(report_file, 'w') as f:
            f.write(report)
            f.write(f"\n\nTotal execution time: {total_time:.2f}s\n")
        
        print(f"\n✓ Report saved to: {report_file}")
        
        # Save JSON results
        import json
        results_file = 'external_dataset_test_results.json'
        with open(results_file, 'w') as f:
            json.dump(tester.results, f, indent=2, default=str)
        
        print(f"✓ Detailed results saved to: {results_file}")
        
        return True
    
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_summary():
    """Print summary of testing."""
    
    print("\n" + "="*80)
    print("Q-MIND ENTERPRISE EXTERNAL DATASET TESTING COMPLETE")
    print("="*80)
    
    print("\nGenerated Files:")
    files = [
        ('EXTERNAL_DATASET_TEST_RESULTS.txt', 'Human-readable test report'),
        ('external_dataset_test_results.json', 'Detailed results in JSON format'),
        ('dataset_cache/', 'Cached threat intelligence datasets'),
    ]
    
    for filename, description in files:
        if os.path.exists(filename):
            print(f"  ✓ {filename:<40} - {description}")
        else:
            print(f"  ? {filename:<40} - {description}")
    
    print("\nNext Steps:")
    print("  1. Review test results in EXTERNAL_DATASET_TEST_RESULTS.txt")
    print("  2. Analyze detailed metrics in external_dataset_test_results.json")
    print("  3. Check dataset_cache/ for downloaded threat intelligence")
    print("  4. Use results for production deployment planning")

def main():
    """Main execution."""
    
    print("\n" + "="*80)
    print("Q-MIND ENTERPRISE: EXTERNAL DATASET TESTING FRAMEWORK")
    print("Version 1.0.0 | Large-Scale Threat Intelligence Validation")
    print("="*80)
    
    # Check environment
    if not check_environment():
        print("\n✗ Environment check failed")
        return 1
    
    # Run tests
    if not run_external_dataset_tests():
        print("\n✗ Testing failed")
        return 1
    
    # Print summary
    print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
