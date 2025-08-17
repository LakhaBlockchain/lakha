#!/usr/bin/env python3
"""
Test API Broadcast Fix
Tests that the API broadcasting fix works correctly
"""

import requests
import time
import json
from address import generate_address

def test_api_broadcast():
    """Test API broadcasting with the fix"""
    print("🔍 Testing API Broadcast Fix")
    print("=" * 50)
    
    # Test parameters
    node1_url = "http://localhost:5000"
    node2_url = "http://localhost:5001"
    node3_url = "http://localhost:5002"
    
    print("📋 Instructions:")
    print("1. Make sure your 3 nodes are running on ports 5000, 5001, 5002")
    print("2. Watch the node terminals for P2P broadcast logs")
    print("3. Look for '[P2P] Broadcasting transaction' messages")
    
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
    
    # Step 2: Check P2P status
    print("\n2️⃣ Checking P2P status...")
    try:
        p2p1 = requests.get(f"{node1_url}/api/p2p/status").json()
        p2p2 = requests.get(f"{node2_url}/api/p2p/status").json()
        p2p3 = requests.get(f"{node3_url}/api/p2p/status").json()
        
        print(f"   Node 1: {p2p1['data']['connections']} connections")
        print(f"   Node 2: {p2p2['data']['connections']} connections")
        print(f"   Node 3: {p2p3['data']['connections']} connections")
        
        if p2p1['data']['connections'] > 0 and p2p2['data']['connections'] > 0 and p2p3['data']['connections'] > 0:
            print("   ✅ P2P connections are active")
        else:
            print("   ⚠️  Some nodes have no P2P connections")
    except Exception as e:
        print(f"   ❌ P2P status check failed: {e}")
        return
    
    # Step 3: Generate address
    print("\n3️⃣ Generating test address...")
    try:
        address_resp = requests.post(f"{node1_url}/api/utils/generate-address").json()
        address = address_resp['data']['address']
        print(f"   Address: {address}")
    except Exception as e:
        print(f"   ❌ Address generation failed: {e}")
        return
    
    # Step 4: Get genesis nonce
    print("\n4️⃣ Getting genesis nonce...")
    try:
        nonce_resp = requests.get(f"{node1_url}/api/accounts/genesis/nonce").json()
        nonce = nonce_resp['data']['nonce']
        print(f"   Genesis nonce: {nonce}")
    except Exception as e:
        print(f"   ❌ Nonce retrieval failed: {e}")
        return
    
    # Step 5: Submit transaction (should trigger broadcast)
    print("\n5️⃣ Submitting transaction (should trigger broadcast)...")
    print("   ⚠️  WATCH YOUR NODE TERMINALS FOR P2P LOGS!")
    
    try:
        tx_data = {
            "from_address": "genesis",
            "to_address": address,
            "amount": 25.0,
            "transaction_type": "transfer",
            "gas_limit": 21000,
            "gas_price": 1.0,
            "nonce": nonce
        }
        
        tx_resp = requests.post(f"{node1_url}/api/transactions", json=tx_data).json()
        
        if tx_resp['status'] == 'success':
            print(f"   ✅ Transaction submitted: {tx_resp['data']['transaction_hash']}")
            print("   📡 Check your node terminals for P2P broadcast logs!")
        else:
            print(f"   ❌ Transaction failed: {tx_resp}")
    except Exception as e:
        print(f"   ❌ Transaction submission failed: {e}")
        return
    
    # Step 6: Wait and check propagation
    print("\n6️⃣ Waiting for propagation...")
    time.sleep(3)
    
    # Step 7: Check pending transactions on all nodes
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
    
    print("\n📝 What to look for in your node terminals:")
    print("✅ [P2P] Broadcasting transaction message to X peers")
    print("✅ [P2P] Successfully sent transaction message to peer")
    print("✅ [P2P] Broadcast completed: X/X messages sent")
    print("✅ [P2P] Received message: {\"type\": \"transaction\"...}")
    print("✅ [P2P] Adding received transaction [hash]")
    
    print("\n🎉 Test completed! Check your node terminals for the P2P logs above.")

if __name__ == "__main__":
    test_api_broadcast() 