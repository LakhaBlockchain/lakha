#!/usr/bin/env python3
"""
Test Genesis Nonce Fix
Tests that genesis account nonce synchronization works correctly
"""

import requests
import time
import json
from address import generate_address

def test_genesis_nonce_fix():
    """Test genesis nonce synchronization fix"""
    print("🔍 Testing Genesis Nonce Fix")
    print("=" * 50)
    
    # Test parameters
    node1_url = "http://localhost:5000"
    node2_url = "http://localhost:5001"
    node3_url = "http://localhost:5002"
    
    print("📋 Instructions:")
    print("1. Make sure your 3 nodes are running on ports 5000, 5001, 5002")
    print("2. Watch the node terminals for genesis nonce logs")
    print("3. Look for 'Genesis nonce mismatch, accepting higher nonce' messages")
    
    # Step 1: Check node health
    print("\n1️⃣ Checking node health...")
    try:
        health1 = requests.get(f"{node1_url}/api/health").json()
        health2 = requests.get(f"{node2_url}/api/health").json()
        health3 = requests.get(f"{node3_url}/api/health").json()
        print("   ✅ All nodes are healthy")
    except Exception as e:
        print(f"   ❌ Node health check failed: {e}")
        return
    
    # Step 2: Check initial genesis nonces
    print("\n2️⃣ Checking initial genesis nonces...")
    try:
        nonce1 = requests.get(f"{node1_url}/api/accounts/genesis/nonce").json()
        nonce2 = requests.get(f"{node2_url}/api/accounts/genesis/nonce").json()
        nonce3 = requests.get(f"{node3_url}/api/accounts/genesis/nonce").json()
        
        print(f"   Node 1 genesis nonce: {nonce1['data']['nonce']}")
        print(f"   Node 2 genesis nonce: {nonce2['data']['nonce']}")
        print(f"   Node 3 genesis nonce: {nonce3['data']['nonce']}")
        
        # Check if nonces are synchronized
        if nonce1['data']['nonce'] == nonce2['data']['nonce'] == nonce3['data']['nonce']:
            print("   ✅ Genesis nonces are synchronized")
        else:
            print("   ⚠️  Genesis nonces are not synchronized (this is expected initially)")
    except Exception as e:
        print(f"   ❌ Nonce check failed: {e}")
        return
    
    # Step 3: Generate test addresses
    print("\n3️⃣ Generating test addresses...")
    try:
        address1 = requests.post(f"{node1_url}/api/utils/generate-address").json()['data']['address']
        address2 = requests.post(f"{node2_url}/api/utils/generate-address").json()['data']['address']
        address3 = requests.post(f"{node3_url}/api/utils/generate-address").json()['data']['address']
        
        print(f"   Address 1: {address1}")
        print(f"   Address 2: {address2}")
        print(f"   Address 3: {address3}")
    except Exception as e:
        print(f"   ❌ Address generation failed: {e}")
        return
    
    # Step 4: Submit transaction from Node 1 (should trigger nonce sync)
    print("\n4️⃣ Submitting transaction from Node 1...")
    print("   ⚠️  WATCH YOUR NODE TERMINALS FOR GENESIS NONCE LOGS!")
    
    try:
        # Get current nonce from Node 1
        nonce_resp = requests.get(f"{node1_url}/api/accounts/genesis/nonce").json()
        current_nonce = nonce_resp['data']['nonce']
        
        tx_data = {
            "from_address": "genesis",
            "to_address": address1,
            "amount": 30.0,
            "transaction_type": "transfer",
            "gas_limit": 21000,
            "gas_price": 1.0,
            "nonce": current_nonce
        }
        
        tx_resp = requests.post(f"{node1_url}/api/transactions", json=tx_data).json()
        
        if tx_resp['status'] == 'success':
            print(f"   ✅ Transaction submitted: {tx_resp['data']['transaction_hash']}")
            print("   📡 Check your node terminals for genesis nonce synchronization logs!")
        else:
            print(f"   ❌ Transaction failed: {tx_resp}")
            return
    except Exception as e:
        print(f"   ❌ Transaction submission failed: {e}")
        return
    
    # Step 5: Wait for propagation and nonce sync
    print("\n5️⃣ Waiting for propagation and nonce sync...")
    time.sleep(3)
    
    # Step 6: Check if nonces are now synchronized
    print("\n6️⃣ Checking if genesis nonces are synchronized...")
    try:
        nonce1 = requests.get(f"{node1_url}/api/accounts/genesis/nonce").json()
        nonce2 = requests.get(f"{node2_url}/api/accounts/genesis/nonce").json()
        nonce3 = requests.get(f"{node3_url}/api/accounts/genesis/nonce").json()
        
        print(f"   Node 1 genesis nonce: {nonce1['data']['nonce']}")
        print(f"   Node 2 genesis nonce: {nonce2['data']['nonce']}")
        print(f"   Node 3 genesis nonce: {nonce3['data']['nonce']}")
        
        # Check if nonces are synchronized
        if nonce1['data']['nonce'] == nonce2['data']['nonce'] == nonce3['data']['nonce']:
            print("   ✅ Genesis nonces are now synchronized!")
        else:
            print("   ❌ Genesis nonces are still not synchronized")
    except Exception as e:
        print(f"   ❌ Nonce check failed: {e}")
        return
    
    # Step 7: Check transaction propagation
    print("\n7️⃣ Checking transaction propagation...")
    try:
        pending1 = requests.get(f"{node1_url}/api/transactions/pending").json()
        pending2 = requests.get(f"{node2_url}/api/transactions/pending").json()
        pending3 = requests.get(f"{node3_url}/api/transactions/pending").json()
        
        print(f"   Node 1 pending: {pending1['data']['count']}")
        print(f"   Node 2 pending: {pending2['data']['count']}")
        print(f"   Node 3 pending: {pending3['data']['count']}")
        
        # Check if transaction propagated
        tx_hash = tx_resp['data']['transaction_hash']
        tx_in_node2 = any(tx['hash'] == tx_hash for tx in pending2['data']['transactions'])
        tx_in_node3 = any(tx['hash'] == tx_hash for tx in pending3['data']['transactions'])
        
        print(f"   Transaction in Node 2: {tx_in_node2}")
        print(f"   Transaction in Node 3: {tx_in_node3}")
        
        if tx_in_node2 and tx_in_node3:
            print("   ✅ Transaction successfully propagated!")
        else:
            print("   ❌ Transaction did not propagate")
            
    except Exception as e:
        print(f"   ❌ Propagation check failed: {e}")
    
    # Step 8: Test submitting from Node 2 (should work now)
    print("\n8️⃣ Testing transaction submission from Node 2...")
    try:
        # Get current nonce from Node 2
        nonce_resp = requests.get(f"{node2_url}/api/accounts/genesis/nonce").json()
        current_nonce = nonce_resp['data']['nonce']
        
        tx_data = {
            "from_address": "genesis",
            "to_address": address2,
            "amount": 25.0,
            "transaction_type": "transfer",
            "gas_limit": 21000,
            "gas_price": 1.0,
            "nonce": current_nonce
        }
        
        tx_resp = requests.post(f"{node2_url}/api/transactions", json=tx_data).json()
        
        if tx_resp['status'] == 'success':
            print(f"   ✅ Transaction from Node 2 submitted: {tx_resp['data']['transaction_hash']}")
        else:
            print(f"   ❌ Transaction from Node 2 failed: {tx_resp}")
    except Exception as e:
        print(f"   ❌ Transaction submission from Node 2 failed: {e}")
    
    print("\n📝 What to look for in your node terminals:")
    print("✅ [P2P] Broadcasting transaction message to X peers")
    print("✅ [P2P] Received message: {\"type\": \"transaction\"...}")
    print("✅ [DEBUG] add_transaction: Genesis nonce mismatch, accepting higher nonce")
    print("✅ [P2P] Adding received transaction [hash]")
    
    print("\n🎉 Test completed! Check your node terminals for the logs above.")

if __name__ == "__main__":
    test_genesis_nonce_fix() 