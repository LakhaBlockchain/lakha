#!/usr/bin/env python3
"""
Chain Synchronization Script
Synchronizes blockchain chains across all nodes
"""

import requests
import json
import time

def get_chain_info(node_port):
    """Get chain information from a node"""
    try:
        response = requests.get(f'http://localhost:{node_port}/api/status')
        if response.status_code == 200:
            return response.json()['data']
        else:
            return None
    except Exception as e:
        print(f"Error getting chain info from port {node_port}: {e}")
        return None

def get_blocks(node_port, start_index=0, limit=100):
    """Get blocks from a node"""
    try:
        response = requests.get(f'http://localhost:{node_port}/api/blocks?page=1&limit={limit}')
        if response.status_code == 200:
            return response.json()['data']['blocks']
        else:
            return []
    except Exception as e:
        print(f"Error getting blocks from port {node_port}: {e}")
        return []

def sync_chains():
    """Synchronize chains across all nodes"""
    print("🔄 Chain Synchronization Script")
    print("=" * 50)
    
    # Get chain info from all nodes
    print("1️⃣ Getting current chain status...")
    node1_info = get_chain_info(5000)
    node2_info = get_chain_info(5001)
    node3_info = get_chain_info(5002)
    
    if not all([node1_info, node2_info, node3_info]):
        print("❌ Could not get chain info from all nodes")
        return
    
    print(f"   Node 1: {node1_info['chain_length']} blocks")
    print(f"   Node 2: {node2_info['chain_length']} blocks")
    print(f"   Node 3: {node3_info['chain_length']} blocks")
    
    # Find the node with the longest chain (should be Node 1)
    max_blocks = max(node1_info['chain_length'], node2_info['chain_length'], node3_info['chain_length'])
    leader_node = None
    
    if node1_info['chain_length'] == max_blocks:
        leader_node = 5000
        print(f"   ✅ Node 1 is the leader with {max_blocks} blocks")
    elif node2_info['chain_length'] == max_blocks:
        leader_node = 5001
        print(f"   ✅ Node 2 is the leader with {max_blocks} blocks")
    elif node3_info['chain_length'] == max_blocks:
        leader_node = 5002
        print(f"   ✅ Node 3 is the leader with {max_blocks} blocks")
    
    if not leader_node:
        print("❌ Could not determine leader node")
        return
    
    # Get all blocks from the leader
    print(f"\n2️⃣ Getting all blocks from leader (port {leader_node})...")
    all_blocks = get_blocks(leader_node, 0, max_blocks)
    print(f"   Retrieved {len(all_blocks)} blocks")
    
    if not all_blocks:
        print("❌ Could not retrieve blocks from leader")
        return
    
    # Show block details
    print("\n3️⃣ Block chain details:")
    for i, block in enumerate(all_blocks):
        print(f"   Block #{block['index']}: {block['hash'][:16]}... (prev: {block['previous_hash'][:16]}...)")
    
    # Check if chains are already synchronized
    print("\n4️⃣ Checking if chains need synchronization...")
    nodes_to_sync = []
    
    if node1_info['chain_length'] < max_blocks:
        nodes_to_sync.append(5000)
    if node2_info['chain_length'] < max_blocks:
        nodes_to_sync.append(5001)
    if node3_info['chain_length'] < max_blocks:
        nodes_to_sync.append(5002)
    
    if not nodes_to_sync:
        print("   ✅ All chains are already synchronized!")
        return
    
    print(f"   Nodes that need sync: {nodes_to_sync}")
    
    # For now, we can't directly sync chains via API
    # The P2P network should handle this automatically
    print("\n5️⃣ Chain synchronization strategy:")
    print("   📋 The P2P network should automatically sync chains")
    print("   📋 If not working, you may need to restart the nodes")
    print("   📋 Or manually trigger block requests")
    
    # Check if P2P is working
    print("\n6️⃣ Checking P2P status...")
    for port in [5000, 5001, 5002]:
        try:
            response = requests.get(f'http://localhost:{port}/api/p2p/status')
            if response.status_code == 200:
                p2p_info = response.json()['data']
                print(f"   Port {port}: {p2p_info['connections']} connections, enabled: {p2p_info['enabled']}")
            else:
                print(f"   Port {port}: P2P status unavailable")
        except Exception as e:
            print(f"   Port {port}: Error getting P2P status - {e}")
    
    print("\n7️⃣ Recommendations:")
    print("   🔄 Restart all nodes to ensure clean state")
    print("   🔄 Make sure P2P connections are established")
    print("   🔄 Submit a new transaction to trigger sync")
    print("   🔄 Mine a new block to test propagation")

def test_chain_sync():
    """Test if chains are synchronized after some time"""
    print("\n🔄 Testing Chain Synchronization")
    print("=" * 50)
    
    # Wait a bit for P2P sync
    print("⏳ Waiting 10 seconds for P2P synchronization...")
    time.sleep(10)
    
    # Check chain lengths again
    print("📊 Checking chain lengths after wait...")
    node1_info = get_chain_info(5000)
    node2_info = get_chain_info(5001)
    node3_info = get_chain_info(5002)
    
    if all([node1_info, node2_info, node3_info]):
        print(f"   Node 1: {node1_info['chain_length']} blocks")
        print(f"   Node 2: {node2_info['chain_length']} blocks")
        print(f"   Node 3: {node3_info['chain_length']} blocks")
        
        if node1_info['chain_length'] == node2_info['chain_length'] == node3_info['chain_length']:
            print("   ✅ Chains are synchronized!")
        else:
            print("   ❌ Chains are still not synchronized")
    else:
        print("   ❌ Could not get chain info")

if __name__ == '__main__':
    sync_chains()
    test_chain_sync() 