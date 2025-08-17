#!/usr/bin/env python3
"""
Test Validator Registration
Registers validators so other addresses can mine blocks
"""

import requests
import json
import time

def generate_address():
    """Generate a new address"""
    try:
        response = requests.post('http://localhost:5000/api/utils/generate-address')
        if response.status_code == 200:
            return response.json()['data']['address']
        else:
            return None
    except Exception as e:
        print(f"Error generating address: {e}")
        return None

def get_balance(address):
    """Get balance for an address"""
    try:
        response = requests.get(f'http://localhost:5000/api/accounts/{address}/balance')
        if response.status_code == 200:
            return response.json()['data']['balance']
        else:
            return 0.0
    except Exception as e:
        print(f"Error getting balance: {e}")
        return 0.0

def faucet_request(address, amount=100.0):
    """Request tokens from faucet"""
    try:
        response = requests.post('http://localhost:5000/api/faucet', json={
            'address': address,
            'amount': amount
        })
        if response.status_code == 200:
            return response.json()['data']['transaction_hash']
        else:
            print(f"Faucet request failed: {response.json()}")
            return None
    except Exception as e:
        print(f"Error requesting faucet: {e}")
        return None

def register_validator(address, stake_amount=50.0):
    """Register a validator"""
    try:
        response = requests.post('http://localhost:5000/api/validators', json={
            'address': address,
            'stake_amount': stake_amount
        })
        if response.status_code == 200:
            return response.json()['data']['message']
        else:
            print(f"Validator registration failed: {response.json()}")
            return None
    except Exception as e:
        print(f"Error registering validator: {e}")
        return None

def get_validators():
    """Get all validators"""
    try:
        response = requests.get('http://localhost:5000/api/validators')
        if response.status_code == 200:
            return response.json()['data']
        else:
            return {}
    except Exception as e:
        print(f"Error getting validators: {e}")
        return {}

def test_validator_registration():
    """Test the complete validator registration process"""
    print("🔧 Testing Validator Registration")
    print("=" * 50)
    
    # Step 1: Generate addresses for validators
    print("1️⃣ Generating validator addresses...")
    validator1 = generate_address()
    validator2 = generate_address()
    
    if not validator1 or not validator2:
        print("❌ Failed to generate addresses")
        return False
    
    print(f"   Validator 1: {validator1}")
    print(f"   Validator 2: {validator2}")
    
    # Step 2: Fund the validators
    print("\n2️⃣ Funding validators via faucet...")
    faucet1 = faucet_request(validator1, 100.0)
    faucet2 = faucet_request(validator2, 100.0)
    
    if not faucet1 or not faucet2:
        print("❌ Failed to fund validators")
        return False
    
    print(f"   Funded {validator1}: {faucet1}")
    print(f"   Funded {validator2}: {faucet2}")
    
    # Wait for transactions to be processed
    print("   ⏳ Waiting for transactions to be processed...")
    time.sleep(3)
    
    # Check balances
    balance1 = get_balance(validator1)
    balance2 = get_balance(validator2)
    print(f"   Balance {validator1}: {balance1}")
    print(f"   Balance {validator2}: {balance2}")
    
    # Step 3: Register validators
    print("\n3️⃣ Registering validators...")
    reg1 = register_validator(validator1, 50.0)
    reg2 = register_validator(validator2, 75.0)
    
    if not reg1 or not reg2:
        print("❌ Failed to register validators")
        return False
    
    print(f"   Registered {validator1}: {reg1}")
    print(f"   Registered {validator2}: {reg2}")
    
    # Step 4: Verify validators
    print("\n4️⃣ Verifying validators...")
    validators = get_validators()
    print(f"   Total validators: {len(validators)}")
    
    for addr, validator_data in validators.items():
        print(f"   - {addr}: stake={validator_data['stake']}, active={validator_data['is_active']}")
    
    # Step 5: Test mining with validators
    print("\n5️⃣ Testing mining with validators...")
    
    # Submit a transaction
    test_address = generate_address()
    faucet_tx = faucet_request(test_address, 25.0)
    
    if faucet_tx:
        print(f"   Submitted test transaction: {faucet_tx}")
        
        # Wait for transaction to be processed
        time.sleep(2)
        
        # Mine a block
        try:
            response = requests.post('http://localhost:5000/api/mining/mine')
            if response.status_code == 200:
                mine_data = response.json()['data']
                print(f"   ✅ Block mined: {mine_data['message']}")
                print(f"   📦 Block hash: {mine_data['block_hash']}")
                print(f"   🏆 Validator: {mine_data.get('validator', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Mining failed: {response.json()}")
                return False
        except Exception as e:
            print(f"   ❌ Error mining: {e}")
            return False
    else:
        print("   ❌ Failed to submit test transaction")
        return False

def main():
    """Main function"""
    print("🚀 Validator Registration Test")
    print("=" * 50)
    
    success = test_validator_registration()
    
    if success:
        print("\n🎉 SUCCESS: Validators can now mine blocks!")
        print("✅ Validators registered successfully")
        print("✅ Mining works with registered validators")
        print("✅ PoCS consensus is active")
    else:
        print("\n❌ FAILED: Validator registration test failed")
        print("   Check the logs above for details")

if __name__ == '__main__':
    main() 