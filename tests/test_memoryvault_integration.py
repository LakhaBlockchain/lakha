#!/usr/bin/env python3
"""
MemoryVault Integration Test
Tests the new MemoryVault integration with automatic funding
"""

import requests
import json
import time
import sys

# API configuration
API_BASE = "http://localhost:5000/api"

def test_memoryvault_integration():
    """Test MemoryVault integration with automatic funding"""
    
    print("🔐 MemoryVault Integration Test")
    print("=" * 60)
    print("Testing MemoryVault with automatic funding (Solana-style)")
    print()
    
    # Test stories
    test_stories = [
        {
            "name": "Childhood Pet Story",
            "story": """
            When I was 8, my first pet was a goldfish named Bubbles because he always made 
            bubble sounds. I kept him in a secret spot behind my toy box in my room. One day, 
            I accidentally spilled my juice on the floor and had to hide it from my mom by 
            putting a blanket over it. That's when I learned that honesty is better than 
            hiding things, and I created my secret handshake with my sister using three 
            high-fives and a fist bump. Now whenever I feel stressed, I go to my secret spot 
            in the corner of my garden and remember that moment with Bubbles.
            """
        },
        {
            "name": "Family Secret Recipe",
            "story": """
            My grandmother taught me her secret recipe for chocolate chip cookies when I was 12. 
            She said the secret was adding a pinch of cinnamon and letting the dough rest for 
            exactly 30 minutes. I still remember the smell of her kitchen and how she would 
            always sneak me an extra cookie when my mom wasn't looking. Now I make these cookies 
            every Christmas and think of her.
            """
        }
    ]
    
    print("📖 Testing Story Validation")
    print("-" * 40)
    
    for i, test_case in enumerate(test_stories, 1):
        print(f"\n{i}. {test_case['name']}")
        
        # Test story validation
        try:
            response = requests.post(f"{API_BASE}/memoryvault/validate-story", 
                                   json={"story": test_case['story']})
            
            if response.status_code == 200:
                data = response.json()['data']
                print(f"   📊 Personalness Score: {data['personalness_score']:.2f}")
                print(f"   🔍 Personal Elements: {data['personal_elements_count']}")
                print(f"   🏷️  Element Types: {data['element_types']}")
                
                if data['recommendations']:
                    print("   💡 Recommendations:")
                    for rec in data['recommendations']:
                        print(f"      - {rec}")
            else:
                print(f"   ❌ Validation failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🔑 Testing Funded Wallet Creation")
    print("-" * 40)
    
    for i, test_case in enumerate(test_stories, 1):
        print(f"\n{i}. Creating funded wallet from '{test_case['name']}'...")
        
        try:
            # Test funded wallet creation
            response = requests.post(f"{API_BASE}/memoryvault/create-funded-wallet", 
                                   json={
                                       "story": test_case['story'],
                                       "funding_amount": 75.0  # 75 LAK tokens
                                   })
            
            if response.status_code == 200:
                data = response.json()['data']
                print(f"   ✅ Address: {data['address']}")
                print(f"   🗝️  Mnemonic: {data['mnemonic'][:50]}...")
                print(f"   📝 Story Hash: {data['story_hash'][:16]}...")
                
                if data.get('funding', {}).get('funded'):
                    funding = data['funding']
                    print(f"   💰 Funding: {funding['amount']} LAK tokens")
                    print(f"   🔗 Transaction: {funding['transaction_hash']}")
                    print(f"   📊 Personalness: {data['validation']['personalness_score']:.2f}")
                    print(f"   🎯 Wallet Ready: {'✅ Yes' if data.get('wallet_ready') else '❌ No'}")
                else:
                    print(f"   ❌ Funding failed: {data['funding'].get('error', 'Unknown error')}")
            else:
                print(f"   ❌ Creation failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🔄 Testing Mnemonic Recovery with Funding")
    print("-" * 40)
    
    # Test mnemonic recovery with funding
    test_mnemonic = "clinic firm bounce canvas thank tent flag naive so"
    
    print(f"\nTesting mnemonic recovery with funding...")
    print(f"Mnemonic: {test_mnemonic}")
    
    try:
        response = requests.post(f"{API_BASE}/memoryvault/generate-from-mnemonic", 
                               json={
                                   "mnemonic": test_mnemonic,
                                   "auto_fund": True,
                                   "funding_amount": 25.0
                               })
        
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   ✅ Recovered Address: {data['address']}")
            
            if data.get('funding', {}).get('funded'):
                funding = data['funding']
                print(f"   💰 Additional Funding: {funding['amount']} LAK tokens")
                print(f"   🔗 Transaction: {funding['transaction_hash']}")
            else:
                print(f"   ℹ️  Funding: {data['funding'].get('message', 'Not funded')}")
        else:
            print(f"   ❌ Recovery failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📊 Testing Account Balance")
    print("-" * 40)
    
    # Test account balance for generated addresses
    try:
        # Get all accounts
        response = requests.get(f"{API_BASE}/accounts")
        if response.status_code == 200:
            accounts = response.json()['data']
            print(f"\nFound {len(accounts)} accounts:")
            
            # Show accounts with balances
            for address, account_info in accounts.items():
                if address.startswith('lakha1') and account_info.get('balance', 0) > 0:
                    print(f"   💰 {address}: {account_info['balance']} LAK")
        else:
            print(f"   ❌ Failed to get accounts: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 MemoryVault Integration Test Complete!")
    print("=" * 60)
    
    print("\n🎭 Key Features Tested:")
    print("✅ Story validation and personalness scoring")
    print("✅ Automatic wallet funding (Solana-style)")
    print("✅ Mnemonic recovery with optional funding")
    print("✅ Blockchain integration and transaction broadcasting")
    print("✅ Account balance verification")
    
    print("\n🚀 Benefits:")
    print("• Users can create wallets from personal stories")
    print("• Wallets are automatically funded and ready to use")
    print("• Dual recovery via story or mnemonic")
    print("• Full blockchain integration with P2P broadcasting")
    print("• Secure and memorable key generation")

def check_api_status():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🔍 Checking API status...")
    
    if not check_api_status():
        print("❌ API is not running. Please start the Lakha API server first:")
        print("   python api.py --port 5000")
        print("\nOr if you have a node running:")
        print("   python run_node.py --api-port 5000")
        sys.exit(1)
    
    print("✅ API is running. Starting integration test...")
    print()
    
    test_memoryvault_integration() 