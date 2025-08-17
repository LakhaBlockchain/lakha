#!/usr/bin/env python3
"""
Test P2P Fix
Simple test to verify P2P message handling works after fixes
"""

import requests
import time
import json

def test_p2p_message_handling():
    """Test P2P message handling with enhanced logging"""
    print("🧪 Testing P2P Message Handling Fix")
    print("=" * 45)
    
    # Check if nodes are running
    print("\n1️⃣ Checking node status...")
    nodes = [
        ('Node 1', 'http://localhost:5000'),
        ('Node 2', 'http://localhost:5001'),
        ('Node 3', 'http://localhost:5002')
    ]
    
    for node_name, url in nodes:
        try:
            response = requests.get(f'{url}/api/health', timeout=2)
            if response.status_code == 200:
                print(f"   ✅ {node_name}: Running")
            else:
                print(f"   ❌ {node_name}: Not responding")
        except Exception as e:
            print(f"   ❌ {node_name}: Error - {e}")
    
    # Test transaction submission and broadcasting
    print("\n2️⃣ Testing transaction broadcasting...")
    try:
        # Generate address
        response = requests.post('http://localhost:5000/api/utils/generate-address')
        if response.status_code == 200:
            address = response.json()['data']['address']
            print(f"   Generated address: {address}")
            
            # Get genesis account nonce first
            print("   Getting genesis account nonce...")
            nonce_response = requests.get('http://localhost:5000/api/accounts/genesis/nonce')
            if nonce_response.status_code == 200:
                nonce = nonce_response.json()['data']['nonce']
                print(f"   Genesis nonce: {nonce}")
            else:
                nonce = 0
                print("   Using default nonce: 0")
            
            # Submit transaction with correct nonce
            tx_data = {
                'from_address': 'genesis',
                'to_address': address,
                'amount': 50.0,
                'transaction_type': 'transfer',
                'gas_limit': 21000,
                'gas_price': 1.0,
                'nonce': nonce
            }
            
            response = requests.post('http://localhost:5000/api/transactions', json=tx_data)
            if response.status_code == 200:
                tx_hash = response.json()['data']['transaction_hash']
                print(f"   ✅ Transaction submitted: {tx_hash[:16]}...")
                
                # Wait for broadcast
                print("   Waiting for broadcast...")
                time.sleep(3)
                
                # Check all nodes for the transaction
                print("   Checking all nodes for transaction...")
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
            else:
                print(f"   ❌ Transaction failed: {response.text}")
        else:
            print(f"   ❌ Address generation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check P2P status
    print("\n3️⃣ Checking P2P status...")
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

def main():
    """Main function"""
    print("🧪 P2P Fix Test")
    print("This test verifies the P2P message handling fixes")
    print()
    
    print("📋 Instructions:")
    print("1. Make sure all 3 nodes are running")
    print("2. Check the node logs for P2P message handling")
    print("3. Look for '[P2P]' log messages")
    print("4. Verify transaction propagation between nodes")
    print()
    
    test_p2p_message_handling()
    
    print("\n🎯 Expected Results:")
    print("✅ P2P message logs should appear in node terminals")
    print("✅ Transactions should propagate between nodes")
    print("✅ All nodes should show the same pending transactions")
    print()
    
    print("📝 Next Steps:")
    print("1. Check the node terminal logs for P2P messages")
    print("2. If messages are still not propagating, check for:")
    print("   - Handler registration errors")
    print("   - Message serialization issues")
    print("   - Event loop problems")

if __name__ == '__main__':
    main() 