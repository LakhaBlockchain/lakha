
#!/usr/bin/env python3
"""
Simple Broadcast Test
Tests P2P broadcasting functionality
"""

import requests
import time
import json

def test_broadcast():
    """Test broadcasting between nodes"""
    print("Testing P2P Broadcasting...")
    
    # Step 1: Generate address on Node 1
    print("1. Generating address on Node 1...")
    response = requests.post('http://localhost:5000/api/utils/generate-address')
    if response.status_code != 200:
        print("❌ Failed to generate address")
        return
    
    address = response.json()['data']['address']
    print(f"   Address: {address}")
    
    # Step 2: Submit transaction on Node 1
    print("2. Submitting transaction on Node 1...")
    tx_data = {
        'from_address': 'genesis',
        'to_address': address,
        'amount': 100.0,
        'transaction_type': 'transfer',
        'gas_limit': 21000,
        'gas_price': 1.0
    }
    
    response = requests.post('http://localhost:5000/api/transactions', json=tx_data)
    if response.status_code != 200:
        print("❌ Failed to submit transaction")
        return
    
    tx_hash = response.json()['data']['transaction_hash']
    print(f"   Transaction hash: {tx_hash[:16]}...")
    
    # Step 3: Wait for broadcast
    print("3. Waiting for broadcast...")
    time.sleep(3)
    
    # Step 4: Check all nodes for the transaction
    print("4. Checking all nodes for transaction...")
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

if __name__ == '__main__':
    test_broadcast()
