#!/usr/bin/env python3
"""
Complete Blockchain Flow Test
Demonstrates faucet, transactions, validators, and mining
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

def test_complete_flow():
    """Test the complete blockchain flow"""
    print("🚀 Complete Blockchain Flow Test")
    print("=" * 60)
    
    # Step 1: Generate addresses
    print("\n1️⃣ Generating addresses...")
    addresses = []
    for i in range(3):
        result = make_request('POST', '/api/utils/generate-address')
        if result['status'] == 'success':
            address = result['data']['address']
            addresses.append(address)
            print(f"   Address {i+1}: {address}")
        else:
            print(f"❌ Failed to generate address {i+1}: {result['message']}")
            return
    
    alice, bob, charlie = addresses
    
    # Step 2: Fund addresses
    print(f"\n2️⃣ Funding addresses...")
    for i, address in enumerate([alice, bob, charlie]):
        result = make_request('POST', '/api/faucet', {'address': address, 'amount': 200.0})
        if result['status'] == 'success':
            print(f"   ✅ Funded {address[:16]}... with 200 tokens")
        else:
            print(f"❌ Failed to fund {address}: {result['message']}")
            return
    
    # Step 3: Mine to process faucet transactions
    print(f"\n3️⃣ Mining faucet transactions...")
    result = make_request('POST', '/api/mining/mine')
    if result['status'] == 'success':
        print(f"   ✅ {result['data']['message']}")
        print(f"   📦 Block hash: {result['data']['block_hash'][:16]}...")
    else:
        print(f"❌ Mining failed: {result['message']}")
        return
    
    # Step 4: Check balances
    print(f"\n4️⃣ Checking balances...")
    for i, address in enumerate([alice, bob, charlie]):
        result = make_request('GET', f'/api/accounts/{address}/balance')
        if result['status'] == 'success':
            balance = result['data']['balance']
            print(f"   💰 {address[:16]}...: {balance} tokens")
        else:
            print(f"❌ Failed to get balance for {address}: {result['message']}")
    
    # Step 5: Send transactions between addresses
    print(f"\n5️⃣ Testing transactions...")
    
    # Alice sends to Bob
    tx_data = {
        'from_address': alice,
        'to_address': bob,
        'amount': 50.0,
        'transaction_type': 'transfer',
        'gas_limit': 21000,
        'gas_price': 1.0
    }
    result = make_request('POST', '/api/transactions', tx_data)
    if result['status'] == 'success':
        print(f"   ✅ Alice → Bob: 50 tokens")
    else:
        print(f"❌ Alice → Bob failed: {result['message']}")
    
    # Bob sends to Charlie
    tx_data = {
        'from_address': bob,
        'to_address': charlie,
        'amount': 30.0,
        'transaction_type': 'transfer',
        'gas_limit': 21000,
        'gas_price': 1.0
    }
    result = make_request('POST', '/api/transactions', tx_data)
    if result['status'] == 'success':
        print(f"   ✅ Bob → Charlie: 30 tokens")
    else:
        print(f"❌ Bob → Charlie failed: {result['message']}")
    
    # Step 6: Mine transactions
    print(f"\n6️⃣ Mining transactions...")
    result = make_request('POST', '/api/mining/mine')
    if result['status'] == 'success':
        print(f"   ✅ {result['data']['message']}")
        print(f"   💸 Transactions processed: {result['data']['transactions_processed']}")
    else:
        print(f"❌ Mining failed: {result['message']}")
        return
    
    # Step 7: Check final balances
    print(f"\n7️⃣ Final balances...")
    for i, address in enumerate([alice, bob, charlie]):
        result = make_request('GET', f'/api/accounts/{address}/balance')
        if result['status'] == 'success':
            balance = result['data']['balance']
            print(f"   💰 {address[:16]}...: {balance} tokens")
        else:
            print(f"❌ Failed to get balance for {address}: {result['message']}")
    
    # Step 8: Register validators
    print(f"\n8️⃣ Registering validators...")
    
    # Alice stakes to become validator
    stake_data = {
        'from_address': alice,
        'to_address': 'stake_pool',
        'amount': 100.0,
        'transaction_type': 'stake',
        'gas_limit': 21000,
        'gas_price': 1.0
    }
    result = make_request('POST', '/api/transactions', stake_data)
    if result['status'] == 'success':
        print(f"   ✅ Alice staked 100 tokens")
    else:
        print(f"❌ Alice staking failed: {result['message']}")
    
    # Bob stakes to become validator
    stake_data = {
        'from_address': bob,
        'to_address': 'stake_pool',
        'amount': 80.0,
        'transaction_type': 'stake',
        'gas_limit': 21000,
        'gas_price': 1.0
    }
    result = make_request('POST', '/api/transactions', stake_data)
    if result['status'] == 'success':
        print(f"   ✅ Bob staked 80 tokens")
    else:
        print(f"❌ Bob staking failed: {result['message']}")
    
    # Step 9: Mine validator registrations
    print(f"\n9️⃣ Mining validator registrations...")
    result = make_request('POST', '/api/mining/mine')
    if result['status'] == 'success':
        print(f"   ✅ {result['data']['message']}")
    else:
        print(f"❌ Mining failed: {result['message']}")
        return
    
    # Step 10: Check validators
    print(f"\n🔟 Checking validators...")
    result = make_request('GET', '/api/validators')
    if result['status'] == 'success':
        validators = result['data']
        print(f"   ⚡ Total validators: {len(validators)}")
        for addr, validator in validators.items():
            print(f"   📍 {addr[:16]}...: {validator['stake']} stake, {validator.get('reputation_score', 0):.1f} reputation")
    else:
        print(f"❌ Failed to get validators: {result['message']}")
    
    # Step 11: Final blockchain status
    print(f"\n1️⃣1️⃣ Final blockchain status...")
    result = make_request('GET', '/api/status')
    if result['status'] == 'success':
        data = result['data']
        print(f"   📊 Chain length: {data['chain_length']}")
        print(f"   ⏳ Pending transactions: {data['pending_transactions']}")
        print(f"   ⚡ Validators: {data['validators']}")
        print(f"   🔧 Contracts: {data['contracts']}")
        
        if data['validators'] > 0:
            print("🎉 SUCCESS! Validators are now active!")
        else:
            print("⚠️ No validators registered yet")
    else:
        print(f"❌ Failed to get status: {result['message']}")

if __name__ == '__main__':
    test_complete_flow() 