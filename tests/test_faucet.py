#!/usr/bin/env python3
"""
Test Faucet and Mining
Demonstrates the faucet functionality and manual mining
"""

import requests
import time
import json

API_URL = 'http://localhost:5000'

def make_request(method, endpoint, data=None):
    """Make HTTP request to API"""
    url = f"{API_URL}{endpoint}"
    try:
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return {'status': 'error', 'message': str(e)}

def test_faucet_and_mining():
    """Test faucet functionality and manual mining"""
    print("🧪 Testing Faucet and Mining")
    print("=" * 50)
    
    # Step 1: Generate a new address
    print("\n1️⃣ Generating new address...")
    result = make_request('POST', '/api/utils/generate-address')
    if result['status'] != 'success':
        print(f"❌ Failed to generate address: {result['message']}")
        return
    
    address = result['data']['address']
    print(f"✅ Generated address: {address}")
    
    # Step 2: Check initial balance
    print(f"\n2️⃣ Checking initial balance for {address}...")
    result = make_request('GET', f'/api/accounts/{address}/balance')
    if result['status'] == 'success':
        balance = result['data']['balance']
        print(f"💰 Initial balance: {balance}")
    else:
        print(f"ℹ️ Account not found (expected for new address)")
    
    # Step 3: Request tokens from faucet
    print(f"\n3️⃣ Requesting 100 tokens from faucet...")
    faucet_data = {'address': address, 'amount': 100.0}
    result = make_request('POST', '/api/faucet', faucet_data)
    if result['status'] != 'success':
        print(f"❌ Faucet request failed: {result['message']}")
        return
    
    tx_hash = result['data']['transaction_hash']
    print(f"✅ Faucet request successful!")
    print(f"📝 Transaction hash: {tx_hash}")
    
    # Step 4: Check pending transactions
    print(f"\n4️⃣ Checking pending transactions...")
    result = make_request('GET', '/api/transactions/pending')
    if result['status'] == 'success':
        pending_count = result['data']['count']
        print(f"⏳ Pending transactions: {pending_count}")
        if pending_count > 0:
            print("📋 Pending transaction details:")
            for tx in result['data']['transactions']:
                print(f"  - Hash: {tx['hash'][:16]}...")
                print(f"    From: {tx['from_address']}")
                print(f"    To: {tx['to_address']}")
                print(f"    Amount: {tx['amount']}")
    else:
        print(f"❌ Failed to get pending transactions: {result['message']}")
    
    # Step 5: Manually mine a block
    print(f"\n5️⃣ Mining a block to process pending transactions...")
    result = make_request('POST', '/api/mining/mine')
    if result['status'] != 'success':
        print(f"❌ Mining failed: {result['message']}")
        return
    
    mine_data = result['data']
    print(f"✅ {mine_data['message']}")
    print(f"📦 Block hash: {mine_data['block_hash'][:16]}...")
    print(f"💸 Transactions processed: {mine_data['transactions_processed']}")
    print(f"⏳ Pending remaining: {mine_data['pending_remaining']}")
    
    # Step 6: Check final balance
    print(f"\n6️⃣ Checking final balance...")
    time.sleep(1)  # Give a moment for processing
    result = make_request('GET', f'/api/accounts/{address}/balance')
    if result['status'] == 'success':
        balance = result['data']['balance']
        print(f"💰 Final balance: {balance}")
        if balance == 100.0:
            print("🎉 Success! Faucet and mining working correctly!")
        else:
            print(f"⚠️ Unexpected balance: expected 100.0, got {balance}")
    else:
        print(f"❌ Failed to get final balance: {result['message']}")
    
    # Step 7: Check blockchain status
    print(f"\n7️⃣ Checking blockchain status...")
    result = make_request('GET', '/api/status')
    if result['status'] == 'success':
        data = result['data']
        print(f"📊 Chain length: {data['chain_length']}")
        print(f"⏳ Pending transactions: {data['pending_transactions']}")
        print(f"⚡ Validators: {data['validators']}")
        print(f"🔧 Contracts: {data['contracts']}")
    else:
        print(f"❌ Failed to get status: {result['message']}")

if __name__ == '__main__':
    test_faucet_and_mining() 