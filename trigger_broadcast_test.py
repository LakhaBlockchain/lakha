#!/usr/bin/env python3
"""
Trigger Broadcast Test
Simple test to trigger P2P broadcasting and see what happens
"""

import requests
import time
import json

def test_broadcast_trigger():
    """Test to trigger P2P broadcasting"""
    print("🔍 Triggering P2P Broadcast Test")
    print("=" * 40)
    
    print("\n📋 Instructions:")
    print("1. Watch your node terminals for P2P broadcast logs")
    print("2. Look for messages starting with '[P2P]'")
    print("3. Check if transactions propagate between nodes")
    print()
    
    # Step 1: Generate address
    print("1️⃣ Generating address...")
    response = requests.post('http://localhost:5000/api/utils/generate-address')
    if response.status_code != 200:
        print("❌ Failed to generate address")
        return
    
    address = response.json()['data']['address']
    print(f"   Address: {address}")
    
    # Step 2: Get genesis nonce
    print("\n2️⃣ Getting genesis nonce...")
    nonce_response = requests.get('http://localhost:5000/api/accounts/genesis/nonce')
    if nonce_response.status_code == 200:
        nonce = nonce_response.json()['data']['nonce']
        print(f"   Genesis nonce: {nonce}")
    else:
        nonce = 0
        print(f"   Using default nonce: {nonce}")
    
    # Step 3: Submit transaction (this should trigger broadcast)
    print("\n3️⃣ Submitting transaction (should trigger broadcast)...")
    print("   ⚠️  WATCH YOUR NODE TERMINALS FOR P2P LOGS!")
    
    tx_data = {
        'from_address': 'genesis',
        'to_address': address,
        'amount': 25.0,
        'transaction_type': 'transfer',
        'gas_limit': 21000,
        'gas_price': 1.0,
        'nonce': nonce
    }
    
    response = requests.post('http://localhost:5000/api/transactions', json=tx_data)
    if response.status_code == 200:
        tx_hash = response.json()['data']['transaction_hash']
        print(f"   ✅ Transaction submitted: {tx_hash[:16]}...")
        print("   📡 Broadcasting should have been triggered!")
    else:
        print(f"   ❌ Transaction failed: {response.text}")
        return
    
    # Step 4: Wait and check propagation
    print("\n4️⃣ Waiting for broadcast propagation...")
    time.sleep(2)
    
    print("   Checking transaction propagation:")
    nodes = [
        ('Node 1', 'http://localhost:5000'),
        ('Node 2', 'http://localhost:5001'),
        ('Node 3', 'http://localhost:5002')
    ]
    
    for node_name, url in nodes:
        try:
            response = requests.get(f'{url}/api/transactions/pending')
            if response.status_code == 200:
                pending_txs = response.json()['data']['transactions']
                found = any(tx['hash'] == tx_hash for tx in pending_txs)
                status = "✅ Found" if found else "❌ Not found"
                print(f"   {node_name}: {status} ({len(pending_txs)} pending)")
            else:
                print(f"   {node_name}: ❌ Error - {response.status_code}")
        except Exception as e:
            print(f"   {node_name}: ❌ Exception - {e}")
    
    # Step 5: Check P2P status
    print("\n5️⃣ Checking P2P connection status:")
    for node_name, url in nodes:
        try:
            response = requests.get(f'{url}/api/p2p/status')
            if response.status_code == 200:
                p2p_data = response.json()['data']
                connections = p2p_data.get('connections', 0)
                enabled = p2p_data.get('enabled', False)
                print(f"   {node_name}: P2P={enabled}, Connections={connections}")
            else:
                print(f"   {node_name}: ❌ P2P status failed")
        except Exception as e:
            print(f"   {node_name}: ❌ Error - {e}")
    
    print("\n🎯 Analysis:")
    print("If you see P2P broadcast logs in your terminals but transactions don't propagate,")
    print("the issue is in message handling. If you don't see broadcast logs, the issue")
    print("is in the broadcasting trigger logic.")

def main():
    """Main function"""
    print("🔍 P2P Broadcast Trigger Test")
    print("This test triggers P2P broadcasting and monitors the results")
    print()
    
    test_broadcast_trigger()
    
    print("\n📝 What to look for in your node terminals:")
    print("✅ [P2P] Broadcasting transaction message to 2 peers")
    print("✅ [P2P] Successfully sent transaction message to peer")
    print("✅ [P2P] Broadcast completed: 2/2 messages sent")
    print("❌ If you don't see these, broadcasting is not being triggered")

if __name__ == '__main__':
    main() 