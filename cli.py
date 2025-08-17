#!/usr/bin/env python3
"""
Lakha Blockchain CLI Tool
Command-line interface for blockchain interaction
"""

import argparse
import json
import sys
import time
from typing import Dict, Any
from core import (
    LahkaBlockchain, Transaction, TransactionType,
    generate_address, is_valid_address
)
import requests

class LakhaCLI:
    """Command-line interface for Lakha blockchain"""
    
    def __init__(self, api_url='http://localhost:5000', api_key=None):
        self.api_url = api_url
        self.api_key = api_key
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to API"""
        url = f"{self.api_url}{endpoint}"
        headers = {}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
            
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def status(self):
        """Get blockchain status"""
        result = self._make_request('GET', '/api/status')
        if result.get('status') == 'success':
            data = result['data']
            print("🚀 Lakha Blockchain Status")
            print("=" * 40)
            print(f"Chain Length: {data['chain_length']}")
            print(f"Pending Transactions: {data['pending_transactions']}")
            print(f"Validators: {data['validators']}")
            print(f"Contracts: {data['contracts']}")
            print(f"Latest Block: #{data['latest_block']['index']}")
            print(f"Latest Block Hash: {data['latest_block']['hash'][:16]}...")
            
            if 'network_performance' in data:
                perf = data['network_performance']
                print(f"\n📊 Network Performance:")
                print(f"  Total Validators: {perf.get('total_validators', 0)}")
                print(f"  Active Validators: {perf.get('active_validators', 0)}")
                print(f"  Total Stake: {perf.get('total_stake', 0):.2f}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def blocks(self, page=1, limit=10):
        """List blocks"""
        result = self._make_request('GET', f'/api/blocks?page={page}&limit={limit}')
        if result.get('status') == 'success':
            data = result['data']
            print(f"📦 Blocks (Page {data['page']}, {data['total']} total)")
            print("=" * 50)
            
            for block in data['blocks']:
                print(f"Block #{block['index']}")
                print(f"  Hash: {block['hash'][:16]}...")
                print(f"  Validator: {block['validator']}")
                print(f"  Transactions: {len(block['transactions'])}")
                print(f"  Timestamp: {time.ctime(block['timestamp'])}")
                print()
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def transactions(self, page=1, limit=10):
        """List transactions"""
        result = self._make_request('GET', f'/api/transactions?page={page}&limit={limit}')
        if result.get('status') == 'success':
            data = result['data']
            print(f"💸 Transactions (Page {data['page']}, {data['total']} total)")
            print("=" * 50)
            
            for tx in data['transactions']:
                print(f"Hash: {tx['hash'][:16]}...")
                print(f"  From: {tx['from_address']}")
                print(f"  To: {tx['to_address']}")
                print(f"  Amount: {tx['amount']}")
                print(f"  Type: {tx['transaction_type']}")
                print(f"  Timestamp: {time.ctime(tx['timestamp'])}")
                print()
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def pending(self):
        """Show pending transactions"""
        result = self._make_request('GET', '/api/transactions/pending')
        if result.get('status') == 'success':
            data = result['data']
            print(f"⏳ Pending Transactions ({data['count']})")
            print("=" * 40)
            
            for tx in data['transactions']:
                print(f"Hash: {tx['hash'][:16]}...")
                print(f"  From: {tx['from_address']}")
                print(f"  To: {tx['to_address']}")
                print(f"  Amount: {tx['amount']}")
                print(f"  Type: {tx['transaction_type']}")
                print()
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def account(self, address):
        """Show account details"""
        result = self._make_request('GET', f'/api/accounts/{address}')
        if result.get('status') == 'success':
            data = result['data']
            account = data['account']
            history = data['history']
            
            print(f"👤 Account: {address}")
            print("=" * 40)
            print(f"Balance: {account['balance']}")
            print(f"Nonce: {account['nonce']}")
            print(f"Is Contract: {account['is_contract']}")
            print(f"Created: {time.ctime(account['created_at'])}")
            print(f"Updated: {time.ctime(account['last_updated'])}")
            
            if history:
                print(f"\n📜 Recent History ({len(history)} transactions):")
                for entry in history[-5:]:  # Show last 5 transactions
                    print(f"  {entry['transaction_type']}: {entry['amount']} (Block #{entry['block_number']})")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def balance(self, address):
        """Show account balance"""
        result = self._make_request('GET', f'/api/accounts/{address}/balance')
        if result.get('status') == 'success':
            data = result['data']
            print(f"💰 Balance for {data['address']}: {data['balance']}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def send(self, from_addr, to_addr, amount, tx_type='transfer', authority_file=None):
        """Send a transaction with proper signing using authority file"""
        print(f"💸 Sending {amount} LAK from {from_addr} to {to_addr}")
        
        # Get the sender's nonce
        nonce_result = self._make_request('GET', f'/api/accounts/{from_addr}/nonce')
        if nonce_result.get('status') != 'success':
            print(f"Error getting nonce for {from_addr}: {nonce_result.get('message', 'Unknown error')}")
            return
        
        nonce = nonce_result['data']['nonce']
        
        # Validate the recipient address
        validate_result = self._make_request('POST', '/api/utils/validate-address', {'address': to_addr})
        if validate_result.get('status') != 'success' or not validate_result['data']['is_valid']:
            print(f"❌ Invalid recipient address '{to_addr}'")
            return
        
        # Get private key from authority file
        private_key = self._get_private_key_from_authority(from_addr, authority_file)
        if not private_key:
            print("❌ No private key found in authority file")
            return
        
        # Create and sign transaction
        try:
            from core import Transaction, TransactionType
            import hashlib
            import time
            
            # Create transaction
            tx = Transaction(
                from_address=from_addr,
                to_address=to_addr,
                amount=float(amount),
                transaction_type=TransactionType(tx_type),
                gas_limit=21000,
                gas_price=1.0,
                nonce=nonce,
                timestamp=time.time()
            )
            
            # Sign transaction
            tx_data = f"{tx.from_address}{tx.to_address}{tx.amount}{tx.transaction_type.value}{tx.gas_limit}{tx.gas_price}{tx.nonce}{tx.timestamp}"
            signature = self._sign_data(tx_data, private_key)
            tx.signature = signature
            
            # Submit signed transaction
            tx_data = {
                'from_address': tx.from_address,
                'to_address': tx.to_address,
                'amount': tx.amount,
                'transaction_type': tx.transaction_type.value,
                'gas_limit': tx.gas_limit,
                'gas_price': tx.gas_price,
                'nonce': tx.nonce,
                'signature': tx.signature,
                'timestamp': tx.timestamp
            }
            
            result = self._make_request('POST', '/api/transactions', tx_data)
            if result.get('status') == 'success':
                data = result['data']
                print(f"✅ Transaction signed and submitted successfully!")
                print(f"Hash: {data['transaction_hash']}")
                print(f"From: {from_addr}")
                print(f"To: {to_addr}")
                print(f"Amount: {amount}")
                print(f"Signature: {signature[:16]}...")
            else:
                print(f"❌ Transaction failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error creating transaction: {e}")
    
    def _get_private_key_from_authority(self, address, authority_file=None):
        """Get private key from authority file"""
        if not authority_file:
            # Try to find wallet file automatically
            authority_file = self._find_wallet_file(address)
            if not authority_file:
                print(f"❌ No authority file found for address {address}")
                print("Please specify an authority file with --authority-file")
                return None
        
        try:
            with open(authority_file, 'r') as f:
                wallet_data = json.load(f)
                
            # Verify the address matches
            if wallet_data.get('address') != address:
                print(f"❌ Authority file address ({wallet_data.get('address')}) doesn't match transaction address ({address})")
                return None
            
            return wallet_data.get('private_key')
            
        except FileNotFoundError:
            print(f"❌ Authority file not found: {authority_file}")
            return None
        except json.JSONDecodeError:
            print(f"❌ Invalid authority file format: {authority_file}")
            return None
        except Exception as e:
            print(f"❌ Error reading authority file: {e}")
            return None
    
    def _sign_data(self, data, private_key):
        """Sign data with private key"""
        try:
            import hashlib
            # Simple signing for now - in production use proper ECDSA
            message = data.encode()
            key = private_key.encode()
            signature = hashlib.sha256(message + key).hexdigest()
            return signature
        except Exception as e:
            print(f"❌ Error signing data: {e}")
            return None
    
    def _find_wallet_file(self, address):
        """Find wallet file for given address"""
        import os
        import glob
        
        # Look for wallet files in current directory
        wallet_files = glob.glob("memoryvault_wallet_*.json")
        
        for file in wallet_files:
            try:
                with open(file, 'r') as f:
                    wallet_data = json.load(f)
                    if wallet_data.get('address') == address:
                        return file
            except:
                continue
        
        return None
    
    def faucet(self, address, amount=100):
        """Request tokens from faucet"""
        data = {
            'address': address,
            'amount': float(amount)
        }
        
        result = self._make_request('POST', '/api/faucet', data)
        if result.get('status') == 'success':
            data = result['data']
            print(f"🚰 Faucet request successful!")
            print(f"Message: {data['message']}")
            print(f"Transaction Hash: {data['transaction_hash']}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def generate_address(self):
        """Generate a new address (legacy method - use MemoryVault instead)"""
        print("⚠️  Legacy address generation detected.")
        print("🎭 MemoryVault is now the recommended way to create wallets.")
        print()
        
        choice = input("Would you like to create a MemoryVault wallet instead? (y/n): ").strip().lower()
        
        if choice in ['y', 'yes']:
            self.generate_memoryvault_wallet()
        else:
            # Fallback to legacy generation
            result = self._make_request('POST', '/api/utils/generate-address')
            if result.get('status') == 'success':
                data = result['data']
                print(f"🔑 Generated legacy address: {data['address']}")
                print("💡 Consider using MemoryVault for better security and memorability.")
            else:
                print(f"Error: {result.get('message', 'Unknown error')}")
    
    def generate_memoryvault_wallet(self):
        """Generate a MemoryVault wallet from personal story"""
        print("🎭 MemoryVault - Create Wallet from Personal Story")
        print("=" * 60)
        print("Tell us a personal story to create your unique wallet.")
        print("The more personal and detailed your story, the stronger your wallet will be.")
        print()
        
        # Interactive story collection
        story = self._collect_story_interactive()
        
        if not story:
            print("❌ No story provided. Wallet generation cancelled.")
            return
        
        # Validate story personalness
        print("\n🔍 Validating your story...")
        validation_result = self._make_request('POST', '/api/memoryvault/validate-story', {'story': story})
        
        if validation_result.get('status') != 'success':
            print(f"❌ Story validation failed: {validation_result.get('message', 'Unknown error')}")
            return
        
        validation = validation_result['data']
        score = validation['personalness_score']
        
        print(f"📊 Personalness Score: {score:.2f}")
        print(f"🔍 Personal Elements: {validation['personal_elements_count']}")
        print(f"🏷️  Element Types: {validation['element_types']}")
        
        if validation['recommendations']:
            print("\n💡 Suggestions to improve your story:")
            for rec in validation['recommendations']:
                print(f"   - {rec}")
        
        # Check if story is personal enough
        if score < 0.5:
            print(f"\n⚠️  Your story personalness score ({score:.2f}) is below the recommended threshold (0.5).")
            print("Would you like to:")
            print("1. Try again with a more personal story")
            print("2. Continue anyway (wallet will be less secure)")
            print("3. Cancel wallet generation")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                print("\n" + "="*60)
                return self.generate_memoryvault_wallet()
            elif choice == '3':
                print("❌ Wallet generation cancelled.")
                return
            elif choice != '2':
                print("❌ Invalid choice. Wallet generation cancelled.")
                return
        
        # Create funded wallet
        print(f"\n🎯 Creating your MemoryVault wallet...")
        wallet_result = self._make_request('POST', '/api/memoryvault/create-funded-wallet', {
            'story': story,
            'funding_amount': 0.000001 # Changed funding amount to IBE
        })
        
        if wallet_result.get('status') != 'success':
            print(f"❌ Wallet creation failed: {wallet_result.get('message', 'Unknown error')}")
            return
        
        wallet_data = wallet_result['data']
        
        # Display wallet information
        print("\n" + "="*60)
        print("🎉 MemoryVault Wallet Created Successfully!")
        print("="*60)
        
        print(f"\n🔑 Wallet Address: {wallet_data['address']}")
        print(f"🗝️  Mnemonic Phrase: {wallet_data['mnemonic']}")
        print(f"📝 Story Hash: {wallet_data['story_hash'][:16]}...")
        print(f"🔍 Personal Elements: {wallet_data['personal_elements_count']}")
        print(f"📊 Personalness Score: {wallet_data['validation']['personalness_score']:.2f}")
        
        if wallet_data.get('funding', {}).get('funded'):
            funding = wallet_data['funding']
            print(f"\n💰 Initial Funding: {funding['amount']} LAK tokens")
            print(f"🔗 Funding Transaction: {funding['transaction_hash']}")
            print(f"✅ Wallet is ready to use!")
        else:
            print(f"\n⚠️  Funding failed: {wallet_data['funding'].get('error', 'Unknown error')}")
            print("You can manually fund this wallet using the faucet.")
        
        print(f"\n🔄 Recovery Methods:")
        print(f"   1. Story Recovery: Use your personal story to recover the wallet")
        print(f"   2. Mnemonic Recovery: Use the mnemonic phrase above")
        
        print(f"\n💡 Tips:")
        print(f"   • Keep your story private - it's your backup key")
        print(f"   • Store the mnemonic phrase securely")
        print(f"   • The more personal your story, the more secure your wallet")
        
        # Save wallet info to file
        self._save_wallet_info(wallet_data, story)
    
    def _collect_story_interactive(self):
        """Collect personal story interactively"""
        print("📖 Please tell us a personal story that's meaningful to you.")
        print("Include details like:")
        print("   • Names of people, pets, or places")
        print("   • Specific locations (rooms, houses, secret spots)")
        print("   • Emotions and feelings")
        print("   • Personal actions or discoveries")
        print("   • Family secrets or private moments")
        print()
        print("💡 Example: 'When I was 8, my first pet was a goldfish named Bubbles...'" )
        print()
        print("Enter your story (press Enter twice when finished):")
        
        lines = []
        while True:
            line = input()
            if line.strip() == "" and lines:  # Empty line and we have content
                break
            lines.append(line)
        
        story = "\n".join(lines).strip()
        return story if story else None
    
    def _save_wallet_info(self, wallet_data, story):
        """Save wallet information to a file"""
        try:
            import os
            from datetime import datetime
            
            filename = f"memoryvault_wallet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            wallet_info = {
                'created_at': datetime.now().isoformat(),
                'address': wallet_data['address'],
                'mnemonic': wallet_data['mnemonic'],
                'story_hash': wallet_data['story_hash'],
                'personal_elements_count': wallet_data['personal_elements_count'],
                'personalness_score': wallet_data['validation']['personalness_score'],
                'funding': wallet_data.get('funding', {}),
                'story': story,  # Include the original story for recovery
                'recovery_instructions': {
                    'story_recovery': 'Use the story above with MemoryVault recovery',
                    'mnemonic_recovery': 'Use the mnemonic phrase above with any BIP39 wallet'
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(wallet_info, f, indent=2)
            
            print(f"\n💾 Wallet information saved to: {filename}")
            print(f"   Keep this file secure - it contains your recovery information!")
            
        except Exception as e:
            print(f"\n⚠️  Warning: Could not save wallet info to file: {e}")
            print("   Please manually save your wallet information securely.")
    
    def recover_memoryvault_wallet(self):
        """Recover MemoryVault wallet from story or mnemonic"""
        print("🔄 MemoryVault - Recover Wallet")
        print("=" * 40)
        print("Choose recovery method:")
        print("1. Recover from personal story")
        print("2. Recover from mnemonic phrase")
        
        choice = input("\nEnter your choice (1-2): ").strip()
        
        if choice == '1':
            self._recover_from_story()
        elif choice == '2':
            self._recover_from_mnemonic()
        else:
            print("❌ Invalid choice.")
    
    def _recover_from_story(self):
        """Recover wallet from personal story"""
        print("\n📖 Story Recovery")
        print("-" * 20)
        print("Please enter your personal story exactly as you told it when creating the wallet:")
        
        story = self._collect_story_interactive()
        if not story:
            print("❌ No story provided.")
            return
        
        print("\n🔍 Recovering wallet from story...")
        result = self._make_request('POST', '/api/memoryvault/generate-from-story', {
            'story': story,
            'auto_fund': False  # Don't auto-fund during recovery
        })
        
        if result.get('status') == 'success':
            data = result['data']
            print(f"\n✅ Wallet recovered successfully!")
            print(f"🔑 Address: {data['address']}")
            print(f"🗝️  Mnemonic: {data['mnemonic']}")
            print(f"📝 Story Hash: {data['story_hash'][:16]}...")
        else:
            print(f"❌ Recovery failed: {result.get('message', 'Unknown error')}")
    
    def _recover_from_mnemonic(self):
        """Recover wallet from mnemonic phrase"""
        print("\n🗝️  Mnemonic Recovery")
        print("-" * 20)
        print("Please enter your mnemonic phrase:")
        
        mnemonic = input("Mnemonic: ").strip()
        if not mnemonic:
            print("❌ No mnemonic provided.")
            return
        
        print("\n🔍 Recovering wallet from mnemonic...")
        result = self._make_request('POST', '/api/memoryvault/generate-from-mnemonic', {
            'mnemonic': mnemonic,
            'auto_fund': False  # Don't auto-fund during recovery
        })
        
        if result.get('status') == 'success':
            data = result['data']
            print(f"\n✅ Wallet recovered successfully!")
            print(f"🔑 Address: {data['address']}")
            print(f"🗝️  Mnemonic: {data['mnemonic']}")
        else:
            print(f"❌ Recovery failed: {result.get('message', 'Unknown error')}")
    
    def validate_address(self, address):
        """Validate an address"""
        data = {'address': address}
        result = self._make_request('POST', '/api/utils/validate-address', data)
        if result.get('status') == 'success':
            data = result['data']
            if data['is_valid']:
                print(f"✅ Address {data['address']} is valid")
            else:
                print(f"❌ Address {data['address']} is invalid")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def validators(self):
        """List validators"""
        result = self._make_request('GET', '/api/validators')
        if result.get('status') == 'success':
            data = result['data']
            print(f"⚡ Validators ({len(data)} total)")
            print("=" * 40)
            
            for addr, validator in data.items():
                print(f"Address: {addr}")
                print(f"  Stake: {validator['stake']}")
                print(f"  Reputation: {validator.get('reputation_score', 0):.2f}")
                print(f"  Blocks Validated: {validator.get('blocks_validated', 0)}")
                print(f"  Is Active: {validator.get('is_active', True)}")
                print()
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def contracts(self):
        """List contracts"""
        result = self._make_request('GET', '/api/contracts')
        if result.get('status') == 'success':
            data = result['data']
            print(f"🔧 Smart Contracts ({len(data)} total)")
            print("=" * 40)
            
            for addr, contract in data.items():
                print(f"Address: {addr}")
                print(f"  Owner: {contract['owner']}")
                print(f"  Status: {contract['status']}")
                print(f"  Created: {time.ctime(contract['created_at'])}")
                print()
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def mining_status(self):
        """Show mining status"""
        result = self._make_request('GET', '/api/mining/status')
        if result.get('status') == 'success':
            data = result['data']
            status = "🟢 Active" if data['mining_active'] else "🔴 Inactive"
            print(f"⛏️ Mining Status: {status}")
            print(f"Pending Transactions: {data['pending_transactions']}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def start_mining(self):
        """Start mining"""
        result = self._make_request('POST', '/api/mining/start')
        if result.get('status') == 'success':
            print("⛏️ Mining started successfully!")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def stop_mining(self):
        """Stop mining"""
        result = self._make_request('POST', '/api/mining/stop')
        if result.get('status') == 'success':
            print("⛏️ Mining stopped successfully!")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def mine_block(self):
        """Manually mine a single block"""
        if not self.api_key:
            print("❌ API key is required to mine. Use --api-key.")
            return

        # Proceed with mining - the server will handle the logic
        # of using the genesis miner if no other validators are present.
        result = self._make_request('POST', '/api/mining/mine')
        if result.get('status') == 'success':
            data = result['data']
            print(f"⛏️ {data.get('message', 'Block mined successfully!')}")
            if 'block_hash' in data:
                print(f"Block Hash: {data['block_hash'][:16]}...")
                print(f"Transactions Processed: {data['transactions_processed']}")
                print(f"Pending Remaining: {data['pending_remaining']}")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
    
    def create_validator_wallet(self):
        """Create a MemoryVault wallet specifically for validator staking"""
        print("⚡ MemoryVault - Create Validator Wallet")
        print("=" * 50)
        print("Create a wallet that will be used for validator staking.")
        print("This wallet will be funded with LAK tokens for staking.")
        print()
        
        # Interactive story collection
        story = self._collect_story_interactive()
        
        if not story:
            print("❌ No story provided. Validator wallet creation cancelled.")
            return
        
        # Validate story personalness
        print("\n🔍 Validating your story...")
        validation_result = self._make_request('POST', '/api/memoryvault/validate-story', {'story': story})
        
        if validation_result.get('status') != 'success':
            print(f"❌ Story validation failed: {validation_result.get('message', 'Unknown error')}")
            return
        
        validation = validation_result['data']
        score = validation['personalness_score']
        
        print(f"📊 Personalness Score: {score:.2f}")
        print(f"🔍 Personal Elements: {validation['personal_elements_count']}")
        print(f"🏷️  Element Types: {validation['element_types']}")
        
        if validation['recommendations']:
            print("\n💡 Suggestions to improve your story:")
            for rec in validation['recommendations']:
                print(f"   - {rec}")
        
        # Check if story is personal enough
        if score < 0.5:
            print(f"\n⚠️  Your story personalness score ({score:.2f}) is below the recommended threshold (0.5).")
            print("Would you like to:")
            print("1. Try again with a more personal story")
            print("2. Continue anyway (wallet will be less secure)")
            print("3. Cancel validator wallet creation")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                print("\n" + "="*50)
                return self.create_validator_wallet()
            elif choice == '3':
                print("❌ Validator wallet creation cancelled.")
                return
            elif choice != '2':
                print("❌ Invalid choice. Validator wallet creation cancelled.")
                return
        
        # Create funded wallet with more LAK for staking
        print(f"\n🎯 Creating your validator wallet...")
        wallet_result = self._make_request('POST', '/api/memoryvault/create-funded-wallet', {
            'story': story,
            'funding_amount': 1000.0  # Fund with 1000 LAK for staking
        })
        
        if wallet_result.get('status') != 'success':
            print(f"❌ Validator wallet creation failed: {wallet_result.get('message', 'Unknown error')}")
            return
        
        wallet_data = wallet_result['data']
        
        # Display wallet information
        print("\n" + "="*50)
        print("🎉 Validator Wallet Created Successfully!")
        print("="*50)
        
        print(f"\n🔑 Wallet Address: {wallet_data['address']}")
        print(f"🗝️  Mnemonic Phrase: {wallet_data['mnemonic']}")
        print(f"📝 Story Hash: {wallet_data['story_hash'][:16]}...")
        print(f"🔍 Personal Elements: {wallet_data['personal_elements_count']}")
        print(f"📊 Personalness Score: {wallet_data['validation']['personalness_score']:.2f}")
        
        if wallet_data.get('funding', {}).get('funded'):
            funding = wallet_data['funding']
            print(f"\n💰 Initial Funding: {funding['amount']} LAK tokens")
            print(f"🔗 Funding Transaction: {funding['transaction_hash']}")
            print(f"✅ Wallet is ready for staking!")
        else:
            print(f"\n⚠️  Funding failed: {wallet_data['funding'].get('error', 'Unknown error')}")
            print("You can manually fund this wallet using the faucet.")
        
        print(f"\n🔄 Recovery Methods:")
        print(f"   1. Story Recovery: Use your personal story to recover the wallet")
        print(f"   2. Mnemonic Recovery: Use the mnemonic phrase above")
        
        print(f"\n💡 Next Steps:")
        print(f"   • Use this wallet to register as a validator")
        print(f"   • Keep your story private - it's your backup key")
        print(f"   • Store the mnemonic phrase securely")
        
        # Save wallet info to file with validator prefix
        self._save_validator_wallet_info(wallet_data, story)
    
    def _save_validator_wallet_info(self, wallet_data, story):
        """Save validator wallet information to a file"""
        try:
            import os
            from datetime import datetime
            
            filename = f"validator_wallet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            wallet_info = {
                'created_at': datetime.now().isoformat(),
                'wallet_type': 'validator',
                'address': wallet_data['address'],
                'mnemonic': wallet_data['mnemonic'],
                'story_hash': wallet_data['story_hash'],
                'personal_elements_count': wallet_data['personal_elements_count'],
                'personalness_score': wallet_data['validation']['personalness_score'],
                'funding': wallet_data.get('funding', {}),
                'story': story,  # Include the original story for recovery
                'recovery_instructions': {
                    'story_recovery': 'Use the story above with MemoryVault recovery',
                    'mnemonic_recovery': 'Use the mnemonic phrase above with any BIP39 wallet'
                },
                'validator_instructions': {
                    'stake_command': f'python cli.py stake {wallet_data["address"]} <stake_amount> --authority-file {filename}',
                    'min_stake': '10.0 LAK',
                    'recommended_stake': '100.0 LAK'
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(wallet_info, f, indent=2)
            
            print(f"\n💾 Validator wallet information saved to: {filename}")
            print(f"   Use this file for staking: python cli.py stake {wallet_data['address']} <amount> --authority-file {filename}")
            
        except Exception as e:
            print(f"\n⚠️  Warning: Could not save validator wallet info to file: {e}")
            print("   Please manually save your wallet information securely.")
    
    def stake(self, address, amount, authority_file=None):
        """Register as a validator by staking tokens with authority file authentication"""
        print(f"⚡ Registering {address} as validator with {amount} LAK stake")
        
        # Get private key from authority file
        private_key = self._get_private_key_from_authority(address, authority_file)
        if not private_key:
            print("❌ No private key found in authority file")
            print("Please specify an authority file with --authority-file")
            return
        
        # Get the account's nonce
        nonce_result = self._make_request('GET', f'/api/accounts/{address}/nonce')
        if nonce_result.get('status') != 'success':
            print(f"Error getting nonce for {address}: {nonce_result.get('message', 'Unknown error')}")
            return
        
        nonce = nonce_result['data']['nonce']
        
        # Create and sign stake transaction
        try:
            from core import Transaction, TransactionType
            import hashlib
            import time
            
            # Create stake transaction
            tx = Transaction(
                from_address=address,
                to_address="stake_pool",
                amount=float(amount),
                transaction_type=TransactionType.STAKE,
                gas_limit=10,  # Low gas for stake transaction
                gas_price=1.0,
                nonce=nonce,
                timestamp=time.time()
            )
            
            # Sign transaction
            tx_data = f"{tx.from_address}{tx.to_address}{tx.amount}{tx.transaction_type.value}{tx.gas_limit}{tx.gas_price}{tx.nonce}{tx.timestamp}"
            signature = self._sign_data(tx_data, private_key)
            tx.signature = signature
            
            # Submit signed transaction
            tx_data = {
                'from_address': tx.from_address,
                'to_address': tx.to_address,
                'amount': tx.amount,
                'transaction_type': tx.transaction_type.value,
                'gas_limit': tx.gas_limit,
                'gas_price': tx.gas_price,
                'nonce': tx.nonce,
                'signature': tx.signature,
                'timestamp': tx.timestamp
            }
            
            result = self._make_request('POST', '/api/transactions', tx_data)
            if result.get('status') == 'success':
                data = result['data']
                print(f"✅ Stake transaction signed and submitted successfully!")
                print(f"Hash: {data['transaction_hash']}")
                print(f"Address: {address}")
                print(f"Stake Amount: {amount}")
                print(f"Signature: {signature[:16]}...")
                print(f"\n⏳ Transaction is pending. Mine a block to process it.")
            else:
                print(f"❌ Stake transaction failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error creating stake transaction: {e}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Lakha Blockchain CLI Tool')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API server URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Get blockchain status')
    
    # Blocks command
    blocks_parser = subparsers.add_parser('blocks', help='List blocks')
    blocks_parser.add_argument('--page', type=int, default=1, help='Page number')
    blocks_parser.add_argument('--limit', type=int, default=10, help='Items per page')
    
    # Transactions command
    txs_parser = subparsers.add_parser('transactions', help='List transactions')
    txs_parser.add_argument('--page', type=int, default=1, help='Page number')
    txs_parser.add_argument('--limit', type=int, default=10, help='Items per page')
    
    # Pending command
    subparsers.add_parser('pending', help='Show pending transactions')
    
    # Account command
    account_parser = subparsers.add_parser('account', help='Show account details')
    account_parser.add_argument('address', help='Account address')
    
    # Balance command
    balance_parser = subparsers.add_parser('balance', help='Show account balance')
    balance_parser.add_argument('address', help='Account address')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send a transaction')
    send_parser.add_argument('from_address', help='Sender address')
    send_parser.add_argument('to_address', help='Recipient address')
    send_parser.add_argument('amount', type=float, help='Amount to send')
    send_parser.add_argument('--type', default='transfer', help='Transaction type')
    send_parser.add_argument('--authority-file', help='Path to authority file (JSON with private_key)')
    
    # Faucet command
    faucet_parser = subparsers.add_parser('faucet', help='Request tokens from faucet')
    faucet_parser.add_argument('address', help='Address to fund')
    faucet_parser.add_argument('--amount', type=float, default=100, help='Amount to request')
    
    # Generate address command
    subparsers.add_parser('generate-address', help='Generate a new address')
    
    # MemoryVault commands
    subparsers.add_parser('generate-memoryvault-wallet', help='Generate a MemoryVault wallet from personal story')
    subparsers.add_parser('recover-memoryvault-wallet', help='Recover MemoryVault wallet from story or mnemonic')
    subparsers.add_parser('create-validator-wallet', help='Create a MemoryVault wallet specifically for validator staking')
    
    # Validate address command
    validate_parser = subparsers.add_parser('validate-address', help='Validate an address')
    validate_parser.add_argument('address', help='Address to validate')
    
    # Validators command
    subparsers.add_parser('validators', help='List validators')
    
    # Contracts command
    subparsers.add_parser('contracts', help='List contracts')
    
    # Mining commands
    mining_status_parser = subparsers.add_parser('mining-status', help='Show mining status')
    start_mining_parser = subparsers.add_parser('start-mining', help='Start mining')
    stop_mining_parser = subparsers.add_parser('stop-mining', help='Stop mining')
    mine_parser = subparsers.add_parser('mine', help='Manually mine a single block')
    
    # Add api-key argument to relevant commands
    for p in [start_mining_parser, stop_mining_parser, mine_parser]:
        p.add_argument('--api-key', required=True, help='API key for authenticated endpoints')

    # Stake command
    stake_parser = subparsers.add_parser('stake', help='Register as a validator by staking tokens')
    stake_parser.add_argument('address', help='Address to register as validator')
    stake_parser.add_argument('amount', type=float, help='Amount to stake')
    stake_parser.add_argument('--authority-file', help='Path to authority file (JSON with private_key)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Pass api_key to CLI constructor if it exists in args
    api_key = getattr(args, 'api_key', None)
    cli = LakhaCLI(args.api_url, api_key)
    
    # Execute command
    if args.command == 'status':
        cli.status()
    elif args.command == 'blocks':
        cli.blocks(args.page, args.limit)
    elif args.command == 'transactions':
        cli.transactions(args.page, args.limit)
    elif args.command == 'pending':
        cli.pending()
    elif args.command == 'account':
        cli.account(args.address)
    elif args.command == 'balance':
        cli.balance(args.address)
    elif args.command == 'send':
        cli.send(args.from_address, args.to_address, args.amount, args.type, 
                authority_file=args.authority_file)
    elif args.command == 'faucet':
        cli.faucet(args.address, args.amount)
    elif args.command == 'generate-address':
        cli.generate_address()
    elif args.command == 'generate-memoryvault-wallet':
        cli.generate_memoryvault_wallet()
    elif args.command == 'recover-memoryvault-wallet':
        cli.recover_memoryvault_wallet()
    elif args.command == 'create-validator-wallet':
        cli.create_validator_wallet()
    elif args.command == 'validate-address':
        cli.validate_address(args.address)
    elif args.command == 'validators':
        cli.validators()
    elif args.command == 'contracts':
        cli.contracts()
    elif args.command == 'mining-status':
        cli.mining_status()
    elif args.command == 'start-mining':
        cli.start_mining()
    elif args.command == 'stop-mining':
        cli.stop_mining()
    elif args.command == 'mine':
        cli.mine_block()
    elif args.command == 'stake':
        cli.stake(args.address, args.amount, authority_file=args.authority_file)

if __name__ == '__main__':
    main()
