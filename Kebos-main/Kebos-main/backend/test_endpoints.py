#!/usr/bin/env python3
"""
Test script to verify CatBoost API endpoints work correctly.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint and print the results."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def main():
    """Test all CatBoost API endpoints."""
    print("CatBoost API Test Suite")
    print("Waiting 2 seconds for server to start...")
    time.sleep(2)
    
    # Test health endpoint
    test_endpoint("/health")
    
    # Test CatBoost status endpoint
    test_endpoint("/threat/catboost-status")
    
    # Test threat detection with sample packet
    sample_packet = {
        "source_ip": "192.168.1.100",
        "dest_ip": "192.168.1.1",
        "source_port": 12345,
        "dest_port": 80,
        "protocol": "TCP",
        "packet_size": 1024,
        "flags": ["SYN"],
        "payload": "GET / HTTP/1.1"
    }
    
    test_endpoint("/threat/detect-catboost", "POST", sample_packet)
    
    # Test with different packet
    suspicious_packet = {
        "source_ip": "10.0.0.100", 
        "dest_ip": "192.168.1.10",
        "source_port": 8080,
        "dest_port": 22,
        "protocol": "TCP",
        "packet_size": 65535,
        "flags": ["SYN", "ACK", "FIN"],
        "payload": "AAAA" * 100
    }
    
    test_endpoint("/threat/detect-catboost", "POST", suspicious_packet)

if __name__ == "__main__":
    main()
