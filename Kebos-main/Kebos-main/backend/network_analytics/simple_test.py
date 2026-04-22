#!/usr/bin/env python3
"""
Simple test script for Network Analytics models - bypasses module imports
"""

import sys
import os
from datetime import datetime
from ipaddress import IPv4Address

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_model_functionality():
    """Test basic model creation without going through module __init__.py"""
    print("🧪 Testing Network Analytics Models")
    print("=" * 50)
    
    try:
        # Import directly from models file
        from network_analytics.models import (
            NetworkFlowORM, 
            AnalyticsQueryCreate,
            TrafficPatternORM,
            NetworkAnomalyORM,
            NetworkFlowResponse,
            AnalyticsResult
        )
        print("✅ Models imported successfully")
        
        # Test NetworkFlowORM creation
        print("\n📊 Testing NetworkFlowORM...")
        flow = NetworkFlowORM(
            flow_id='test_flow_001',
            source_ip=IPv4Address('192.168.1.100'),
            destination_ip=IPv4Address('10.0.0.1'),
            source_port=12345,
            destination_port=80,
            protocol='TCP',
            direction='outbound',
            packet_count=150,
            byte_count=75000,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        print(f"✅ NetworkFlowORM created: {flow.flow_id}")
        print(f"   Source: {flow.source_ip}:{flow.source_port}")
        print(f"   Destination: {flow.destination_ip}:{flow.destination_port}")
        print(f"   Protocol: {flow.protocol}, Packets: {flow.packet_count}")
        
        # Test Pydantic schema
        print("\n📋 Testing AnalyticsQueryCreate schema...")
        from network_analytics.models import TimeRange, VisualizationType, MetricType
        
        query_data = AnalyticsQueryCreate(
            time_range=TimeRange.LAST_DAY,
            visualization_type=VisualizationType.TIME_SERIES,
            metrics=[MetricType.PACKET_COUNT, MetricType.BYTE_COUNT]
        )
        print(f"✅ AnalyticsQueryCreate schema validated: {query_data.time_range}")
        
        # Test NetworkFlowResponse
        print("\n📊 Testing NetworkFlowResponse...")
        flow_response = NetworkFlowResponse(
            id='test-uuid',
            flow_id='test_flow_003',
            source_ip='192.168.1.100',
            destination_ip='10.0.0.1',
            source_port=12345,
            destination_port=80,
            protocol='TCP',
            direction='outbound',
            packet_count=300,
            byte_count=150000,
            duration_seconds=45.5,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            source_country='US',
            destination_country='US',
            threat_score=0.2,
            anomaly_score=0.1,
            is_malicious=False
        )
        print(f"✅ NetworkFlowResponse created: {flow_response.flow_id}")
        
        # Test other models
        print("\n🔍 Testing TrafficPatternORM...")
        pattern = TrafficPatternORM(
            pattern_id='pattern_001',
            pattern_type='periodic',
            pattern_name='Daily Backup Traffic',
            confidence_score=0.95,
            first_detected=datetime.now(),
            last_detected=datetime.now()
        )
        print(f"✅ TrafficPatternORM created: {pattern.pattern_id}")
        
        print("\n⚠️  Testing NetworkAnomalyORM...")
        anomaly = NetworkAnomalyORM(
            anomaly_id='anomaly_001',
            anomaly_type='traffic_spike',
            title='Unusual Traffic Volume',
            severity_score=0.8,
            confidence_score=0.9,
            risk_level='high',
            detected_at=datetime.now()
        )
        print(f"✅ NetworkAnomalyORM created: {anomaly.anomaly_id}")
        
        print("\n" + "=" * 50)
        print("🎉 All model tests passed successfully!")
        print("✅ NetworkFlowORM: Working")
        print("✅ AnalyticsQueryCreate: Working") 
        print("✅ NetworkFlowResponse: Working")
        print("✅ TrafficPatternORM: Working")
        print("✅ NetworkAnomalyORM: Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_model_functionality()
    sys.exit(0 if success else 1)
