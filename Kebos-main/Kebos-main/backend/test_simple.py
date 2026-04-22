#!/usr/bin/env python3
"""
Simple test script using only built-in Python libraries to test API endpoints.
"""
import json
import urllib.request
import urllib.parse
import time

BASE_URL = "http://localhost:8001"

def test_get(endpoint):
    """Test a GET endpoint."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing GET {endpoint}")
    print(f"{'='*60}")
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = response.read()
            result = json.loads(data.decode('utf-8'))
            print(f"Status: {response.status}")
            print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_post(endpoint, payload):
    """Test a POST endpoint."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing POST {endpoint}")
    print(f"{'='*60}")
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            response_data = response.read()
            result = json.loads(response_data.decode('utf-8'))
            print(f"Status: {response.status}")
            print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Test CatBoost API endpoints."""
    print("CatBoost API Test Suite (using built-in libraries)")
    print("Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    
    # Test health endpoint
    test_get("/health")
    
    # Test CatBoost status endpoint
    test_get("/threat/catboost-status")
    
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
    
    test_post("/threat/detect-catboost", sample_packet)
    
    # Test with a potentially suspicious packet
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
    
    test_post("/threat/detect-catboost", suspicious_packet)

if __name__ == "__main__":
    main()
