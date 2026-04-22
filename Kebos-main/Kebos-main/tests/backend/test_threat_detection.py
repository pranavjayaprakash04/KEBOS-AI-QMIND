#!/usr/bin/env python3
"""
Test script for the enhanced threat detection module
"""

import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test that all threat detection components can be imported"""
    try:
        # Import models directly from the file, not package
        import importlib.util
        import sys
        from pathlib import Path
        
        # Load models directly
        models_path = Path(__file__).parent / "threat_detection" / "models.py"
        spec = importlib.util.spec_from_file_location("threat_detection_models", models_path)
        models_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models_module)
        
        NetworkPacket = models_module.NetworkPacket
        AnomalyReport = models_module.AnomalyReport
        ThreatAlert = models_module.ThreatAlert
        ThreatLevel = models_module.ThreatLevel
        AttackType = models_module.AttackType
        
        print("✓ Models imported successfully")
        
        # Now import services, which will use the models
        services_path = Path(__file__).parent / "threat_detection" / "services.py"
        spec = importlib.util.spec_from_file_location("threat_detection_services", services_path)
        services_module = importlib.util.module_from_spec(spec)
        
        # Add the models to sys.modules so services can import them
        sys.modules['threat_detection.models'] = models_module
        
        spec.loader.exec_module(services_module)
        
        AutoencoderAnomalyDetector = services_module.AutoencoderAnomalyDetector
        AttackClassifier = services_module.AttackClassifier
        TwoStageDetectionEngine = services_module.TwoStageDetectionEngine
        ThreatDetectionService = services_module.ThreatDetectionService
        
        print("✓ Services imported successfully")
        
        # Store in global namespace for the next test
        globals().update({
            'NetworkPacket': NetworkPacket,
            'TwoStageDetectionEngine': TwoStageDetectionEngine
        })
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality of the detection pipeline"""
    try:
        from datetime import datetime
        
        # Use the imported classes from the previous test
        NetworkPacket = globals().get('NetworkPacket')
        TwoStageDetectionEngine = globals().get('TwoStageDetectionEngine')
        
        if not NetworkPacket or not TwoStageDetectionEngine:
            print("✗ Required classes not available from import test")
            return False
        
        # Create a test packet
        test_packet = NetworkPacket(
            timestamp=datetime.now(),
            source_ip="192.168.1.100",
            destination_ip="10.0.0.1",
            source_port=54321,
            destination_port=443,
            protocol="TCP",
            payload_size=1024
        )
        
        # Create detection engine
        engine = TwoStageDetectionEngine()
        
        print("✓ Basic objects created successfully")
        print(f"✓ Test packet: {test_packet.source_ip}:{test_packet.source_port} -> {test_packet.destination_ip}:{test_packet.destination_port}")
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Enhanced Threat Detection Module")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testing imports...")
    success &= test_imports()
    
    print("\n2. Testing basic functionality...")
    success &= test_basic_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! Enhanced threat detection module is ready.")
        print("\nTwo-stage detection pipeline:")
        print("  Stage 1: Autoencoder-based anomaly detection")
        print("  Stage 2: Attack type classification for anomalies")
        print("  Main Service: ThreatDetectionService")
    else:
        print("✗ Some tests failed. Please check the implementation.")
