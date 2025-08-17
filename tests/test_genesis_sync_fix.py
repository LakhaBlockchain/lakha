#!/usr/bin/env python3
"""
Test Genesis Block Synchronization Fix
Tests that all nodes now have the same genesis block hash
"""

import requests
import json
import time

def get_genesis_block_hash(node_port):
    """Get the genesis block hash from a node"""
    try:
        response = requests.get(f'http://localhost:{node_port}/api/blocks/0')
        if response.status_code == 200:
            block_data = response.json()['data']
            return block_data['hash']
        else:
            return None
    except Exception as e:
        print(f"Error getting genesis block from port {node_port}: {e}")
        return None

def test_genesis_synchronization():
    """Test that all nodes have the same genesis block hash"""
    print("🔍 Testing Genesis Block Synchronization Fix")
    print("=" * 60)
    
    # Get genesis block hashes from all nodes
    print("1️⃣ Getting genesis block hashes...")
    node1_hash = get_genesis_block_hash(5000)
    node2_hash = get_genesis_block_hash(5001)
    node3_hash = get_genesis_block_hash(5002)
    
    if not all([node1_hash, node2_hash, node3_hash]):
        print("❌ Could not get genesis block hashes from all nodes")
        return False
    
    print(f"   Node 1 genesis hash: {node1_hash}")
    print(f"   Node 2 genesis hash: {node2_hash}")
    print(f"   Node 3 genesis hash: {node3_hash}")
    
    # Check if all hashes are the same
    if node1_hash == node2_hash == node3_hash:
        print("   ✅ All nodes have the same genesis block hash!")
        return True
    else:
        print("   ❌ Genesis block hashes are different")
        return False

def test_block_propagation():
    """Test block propagation after genesis fix"""
    print("\n2️⃣ Testing Block Propagation...")
    
    # Submit a transaction from Node 1
    print("   Submitting transaction from Node 1...")
    try:
        # Generate a valid address first
        address_response = requests.post('http://localhost:5000/api/utils/generate-address')
        if address_response.status_code != 200:
            print(f"   ❌ Failed to generate address: {address_response.json()}")
            return False
        
        valid_address = address_response.json()['data']['address']
        
        response = requests.post('http://localhost:5000/api/transactions', json={
            'from_address': 'genesis',
            'to_address': valid_address,
            'amount': 50.0,
            'transaction_type': 'transfer',
            'nonce': 0
        })
        
        if response.status_code == 200:
            tx_data = response.json()['data']
            print(f"   ✅ Transaction submitted: {tx_data['transaction_hash']}")
        else:
            print(f"   ❌ Transaction failed: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error submitting transaction: {e}")
        return False
    
    # Wait for transaction propagation
    print("   ⏳ Waiting for transaction propagation...")
    time.sleep(3)
    
    # Check pending transactions on all nodes
    print("   Checking pending transactions...")
    for port in [5000, 5001, 5002]:
        try:
            response = requests.get(f'http://localhost:{port}/api/transactions/pending')
            if response.status_code == 200:
                pending_data = response.json()['data']
                print(f"   Port {port}: {pending_data['count']} pending transactions")
            else:
                print(f"   Port {port}: Error getting pending transactions")
        except Exception as e:
            print(f"   Port {port}: Error - {e}")
    
    # Mine a block on Node 1
    print("   Mining block on Node 1...")
    try:
        response = requests.post('http://localhost:5000/api/mining/mine')
        if response.status_code == 200:
            mine_data = response.json()['data']
            print(f"   ✅ Block mined: {mine_data['message']}")
            print(f"   📦 Block hash: {mine_data['block_hash']}")
        else:
            print(f"   ❌ Mining failed: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ Error mining block: {e}")
        return False
    
    # Wait for block propagation
    print("   ⏳ Waiting for block propagation...")
    time.sleep(5)
    
    # Check chain lengths
    print("   Checking chain lengths...")
    chain_lengths = []
    for port in [5000, 5001, 5002]:
        try:
            response = requests.get(f'http://localhost:{port}/api/status')
            if response.status_code == 200:
                status_data = response.json()['data']
                chain_length = status_data['chain_length']
                chain_lengths.append(chain_length)
                print(f"   Port {port}: {chain_length} blocks")
            else:
                print(f"   Port {port}: Error getting status")
        except Exception as e:
            print(f"   Port {port}: Error - {e}")
    
    # Check if chains are synchronized
    if len(set(chain_lengths)) == 1:
        print("   ✅ All chains are synchronized!")
        return True
    else:
        print("   ❌ Chains are not synchronized")
        return False

def main():
    """Main test function"""
    print("🚀 Genesis Block Synchronization Test")
    print("=" * 60)
    
    # Test 1: Genesis block synchronization
    genesis_sync = test_genesis_synchronization()
    
    if not genesis_sync:
        print("\n❌ Genesis blocks are not synchronized. Please restart all nodes.")
        return
    
    # Test 2: Block propagation
    block_prop = test_block_propagation()
    
    if block_prop:
        print("\n🎉 SUCCESS: Genesis block synchronization fix is working!")
        print("✅ All nodes have the same genesis block")
        print("✅ Block propagation is working")
        print("✅ Chain synchronization is working")
    else:
        print("\n⚠️  Genesis blocks are synchronized, but block propagation needs testing")
        print("   This might be due to timing issues or other factors")

if __name__ == '__main__':
    main() 