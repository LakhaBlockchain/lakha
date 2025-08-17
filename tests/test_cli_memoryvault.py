#!/usr/bin/env python3
"""
Test CLI MemoryVault Functionality
Demonstrates the new interactive MemoryVault wallet generation
"""

import subprocess
import sys
import time

def test_cli_memoryvault():
    """Test the CLI MemoryVault functionality"""
    
    print("🎭 Testing CLI MemoryVault Integration")
    print("=" * 50)
    print()
    
    # Test 1: Show help
    print("1. Testing CLI help...")
    try:
        result = subprocess.run(['python', 'cli.py', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ CLI help works")
            if 'generate-memoryvault-wallet' in result.stdout:
                print("✅ MemoryVault commands found in help")
            else:
                print("❌ MemoryVault commands not found in help")
        else:
            print(f"❌ CLI help failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error testing CLI help: {e}")
    
    print()
    
    # Test 2: Check if API is running
    print("2. Checking API status...")
    try:
        import requests
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API is not responding correctly")
    except Exception as e:
        print(f"❌ API check failed: {e}")
        print("   Please start the API server: python api.py --port 5000")
        return
    
    print()
    
    # Test 3: Test MemoryVault validation
    print("3. Testing MemoryVault story validation...")
    test_story = """
    When I was 8, my first pet was a goldfish named Bubbles because he always made 
    bubble sounds. I kept him in a secret spot behind my toy box in my room. One day, 
    I accidentally spilled my juice on the floor and had to hide it from my mom by 
    putting a blanket over it. That's when I learned that honesty is better than 
    hiding things, and I created my secret handshake with my sister using three 
    high-fives and a fist bump. Now whenever I feel stressed, I go to my secret spot 
    in the corner of my garden and remember that moment with Bubbles.
    """
    
    try:
        import requests
        response = requests.post('http://localhost:5000/api/memoryvault/validate-story', 
                               json={'story': test_story})
        if response.status_code == 200:
            data = response.json()['data']
            print(f"✅ Story validation works")
            print(f"   Personalness Score: {data['personalness_score']:.2f}")
            print(f"   Personal Elements: {data['personal_elements_count']}")
        else:
            print(f"❌ Story validation failed: {response.text}")
    except Exception as e:
        print(f"❌ Story validation error: {e}")
    
    print()
    
    # Test 4: Test funded wallet creation
    print("4. Testing funded wallet creation...")
    try:
        import requests
        response = requests.post('http://localhost:5000/api/memoryvault/create-funded-wallet', 
                               json={'story': test_story, 'funding_amount': 50.0})
        if response.status_code == 200:
            data = response.json()['data']
            print(f"✅ Funded wallet creation works")
            print(f"   Address: {data['address']}")
            print(f"   Mnemonic: {data['mnemonic'][:50]}...")
            if data.get('funding', {}).get('funded'):
                print(f"   Funding: {data['funding']['amount']} LAK tokens")
                print(f"   Transaction: {data['funding']['transaction_hash']}")
            else:
                print(f"   Funding failed: {data['funding'].get('error', 'Unknown')}")
        else:
            print(f"❌ Funded wallet creation failed: {response.text}")
    except Exception as e:
        print(f"❌ Funded wallet creation error: {e}")
    
    print()
    print("=" * 50)
    print("🎉 CLI MemoryVault Test Complete!")
    print()
    print("📋 Manual Testing Instructions:")
    print("1. Generate a MemoryVault wallet:")
    print("   python cli.py generate-memoryvault-wallet")
    print()
    print("2. Recover a MemoryVault wallet:")
    print("   python cli.py recover-memoryvault-wallet")
    print()
    print("3. Check wallet balance:")
    print("   python cli.py balance <address>")
    print()
    print("💡 The CLI will guide you through:")
    print("   • Interactive story collection")
    print("   • Story personalness validation")
    print("   • Automatic wallet funding")
    print("   • Secure wallet information storage")
    print("   • Dual recovery methods (story + mnemonic)")

if __name__ == "__main__":
    test_cli_memoryvault() 