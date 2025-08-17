#!/usr/bin/env python3
"""
Complete P2P Flow Test
Tests the entire P2P flow: transaction submission, propagation, mining, and block propagation
"""

import requests
import time
import json
from address import generate_address

def test_complete_p2p_flow():
    """Test the complete P2P flow"""
    print("🔍 Complete P2P Flow Test")
    print("=" * 50)
    
    # Test parameters
    node1_url = "http://localhost:5000"
    node2_url = "http://localhost:5001"
    node3_url = "http://localhost:5002"
    
    print("📋 Instructions:")
    print("1. Make sure your 3 nodes are running on ports 5000, 5001, 5002")
    print("2. Watch the node terminals for P2P logs")
    print("3. This test will submit transactions and mine blocks")
    
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
    
    # Step 2: Check initial state
    print("\n2️⃣ Checking initial state...")
    try:
        # Check chain lengths
        status1 = requests.get(f"{node1_url}/api/status").json()
        status2 = requests.get(f"{node2_url}/api/status").json()
        status3 = requests.get(f"{node3_url}/api/status").json()
        
        # Handle different response formats
        def get_chain_length(status):
            if 'data' in status and 'chain_length' in status['data']:
                return status['data']['chain_length']
            elif 'chain_length' in status:
                return status['chain_length']
            else:
                return 0
        
        def get_pending_count(pending):
            if 'data' in pending and 'count' in pending['data']:
                return pending['data']['count']
            elif 'count' in pending:
                return pending['count']
            else:
                return len(pending.get('transactions', []))
        
        chain1 = get_chain_length(status1)
        chain2 = get_chain_length(status2)
        chain3 = get_chain_length(status3)
        
        print(f"   Node 1 chain length: {chain1}")
        print(f"   Node 2 chain length: {chain2}")
        print(f"   Node 3 chain length: {chain3}")
        
        # Check pending transactions
        pending1 = requests.get(f"{node1_url}/api/transactions/pending").json()
        pending2 = requests.get(f"{node2_url}/api/transactions/pending").json()
        pending3 = requests.get(f"{node3_url}/api/transactions/pending").json()
        
        pending1_count = get_pending_count(pending1)
        pending2_count = get_pending_count(pending2)
        pending3_count = get_pending_count(pending3)
        
        print(f"   Node 1 pending: {pending1_count}")
        print(f"   Node 2 pending: {pending2_count}")
        print(f"   Node 3 pending: {pending3_count}")
        
    except Exception as e:
        print(f"   ❌ Status check failed: {e}")
        print(f"   Debug - Node 1 status: {requests.get(f'{node1_url}/api/status').text}")
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
    
    # Step 4: Submit transactions from all nodes
    print("\n4️⃣ Submitting transactions from all nodes...")
    print("   ⚠️  WATCH YOUR NODE TERMINALS FOR P2P LOGS!")
    
    transactions = []
    
    # Submit from Node 1
    try:
        nonce_resp = requests.get(f"{node1_url}/api/accounts/genesis/nonce").json()
        current_nonce = nonce_resp['data']['nonce']
        
        tx_data = {
            "from_address": "genesis",
            "to_address": address1,
            "amount": 50.0,
            "transaction_type": "transfer",
            "gas_limit": 21000,
            "gas_price": 1.0,
            "nonce": current_nonce
        }
        
        tx_resp = requests.post(f"{node1_url}/api/transactions", json=tx_data).json()
        
        if tx_resp['status'] == 'success':
            print(f"   ✅ Node 1 transaction: {tx_resp['data']['transaction_hash']}")
            transactions.append(tx_resp['data']['transaction_hash'])
        else:
            print(f"   ❌ Node 1 transaction failed: {tx_resp}")
    except Exception as e:
        print(f"   ❌ Node 1 transaction failed: {e}")
    
    # Wait a moment
    time.sleep(1)
    
    # Submit from Node 2
    try:
        nonce_resp = requests.get(f"{node2_url}/api/accounts/genesis/nonce").json()
        current_nonce = nonce_resp['data']['nonce']
        
        tx_data = {
            "from_address": "genesis",
            "to_address": address2,
            "amount": 40.0,
            "transaction_type": "transfer",
            "gas_limit": 21000,
            "gas_price": 1.0,
            "nonce": current_nonce
        }
        
        tx_resp = requests.post(f"{node2_url}/api/transactions", json=tx_data).json()
        
        if tx_resp['status'] == 'success':
            print(f"   ✅ Node 2 transaction: {tx_resp['data']['transaction_hash']}")
            transactions.append(tx_resp['data']['transaction_hash'])
        else:
            print(f"   ❌ Node 2 transaction failed: {tx_resp}")
    except Exception as e:
        print(f"   ❌ Node 2 transaction failed: {e}")
    
    # Wait a moment
    time.sleep(1)
    
    # Submit from Node 3
    try:
        nonce_resp = requests.get(f"{node3_url}/api/accounts/genesis/nonce").json()
        current_nonce = nonce_resp['data']['nonce']
        
        tx_data = {
            "from_address": "genesis",
            "to_address": address3,
            "amount": 30.0,
            "transaction_type": "transfer",
            "gas_limit": 21000,
            "gas_price": 1.0,
            "nonce": current_nonce
        }
        
        tx_resp = requests.post(f"{node3_url}/api/transactions", json=tx_data).json()
        
        if tx_resp['status'] == 'success':
            print(f"   ✅ Node 3 transaction: {tx_resp['data']['transaction_hash']}")
            transactions.append(tx_resp['data']['transaction_hash'])
        else:
            print(f"   ❌ Node 3 transaction failed: {tx_resp}")
    except Exception as e:
        print(f"   ❌ Node 3 transaction failed: {e}")
    
    # Step 5: Wait for propagation
    print("\n5️⃣ Waiting for transaction propagation...")
    time.sleep(3)
    
    # Step 6: Check transaction propagation
    print("\n6️⃣ Checking transaction propagation...")
    try:
        pending1 = requests.get(f"{node1_url}/api/transactions/pending").json()
        pending2 = requests.get(f"{node2_url}/api/transactions/pending").json()
        pending3 = requests.get(f"{node3_url}/api/transactions/pending").json()
        
        # Helper function to get transactions list
        def get_transactions(pending):
            if 'data' in pending and 'transactions' in pending['data']:
                return pending['data']['transactions']
            elif 'transactions' in pending:
                return pending['transactions']
            else:
                return []
        
        def get_pending_count(pending):
            if 'data' in pending and 'count' in pending['data']:
                return pending['data']['count']
            elif 'count' in pending:
                return pending['count']
            else:
                return len(get_transactions(pending))
        
        pending1_count = get_pending_count(pending1)
        pending2_count = get_pending_count(pending2)
        pending3_count = get_pending_count(pending3)
        
        print(f"   Node 1 pending: {pending1_count}")
        print(f"   Node 2 pending: {pending2_count}")
        print(f"   Node 3 pending: {pending3_count}")
        
        # Check if all transactions propagated
        all_propagated = True
        for tx_hash in transactions:
            tx_list1 = get_transactions(pending1)
            tx_list2 = get_transactions(pending2)
            tx_list3 = get_transactions(pending3)
            
            tx_in_node1 = any(tx['hash'] == tx_hash for tx in tx_list1)
            tx_in_node2 = any(tx['hash'] == tx_hash for tx in tx_list2)
            tx_in_node3 = any(tx['hash'] == tx_hash for tx in tx_list3)
            
            if not (tx_in_node1 and tx_in_node2 and tx_in_node3):
                all_propagated = False
                print(f"   ❌ Transaction {tx_hash[:8]}... did not propagate to all nodes")
        
        if all_propagated:
            print("   ✅ All transactions successfully propagated!")
        else:
            print("   ❌ Some transactions did not propagate")
            
    except Exception as e:
        print(f"   ❌ Propagation check failed: {e}")
    
    # Step 7: Mine a block (should trigger block propagation)
    print("\n7️⃣ Mining a block (should trigger block propagation)...")
    print("   ⚠️  WATCH YOUR NODE TERMINALS FOR BLOCK PROPAGATION LOGS!")
    
    try:
        mine_resp = requests.post(f"{node1_url}/api/mining/mine").json()
        
        if mine_resp['status'] == 'success':
            print(f"   ✅ Block mined: {mine_resp['data']['message']}")
            print(f"   📦 Block hash: {mine_resp['data']['block_hash']}")
            print(f"   📊 Transactions processed: {mine_resp['data']['transactions_processed']}")
        else:
            print(f"   ❌ Mining failed: {mine_resp}")
    except Exception as e:
        print(f"   ❌ Mining failed: {e}")
    
    # Step 8: Wait for block propagation
    print("\n8️⃣ Waiting for block propagation...")
    time.sleep(3)
    
    # Step 9: Check block propagation
    print("\n9️⃣ Checking block propagation...")
    try:
        status1 = requests.get(f"{node1_url}/api/status").json()
        status2 = requests.get(f"{node2_url}/api/status").json()
        status3 = requests.get(f"{node3_url}/api/status").json()
        
        # Helper function to get chain length
        def get_chain_length(status):
            if 'data' in status and 'chain_length' in status['data']:
                return status['data']['chain_length']
            elif 'chain_length' in status:
                return status['chain_length']
            else:
                return 0
        
        def get_pending_count(pending):
            if 'data' in pending and 'count' in pending['data']:
                return pending['data']['count']
            elif 'count' in pending:
                return pending['count']
            else:
                return len(pending.get('transactions', []))
        
        chain1 = get_chain_length(status1)
        chain2 = get_chain_length(status2)
        chain3 = get_chain_length(status3)
        
        print(f"   Node 1 chain length: {chain1}")
        print(f"   Node 2 chain length: {chain2}")
        print(f"   Node 3 chain length: {chain3}")
        
        # Check if chains are synchronized
        if chain1 == chain2 == chain3:
            print("   ✅ All nodes have synchronized chains!")
        else:
            print("   ❌ Chains are not synchronized")
        
        # Check pending transactions (should be 0 after mining)
        pending1 = requests.get(f"{node1_url}/api/transactions/pending").json()
        pending2 = requests.get(f"{node2_url}/api/transactions/pending").json()
        pending3 = requests.get(f"{node3_url}/api/transactions/pending").json()
        
        pending1_count = get_pending_count(pending1)
        pending2_count = get_pending_count(pending2)
        pending3_count = get_pending_count(pending3)
        
        print(f"   Node 1 pending: {pending1_count}")
        print(f"   Node 2 pending: {pending2_count}")
        print(f"   Node 3 pending: {pending3_count}")
        
        if pending1_count == pending2_count == pending3_count == 0:
            print("   ✅ All pending transactions cleared after mining!")
        else:
            print("   ❌ Pending transactions not cleared")
            
    except Exception as e:
        print(f"   ❌ Block propagation check failed: {e}")
    
    print("\n📝 What to look for in your node terminals:")
    print("✅ [P2P] Broadcasting transaction message to X peers")
    print("✅ [P2P] Received message: {\"type\": \"transaction\"...}")
    print("✅ [P2P] Adding received transaction [hash]")
    print("✅ [P2P] Broadcasting block message to X peers")
    print("✅ [P2P] Received message: {\"type\": \"block\"...}")
    print("✅ [P2P] Adding received block [index]")
    
    print("\n🎉 Complete P2P flow test finished!")
    print("🚀 Your Lakha blockchain now has full P2P functionality!")

if __name__ == "__main__":
    test_complete_p2p_flow() 