#!/usr/bin/env python3
"""
Check P2P Connections
Detailed check of P2P connection status and broadcasting conditions
"""

import requests
import json

def check_p2p_details():
    """Check detailed P2P connection information"""
    print("🔍 Detailed P2P Connection Check")
    print("=" * 40)
    
    nodes = [
        ('Node 1', 'http://localhost:5000'),
        ('Node 2', 'http://localhost:5001'),
        ('Node 3', 'http://localhost:5002')
    ]
    
    for node_name, url in nodes:
        print(f"\n📡 {node_name}:")
        
        # Check P2P status
        try:
            response = requests.get(f'{url}/api/p2p/status')
            if response.status_code == 200:
                p2p_data = response.json()['data']
                print(f"   P2P Enabled: {p2p_data.get('enabled', False)}")
                print(f"   P2P Port: {p2p_data.get('p2p_port', 'None')}")
                print(f"   Connections: {p2p_data.get('connections', 0)}")
                print(f"   Thread Running: {p2p_data.get('thread_running', False)}")
                print(f"   P2P Peers: {p2p_data.get('p2p_peers', [])}")
            else:
                print(f"   ❌ P2P status failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Check pending transactions
        try:
            response = requests.get(f'{url}/api/transactions/pending')
            if response.status_code == 200:
                pending_count = response.json()['data']['count']
                print(f"   Pending Transactions: {pending_count}")
            else:
                print(f"   ❌ Pending transactions failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_broadcast_conditions():
    """Test the specific conditions for broadcasting"""
    print("\n🧪 Testing Broadcast Conditions")
    print("=" * 35)
    
    # Test Node 1 specifically
    print("\n1️⃣ Testing Node 1 broadcast conditions:")
    
    # Check if P2P node exists
    try:
        response = requests.get('http://localhost:5000/api/p2p/status')
        if response.status_code == 200:
            p2p_data = response.json()['data']
            p2p_enabled = p2p_data.get('enabled', False)
            connections = p2p_data.get('connections', 0)
            thread_running = p2p_data.get('thread_running', False)
            
            print(f"   P2P Node exists: {p2p_enabled}")
            print(f"   P2P Thread running: {thread_running}")
            print(f"   P2P Connections: {connections}")
            
            # Check broadcasting conditions
            if p2p_enabled and thread_running and connections > 0:
                print("   ✅ All broadcast conditions met!")
                print("   📡 Broadcasting should work")
            else:
                print("   ❌ Broadcast conditions not met:")
                if not p2p_enabled:
                    print("      - P2P not enabled")
                if not thread_running:
                    print("      - P2P thread not running")
                if connections == 0:
                    print("      - No P2P connections")
        else:
            print(f"   ❌ P2P status failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def trigger_test_broadcast():
    """Trigger a test broadcast and monitor results"""
    print("\n2️⃣ Triggering test broadcast...")
    
    # Generate address
    try:
        response = requests.post('http://localhost:5000/api/utils/generate-address')
        if response.status_code == 200:
            address = response.json()['data']['address']
            print(f"   Generated address: {address}")
            
            # Get nonce
            nonce_response = requests.get('http://localhost:5000/api/accounts/genesis/nonce')
            nonce = 0
            if nonce_response.status_code == 200:
                nonce = nonce_response.json()['data']['nonce']
            
            # Submit transaction
            tx_data = {
                'from_address': 'genesis',
                'to_address': address,
                'amount': 10.0,
                'transaction_type': 'transfer',
                'gas_limit': 21000,
                'gas_price': 1.0,
                'nonce': nonce
            }
            
            print("   ⚠️  SUBMITTING TRANSACTION - WATCH NODE 1 TERMINAL FOR LOGS!")
            response = requests.post('http://localhost:5000/api/transactions', json=tx_data)
            
            if response.status_code == 200:
                tx_hash = response.json()['data']['transaction_hash']
                print(f"   ✅ Transaction submitted: {tx_hash[:16]}...")
                print("   📡 Check Node 1 terminal for broadcast logs!")
            else:
                print(f"   ❌ Transaction failed: {response.text}")
        else:
            print(f"   ❌ Address generation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Main function"""
    print("🔍 P2P Connection and Broadcast Analysis")
    print("This script checks P2P connections and broadcast conditions")
    print()
    
    check_p2p_details()
    test_broadcast_conditions()
    trigger_test_broadcast()
    
    print("\n📝 Instructions:")
    print("1. Check your Node 1 terminal for any logs mentioning:")
    print("   - 'Broadcasting transaction'")
    print("   - 'P2P connections'")
    print("   - 'No P2P connections available'")
    print("2. If you see broadcast logs, check other nodes for transaction propagation")
    print("3. If you don't see broadcast logs, the broadcasting conditions are not met")

if __name__ == '__main__':
    main() 