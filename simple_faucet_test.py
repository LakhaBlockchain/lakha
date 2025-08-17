#!/usr/bin/env python3
"""
Simple Faucet Test
"""

import requests
import json

API_URL = 'http://localhost:5000'

def test_faucet_step_by_step():
    """Test faucet step by step"""
    print("🧪 Simple Faucet Test")
    print("=" * 30)
    
    # Test address
    test_address = "lakha1nmrwxp97kq6qeqsgrfy84zpsvn9afndn0472jh"
    
    # Step 1: Check if address is valid
    print(f"\n1️⃣ Validating address: {test_address}")
    validate_data = {'address': test_address}
    try:
        response = requests.post(f"{API_URL}/api/utils/validate-address", json=validate_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 2: Try faucet with minimal data
    print(f"\n2️⃣ Testing faucet...")
    faucet_data = {
        'address': test_address,
        'amount': 100.0
    }
    
    try:
        response = requests.post(f"{API_URL}/api/faucet", json=faucet_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['data']['message']}")
        else:
            print(f"   ❌ Failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 3: Check pending transactions
    print(f"\n3️⃣ Checking pending transactions...")
    try:
        response = requests.get(f"{API_URL}/api/transactions/pending")
        if response.status_code == 200:
            data = response.json()
            count = data['data']['count']
            print(f"   📊 Pending: {count}")
            if count > 0:
                for tx in data['data']['transactions']:
                    print(f"     - {tx['from_address']} → {tx['to_address']}: {tx['amount']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == '__main__':
    test_faucet_step_by_step() 