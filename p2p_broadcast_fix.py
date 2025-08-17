#!/usr/bin/env python3
"""
P2P Broadcasting Fix Demonstration
Shows the current issue and provides a simple fix
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any

def test_current_broadcasting():
    """Test the current broadcasting behavior"""
    print("🔍 Testing Current P2P Broadcasting")
    print("=" * 45)
    
    # Test Node 1
    print("\n1️⃣ Testing Node 1 (Port 5000):")
    try:
        # Generate address
        response = requests.post('http://localhost:5000/api/utils/generate-address')
        if response.status_code == 200:
            address = response.json()['data']['address']
            print(f"   Generated address: {address}")
            
            # Submit faucet transaction
            faucet_response = requests.post('http://localhost:5000/api/faucet', 
                                          json={'address': address, 'amount': 50.0})
            if faucet_response.status_code == 200:
                print(f"   ✅ Faucet transaction submitted")
                
                # Check pending transactions
                pending_response = requests.get('http://localhost:5000/api/transactions/pending')
                if pending_response.status_code == 200:
                    pending_count = pending_response.json()['data']['count']
                    print(f"   📊 Pending transactions: {pending_count}")
            else:
                print(f"   ❌ Faucet failed: {faucet_response.text}")
        else:
            print(f"   ❌ Address generation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Node 2
    print("\n2️⃣ Testing Node 2 (Port 5001):")
    try:
        # Check pending transactions
        pending_response = requests.get('http://localhost:5001/api/transactions/pending')
        if pending_response.status_code == 200:
            pending_count = pending_response.json()['data']['count']
            print(f"   📊 Pending transactions: {pending_count}")
            if pending_count == 0:
                print("   ❌ No transactions received from Node 1 (broadcasting failed)")
            else:
                print("   ✅ Transactions received from Node 1")
        else:
            print(f"   ❌ Failed to get pending transactions: {pending_response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Node 3
    print("\n3️⃣ Testing Node 3 (Port 5002):")
    try:
        # Check pending transactions
        pending_response = requests.get('http://localhost:5002/api/transactions/pending')
        if pending_response.status_code == 200:
            pending_count = pending_response.json()['data']['count']
            print(f"   📊 Pending transactions: {pending_count}")
            if pending_count == 0:
                print("   ❌ No transactions received from Node 1 (broadcasting failed)")
            else:
                print("   ✅ Transactions received from Node 1")
        else:
            print(f"   ❌ Failed to get pending transactions: {pending_response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demonstrate_broadcasting_issue():
    """Demonstrate the specific broadcasting issue"""
    print("\n🎯 Broadcasting Issue Analysis")
    print("=" * 40)
    
    print("\n❌ CURRENT PROBLEMS:")
    print("1. Async Event Loop Mismatch:")
    print("   • Flask runs in main thread (synchronous)")
    print("   • P2P network runs in separate thread (asynchronous)")
    print("   • run_coroutine_threadsafe() may not work properly")
    
    print("\n2. Message Serialization Issues:")
    print("   • Transaction objects may not serialize to JSON properly")
    print("   • Block objects may have circular references")
    print("   • Enum values may not convert correctly")
    
    print("\n3. Timing Issues:")
    print("   • Broadcasting may happen before P2P connections are established")
    print("   • Race conditions between API and P2P startup")
    print("   • Insufficient delays for network stabilization")
    
    print("\n4. Error Handling:")
    print("   • Silent failures in broadcast methods")
    print("   • No logging of broadcast attempts")
    print("   • No retry mechanisms for failed broadcasts")

def suggest_simple_fixes():
    """Suggest simple fixes for the broadcasting issue"""
    print("\n🛠️ Simple Fixes")
    print("=" * 20)
    
    print("\n1️⃣ IMMEDIATE FIXES:")
    print("   • Add proper error handling and logging to broadcast methods")
    print("   • Ensure proper JSON serialization of objects")
    print("   • Add connection status checks before broadcasting")
    print("   • Add delays for P2P network startup")
    
    print("\n2️⃣ CODE CHANGES NEEDED:")
    print("   • Fix async event loop handling in api.py")
    print("   • Add proper error handling in core.py broadcast methods")
    print("   • Improve message serialization in p2p.py")
    print("   • Add connection status monitoring")
    
    print("\n3️⃣ TESTING IMPROVEMENTS:")
    print("   • Add logging to track message flow")
    print("   • Add connection status endpoints")
    print("   • Add broadcast success/failure metrics")
    print("   • Add automated multi-node testing")

def create_broadcast_test():
    """Create a simple test to verify broadcasting"""
    print("\n🧪 Creating Broadcast Test")
    print("=" * 30)
    
    test_code = '''
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
'''
    
    with open('broadcast_test.py', 'w') as f:
        f.write(test_code)
    
    print("✅ Created broadcast_test.py")
    print("Run with: python broadcast_test.py")

def main():
    """Main function"""
    print("🔍 P2P Broadcasting Issue Analysis")
    print("This script analyzes the current P2P broadcasting issues")
    print("and suggests fixes for the multi-node setup.")
    print()
    
    # Check if nodes are running
    print("Checking if nodes are running...")
    nodes_running = 0
    for port in [5000, 5001, 5002]:
        try:
            response = requests.get(f'http://localhost:{port}/api/health', timeout=2)
            if response.status_code == 200:
                nodes_running += 1
                print(f"✅ Node on port {port} is running")
            else:
                print(f"❌ Node on port {port} is not responding")
        except:
            print(f"❌ Node on port {port} is not running")
    
    if nodes_running < 3:
        print(f"\n⚠️ Only {nodes_running}/3 nodes are running.")
        print("Please start all nodes first using the multi-node guide.")
        return
    
    print(f"\n✅ All {nodes_running} nodes are running!")
    
    # Run tests
    test_current_broadcasting()
    demonstrate_broadcasting_issue()
    suggest_simple_fixes()
    create_broadcast_test()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run the broadcast test: python broadcast_test.py")
    print("2. Check the logs for P2P connection and broadcast errors")
    print("3. Implement the suggested fixes")
    print("4. Test again to verify broadcasting works")

if __name__ == '__main__':
    main() 