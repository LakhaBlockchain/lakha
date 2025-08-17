#!/usr/bin/env python3
"""
Simple P2P Broadcast Test
Tests P2P broadcasting directly without API layer
"""

import asyncio
import time
import json
from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address

async def test_p2p_broadcast():
    """Test P2P broadcasting directly"""
    print("🔍 Simple P2P Broadcast Test")
    print("=" * 50)
    
    # Create blockchain instances
    print("1️⃣ Creating blockchain instances...")
    blockchain1 = LahkaBlockchain(
        test_mode=False,
        db_path='lakha_db_test1',
        p2p_port=9001,
        p2p_peers=None
    )
    
    blockchain2 = LahkaBlockchain(
        test_mode=False,
        db_path='lakha_db_test2',
        p2p_port=9002,
        p2p_peers=['ws://localhost:9001']
    )
    
    blockchain3 = LahkaBlockchain(
        test_mode=False,
        db_path='lakha_db_test3',
        p2p_port=9003,
        p2p_peers=['ws://localhost:9001', 'ws://localhost:9002']
    )
    
    # Start P2P networks
    print("2️⃣ Starting P2P networks...")
    await blockchain1.start_network()
    await blockchain2.start_network()
    await blockchain3.start_network()
    
    # Wait for connections to establish
    print("3️⃣ Waiting for P2P connections...")
    await asyncio.sleep(3)
    
    # Check connections
    print("4️⃣ Checking P2P connections...")
    print(f"   Node 1 connections: {len(blockchain1.p2p_node.connections)}")
    print(f"   Node 2 connections: {len(blockchain2.p2p_node.connections)}")
    print(f"   Node 3 connections: {len(blockchain3.p2p_node.connections)}")
    
    # Create a test transaction
    print("5️⃣ Creating test transaction...")
    address = generate_address()
    genesis_account = blockchain1.ledger.get_account('genesis')
    
    tx = Transaction(
        from_address='genesis',
        to_address=address,
        amount=50.0,
        transaction_type=TransactionType.TRANSFER,
        gas_limit=21000,
        gas_price=1.0,
        nonce=genesis_account.nonce
    )
    
    # Add transaction to blockchain1
    print("6️⃣ Adding transaction to Node 1...")
    success = blockchain1.add_transaction(tx)
    print(f"   Transaction added: {success}")
    print(f"   Transaction hash: {tx.hash}")
    
    # Broadcast transaction from Node 1
    print("7️⃣ Broadcasting transaction from Node 1...")
    await blockchain1.broadcast_transaction(tx)
    print("   Broadcast completed")
    
    # Wait a moment for propagation
    print("8️⃣ Waiting for propagation...")
    await asyncio.sleep(2)
    
    # Check if transaction propagated
    print("9️⃣ Checking transaction propagation...")
    print(f"   Node 1 pending transactions: {len(blockchain1.pending_transactions)}")
    print(f"   Node 2 pending transactions: {len(blockchain2.pending_transactions)}")
    print(f"   Node 3 pending transactions: {len(blockchain3.pending_transactions)}")
    
    # Check if transaction hash exists in other nodes
    tx_in_node2 = any(t.hash == tx.hash for t in blockchain2.pending_transactions)
    tx_in_node3 = any(t.hash == tx.hash for t in blockchain3.pending_transactions)
    
    print(f"   Transaction in Node 2: {tx_in_node2}")
    print(f"   Transaction in Node 3: {tx_in_node3}")
    
    # Clean up
    print("🔚 Cleaning up...")
    await blockchain1.stop_network()
    await blockchain2.stop_network()
    await blockchain3.stop_network()
    blockchain1.close()
    blockchain2.close()
    blockchain3.close()
    
    print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_p2p_broadcast()) 