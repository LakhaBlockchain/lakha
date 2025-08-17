#!/usr/bin/env python3
"""
Test API Response Format
Checks the format of API responses to understand the structure
"""

import requests
import json

def test_api_format():
    """Test API response format"""
    print("🔍 Testing API Response Format")
    print("=" * 50)
    
    node1_url = "http://localhost:5000"
    
    try:
        # Test status endpoint
        print("1️⃣ Testing /api/status endpoint...")
        status_resp = requests.get(f"{node1_url}/api/status")
        print(f"   Status code: {status_resp.status_code}")
        print(f"   Response: {json.dumps(status_resp.json(), indent=2)}")
        
        # Test pending transactions endpoint
        print("\n2️⃣ Testing /api/transactions/pending endpoint...")
        pending_resp = requests.get(f"{node1_url}/api/transactions/pending")
        print(f"   Status code: {pending_resp.status_code}")
        print(f"   Response: {json.dumps(pending_resp.json(), indent=2)}")
        
        # Test health endpoint
        print("\n3️⃣ Testing /api/health endpoint...")
        health_resp = requests.get(f"{node1_url}/api/health")
        print(f"   Status code: {health_resp.status_code}")
        print(f"   Response: {json.dumps(health_resp.json(), indent=2)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_api_format() 