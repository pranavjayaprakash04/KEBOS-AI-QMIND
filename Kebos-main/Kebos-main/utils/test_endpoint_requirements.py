#!/usr/bin/env python3
"""
Quick Test: Authentication vs Ollama Requirements
Shows which endpoints work vs which need setup
"""

import requests
import json
from datetime import datetime

def test_endpoint(url, method="GET", data=None, headers=None):
    """Test an endpoint and return status info"""
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            response = requests.get(url, headers=headers, timeout=5)
        
        status_emoji = "✅" if response.status_code == 200 else "⚠️" if response.status_code < 500 else "❌"
        return f"{status_emoji} {response.status_code}", response.status_code
    except requests.exceptions.ConnectionError:
        return "🔴 Connection Error (Backend not running)", 503
    except requests.exceptions.Timeout:
        return "🔴 Timeout", 408
    except Exception as e:
        return f"❌ Error: {str(e)}", 500

def main():
    print("🧪 KEBOS Backend Endpoint Testing")
    print("=" * 50)
    print(f"Testing time: {datetime.now()}")
    print()
    
    base_url = "http://localhost:8000"
    
    print("✅ **Endpoints that work WITHOUT any setup:**")
    print("-" * 50)
    
    no_auth_endpoints = [
        ("/health", "Main application health"),
        ("/auth/auth/health", "Authentication service health"),
        ("/audit/health", "Audit logging service health"), 
        ("/assistant/health", "GenAI assistant health"),
        ("/network/network/health", "Network analytics health"),
        ("/assistant/query-types", "Available GenAI query types"),
        ("/siem/siem/types", "Available SIEM system types"),
        ("/siem/siem/auth-types", "SIEM authentication types"),
    ]
    
    for endpoint, description in no_auth_endpoints:
        status, code = test_endpoint(f"{base_url}{endpoint}")
        print(f"  {status} {endpoint}")
        print(f"      {description}")
    
    print()
    print("🔐 **Endpoints that need AUTHENTICATION:**")
    print("-" * 50)
    
    auth_endpoints = [
        ("/api/dashboard/metrics", "System dashboard metrics"),
        ("/threats/threats/", "Threat detection data"),
        ("/jobs/api/v1/jobs/health", "Job manager health"),
        ("/network/network/query", "Network analytics queries"),
        ("/siem/siem/configs", "SIEM configurations"),
    ]
    
    for endpoint, description in auth_endpoints:
        status, code = test_endpoint(f"{base_url}{endpoint}")
        print(f"  {status} {endpoint}")
        print(f"      {description}")
        if code == 401:
            print(f"      💡 Fix: Add Authorization header with valid token")
    
    print()
    print("🤖 **Endpoints that need OLLAMA (Gemma model):**")
    print("-" * 50)
    
    # Test GenAI query endpoint
    gemma_endpoint = "/assistant/query"
    test_data = {
        "query": "What is cybersecurity?",
        "query_type": "general"
    }
    status, code = test_endpoint(f"{base_url}{gemma_endpoint}", "POST", test_data)
    print(f"  {status} {gemma_endpoint}")
    print(f"      GenAI assistant query processing")
    if "Connection Error" in status:
        print(f"      💡 Fix: Start backend with 'uvicorn main:app --reload'")
    elif code in [200, 500]:  # 500 means backend is running but Ollama might not be
        print(f"      💡 Backend running, may need: 'ollama serve' and 'ollama pull gemma:2b'")
    
    print()
    print("📋 **Quick Setup Commands:**")
    print("-" * 50)
    print("🚀 Start Backend:")
    print("    cd backend")
    print("    uvicorn main:app --reload")
    print()
    print("🤖 Setup Ollama (in separate terminal):")
    print("    ollama serve")
    print("    ollama pull gemma:2b")
    print()
    print("🔐 Get Auth Token:")
    print("    curl -X POST http://localhost:8000/auth/auth/login \\")
    print("         -H 'Content-Type: application/json' \\")
    print("         -d '{\"username\": \"test\", \"password\": \"test\"}'")

if __name__ == "__main__":
    main()
