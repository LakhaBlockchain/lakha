#!/usr/bin/env python3
"""
Multi-Node Lakha Blockchain Demo
Demonstrates running multiple nodes, validator registration, and cross-node transactions
"""

import subprocess
import time
import json
import requests
import os
import signal
import sys
from typing import Dict, List, Optional

class MultiNodeDemo:
    def __init__(self, num_nodes=2):
        self.num_nodes = num_nodes
        self.nodes = {}
        self.validator_wallets = {}
        self.processes = []
        
    def get_api_port(self, i):
        return 5000 + 2 * i

    def get_p2p_port(self, i):
        return 5001 + 2 * i

    def get_db_path(self, i):
        return f'lakha_db_node{i+1}'
    
    def start_node(self, node_id: str, api_port: int, p2p_port: int, db_path: str, peers: Optional[List[str]] = None):
        """Start a Lakha blockchain node"""
        print(f"🚀 Starting Node {node_id} on API port {api_port}, P2P port {p2p_port}")
        
        cmd = [
            'python', 'api.py',
            '--port', str(api_port),
            '--p2p-port', str(p2p_port),
            '--db-path', db_path
        ]
        
        if peers:
            cmd.extend(['--p2p-peers'] + peers)
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.nodes[node_id] = {
            'api_port': api_port,
            'p2p_port': p2p_port,
            'db_path': db_path,
            'process': process,
            'api_url': f'http://localhost:{api_port}'
        }
        
        # Wait for node to start
        time.sleep(5)
        
        # Check if node is running
        try:
            response = requests.get(f'http://localhost:{api_port}/api/health', timeout=5)
            if response.status_code == 200:
                print(f"✅ Node {node_id} started successfully")
                return True
            else:
                print(f"❌ Node {node_id} failed to start (HTTP {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Node {node_id} failed to start: {e}")
            return False
    
    def create_validator_wallet(self, node_id: str, story: str) -> Optional[Dict]:
        """Create a validator wallet on a specific node"""
        print(f"\n🎭 Creating validator wallet on Node {node_id}")
        
        api_url = self.nodes[node_id]['api_url']
        
        # Create funded wallet
        response = requests.post(
            f'{api_url}/api/memoryvault/create-funded-wallet',
            json={
                'story': story,
                'funding_amount': 1000.0
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create wallet on Node {node_id}: {response.text}")
            return None
        
        result = response.json()
        if result['status'] != 'success':
            print(f"❌ Wallet creation failed on Node {node_id}: {result['message']}")
            return None
        
        wallet_data = result['data']
        print(f"✅ Validator wallet created on Node {node_id}")
        print(f"   Address: {wallet_data['address']}")
        
        # Check if funding was successful
        if wallet_data.get('funding', {}).get('funded'):
            print(f"   Funded: {wallet_data['funding']['amount']} LAK")
        else:
            print(f"   Funding: Failed - {wallet_data.get('funding', {}).get('error', 'Unknown error')}")
        
        # Save wallet info
        filename = f"validator_wallet_{node_id}_{int(time.time())}.json"
        wallet_info = {
            'node_id': node_id,
            'created_at': time.time(),
            'wallet_type': 'validator',
            'address': wallet_data['address'],
            'mnemonic': wallet_data['mnemonic'],
            'story_hash': wallet_data['story_hash'],
            'story': story,
            'funding': wallet_data['funding'],
            'api_url': api_url
        }
        
        with open(filename, 'w') as f:
            json.dump(wallet_info, f, indent=2)
        
        self.validator_wallets[node_id] = {
            'filename': filename,
            'data': wallet_info
        }
        
        return wallet_data
    
    def register_validator(self, node_id: str, stake_amount: float = 100.0) -> bool:
        """Register a validator on a specific node"""
        print(f"\n⚡ Registering validator on Node {node_id}")
        
        if node_id not in self.validator_wallets:
            print(f"❌ No validator wallet found for Node {node_id}")
            return False
        
        wallet_data = self.validator_wallets[node_id]['data']
        address = wallet_data['address']
        api_url = wallet_data['api_url']
        
        # Get nonce
        response = requests.get(f'{api_url}/api/accounts/{address}/nonce', timeout=5)
        if response.status_code != 200:
            print(f"❌ Failed to get nonce for {address}")
            return False
        
        nonce = response.json()['data']['nonce']
        
        # Create stake transaction (simplified - in real implementation would need proper signing)
        stake_tx = {
            'from_address': address,
            'to_address': 'stake_pool',
            'amount': stake_amount,
            'transaction_type': 'stake',
            'gas_limit': 10,
            'gas_price': 1.0,
            'nonce': nonce
        }
        
        response = requests.post(f'{api_url}/api/transactions', json=stake_tx, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to submit stake transaction: {response.text}")
            return False
        
        result = response.json()
        if result['status'] != 'success':
            print(f"❌ Stake transaction failed: {result['message']}")
            return False
        
        print(f"✅ Validator registered on Node {node_id}")
        print(f"   Address: {address}")
        print(f"   Stake: {stake_amount} LAK")
        print(f"   Transaction: {result['data']['transaction_hash']}")
        
        return True
    
    def mine_block(self, node_id: str) -> bool:
        """Mine a block on a specific node"""
        print(f"\n⛏️ Mining block on Node {node_id}")
        
        api_url = self.nodes[node_id]['api_url']
        
        response = requests.post(f'{api_url}/api/mining/mine', timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to mine block on Node {node_id}: {response.text}")
            return False
        
        result = response.json()
        if result['status'] != 'success':
            print(f"❌ Mining failed on Node {node_id}: {result['message']}")
            return False
        
        data = result['data']
        print(f"✅ Block mined on Node {node_id}")
        print(f"   Block: #{data['message'].split('#')[1].split()[0]}")
        print(f"   Transactions: {data['transactions_processed']}")
        print(f"   Hash: {data['block_hash'][:16]}...")
        
        return True
    
    def get_status(self, node_id: str) -> Optional[Dict]:
        """Get status of a specific node"""
        api_url = self.nodes[node_id]['api_url']
        
        try:
            response = requests.get(f'{api_url}/api/status', timeout=5)
            if response.status_code == 200:
                return response.json()['data']
            else:
                return None
        except Exception as e:
            print(f"❌ Failed to get status for Node {node_id}: {e}")
            return None
    
    def create_user_wallet(self, node_id: str, story: str) -> Optional[Dict]:
        """Create a user wallet on a specific node"""
        print(f"\n👤 Creating user wallet on Node {node_id}")
        
        api_url = self.nodes[node_id]['api_url']
        
        response = requests.post(
            f'{api_url}/api/memoryvault/create-funded-wallet',
            json={
                'story': story,
                'funding_amount': 0.000001  # 1 IBE
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create user wallet on Node {node_id}: {response.text}")
            return None
        
        result = response.json()
        if result['status'] != 'success':
            print(f"❌ User wallet creation failed on Node {node_id}: {result['message']}")
            # Show validation details if available
            if 'data' in result and 'personalness_score' in result['data']:
                validation = result['data']
                print(f"   📊 Personalness Score: {validation['personalness_score']:.2f}")
                print(f"   🔍 Personal Elements: {validation['personal_elements_count']}")
                print(f"   🏷️  Element Types: {validation['element_types']}")
                if validation.get('recommendations'):
                    print(f"   💡 Recommendations: {validation['recommendations'][:2]}...")
            return None
        
        wallet_data = result['data']
        print(f"✅ User wallet created on Node {node_id}")
        print(f"   Address: {wallet_data['address']}")
        
        # Check if funding was successful
        if wallet_data.get('funding', {}).get('funded'):
            print(f"   Funded: {wallet_data['funding']['amount']} LAK (IBE)")
        else:
            print(f"   Funding: Failed - {wallet_data.get('funding', {}).get('error', 'Unknown error')}")
        
        return wallet_data
    
    def send_transaction(self, from_node: str, to_node: str, amount: float) -> bool:
        """Send a transaction between nodes"""
        print(f"\n💸 Sending {amount} LAK from Node {from_node} to Node {to_node}")
        
        # Get wallet addresses
        if from_node not in self.validator_wallets:
            print(f"❌ No wallet found for Node {from_node}")
            return False
        
        from_address = self.validator_wallets[from_node]['data']['address']
        to_address = self.validator_wallets[to_node]['data']['address']
        api_url = self.nodes[from_node]['api_url']
        
        # Get nonce
        response = requests.get(f'{api_url}/api/accounts/{from_address}/nonce', timeout=5)
        if response.status_code != 200:
            print(f"❌ Failed to get nonce for {from_address}")
            return False
        
        nonce = response.json()['data']['nonce']
        
        # Create transfer transaction
        tx = {
            'from_address': from_address,
            'to_address': to_address,
            'amount': amount,
            'transaction_type': 'transfer',
            'gas_limit': 100,
            'gas_price': 1.0,
            'nonce': nonce
        }
        
        response = requests.post(f'{api_url}/api/transactions', json=tx, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to submit transaction: {response.text}")
            return False
        
        result = response.json()
        if result['status'] != 'success':
            print(f"❌ Transaction failed: {result['message']}")
            return False
        
        print(f"✅ Transaction submitted successfully")
        print(f"   From: {from_address}")
        print(f"   To: {to_address}")
        print(f"   Amount: {amount} LAK")
        print(f"   Hash: {result['data']['transaction_hash']}")
        
        return True
    
    def show_network_status(self):
        """Show status of all nodes"""
        print(f"\n🌐 Network Status")
        print("=" * 50)
        
        for node_id, node_info in self.nodes.items():
            status = self.get_status(node_id)
            if status:
                print(f"Node {node_id}:")
                print(f"  API: http://localhost:{node_info['api_port']}")
                print(f"  P2P: {node_info['p2p_port']}")
                print(f"  Chain Length: {status['chain_length']}")
                print(f"  Pending TXs: {status['pending_transactions']}")
                print(f"  Validators: {status['validators']}")
                
                # Check P2P status
                try:
                    p2p_response = requests.get(f'{node_info["api_url"]}/api/p2p/status', timeout=5)
                    if p2p_response.status_code == 200:
                        p2p_data = p2p_response.json()['data']
                        print(f"  P2P Connections: {p2p_data.get('connections', 0)}")
                        print(f"  P2P Enabled: {p2p_data.get('enabled', False)}")
                except:
                    print(f"  P2P Status: ❌ Unavailable")
                print()
            else:
                print(f"Node {node_id}: ❌ Offline")
                print()
    
    def cleanup(self):
        """Clean up all processes"""
        print("\n🧹 Cleaning up...")
        
        for node_id, node_info in self.nodes.items():
            if node_info['process']:
                print(f"Stopping Node {node_id}...")
                node_info['process'].terminate()
                try:
                    node_info['process'].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    node_info['process'].kill()
        
        print("✅ Cleanup complete")

def main():
    """Main demo function"""
    num_nodes = 2  # Change this to add more nodes
    demo = MultiNodeDemo(num_nodes=num_nodes)

    try:
        print("🚀 Lakha Multi-Node Blockchain Demo")
        print("=" * 50)

        # Step 1: Start N nodes
        print("\n📋 Step 1: Starting Nodes")
        print("-" * 30)

        for i in range(num_nodes):
            node_id = f'node{i+1}'
            api_port = demo.get_api_port(i)
            p2p_port = demo.get_p2p_port(i)
            db_path = demo.get_db_path(i)
            peers = []
            if i > 0:
                # Connect all new nodes to node1's P2P port
                peers = [f'ws://localhost:{demo.get_p2p_port(0)}']
            if not demo.start_node(node_id, api_port, p2p_port, db_path, peers):
                print(f"❌ Failed to start {node_id}")
                return

        # Wait for P2P connections to establish
        print("\n⏳ Waiting for P2P connections to establish...")
        time.sleep(15)
        demo.show_network_status()

        # Step 2: Create validator wallets and mine after each
        print("\n📋 Step 2: Creating Validator Wallets")
        print("-" * 30)
        validator_stories = [
            "When I was 12, I secretly built my first computer from spare parts in my dad's garage workshop behind the old tool cabinet, and I cried happy tears when it actually booted up and played my favorite game because I felt like a genius and my dad was so proud of me",
            "My older sister Sarah and I discovered a hidden compartment behind the loose brick in our basement wall when I was 9, and we secretly stashed our Halloween candy there every October because we were terrified our parents would find our sugar hoard, but I felt like we were pirates with buried treasure",
            "The first time I rode my bike without training wheels, I crashed into Mrs. Lee's rose bushes and she gave me lemonade while I cried, but I felt so proud when I finally made it home on my own"
        ]
        for i in range(num_nodes):
            node_id = f'node{i+1}'
            story = validator_stories[i % len(validator_stories)]
            wallet = demo.create_validator_wallet(node_id, story)
            if not wallet:
                print(f"❌ Failed to create validator wallet for {node_id}")
                return
            # Mine a block to process funding
            demo.mine_block(node_id)
            # Print chain status after mining
            status = demo.get_status(node_id)
            if status:
                print(f"   [DEBUG] {node_id} chain height: {status['chain_length']} hash: {status['latest_block']['hash'][:12]}...")
            # If node1, wait longer for propagation before next node
            if i == 0 and num_nodes > 1:
                print("   [DEBUG] Waiting for block propagation to other nodes...")
                time.sleep(8)
            else:
                time.sleep(2)

        # Step 3: Register validators and mine after each
        print("\n📋 Step 3: Registering Validators")
        print("-" * 30)
        for i in range(num_nodes):
            node_id = f'node{i+1}'
            stake_amount = 100.0 + 50.0 * i
            if not demo.register_validator(node_id, stake_amount):
                print(f"❌ Failed to register validator on {node_id}")
                return
            demo.mine_block(node_id)
            time.sleep(2)

        # Step 4: Create user wallets and mine after each
        print("\n📋 Step 4: Creating User Wallets")
        print("-" * 30)
        user_stories = [
            "I secretly discovered a hidden treehouse in the woods behind my house when I was 8, and I spent every summer afternoon reading my favorite comic books there because it felt like my own private magical world that nobody else knew about",
            "When I was 8, my first pet was a goldfish named Bubbles that I secretly won at the county fair, and I cried for days when it died because I felt like I had failed to take care of my very first responsibility",
            "My best friend and I buried a time capsule under the big oak tree in the park when we were 10, and we made a pact to dig it up together in 20 years"
        ]
        for i in range(num_nodes):
            node_id = f'node{i+1}'
            story = user_stories[i % len(user_stories)]
            user_wallet = demo.create_user_wallet(node_id, story)
            # If funding failed on node2, try faucet as fallback
            if user_wallet and not user_wallet.get('funding', {}).get('funded') and node_id == 'node2':
                print(f"   [DEBUG] Funding failed on {node_id}, trying faucet endpoint...")
                api_url = demo.nodes[node_id]['api_url']
                address = user_wallet['address']
                try:
                    faucet_resp = requests.post(f'{api_url}/api/faucet', json={'address': address, 'amount': 0.000001}, timeout=10)
                    if faucet_resp.status_code == 200:
                        print(f"   [DEBUG] Faucet funding succeeded for {address}")
                    else:
                        print(f"   [DEBUG] Faucet funding failed: {faucet_resp.text}")
                except Exception as e:
                    print(f"   [DEBUG] Faucet funding exception: {e}")
            demo.mine_block(node_id)
            # Print chain status after mining
            status = demo.get_status(node_id)
            if status:
                print(f"   [DEBUG] {node_id} chain height: {status['chain_length']} hash: {status['latest_block']['hash'][:12]}...")
            time.sleep(2)

        # Step 5: Cross-node transactions (node1 -> node2, node2 -> node3, ...)
        print("\n📋 Step 5: Cross-Node Transactions")
        print("-" * 30)
        for i in range(num_nodes - 1):
            from_node = f'node{i+1}'
            to_node = f'node{i+2}'
            if demo.send_transaction(from_node, to_node, 50.0):
                print(f"✅ Cross-node transaction from {from_node} to {to_node} submitted")
                demo.mine_block(from_node)
                # Print chain status after mining
                status_from = demo.get_status(from_node)
                if status_from:
                    print(f"   [DEBUG] {from_node} chain height: {status_from['chain_length']} hash: {status_from['latest_block']['hash'][:12]}...")
                print("   [DEBUG] Waiting for transaction/block propagation to other nodes...")
                time.sleep(8)
                demo.mine_block(to_node)
                status_to = demo.get_status(to_node)
                if status_to:
                    print(f"   [DEBUG] {to_node} chain height: {status_to['chain_length']} hash: {status_to['latest_block']['hash'][:12]}...")
                time.sleep(2)

        # Step 6: Show final network status
        print("\n📋 Step 6: Final Network Status")
        print("-" * 30)
        demo.show_network_status()

        print("\n🎉 Multi-Node Demo Complete!")
        print("=" * 50)
        print(f"✅ {num_nodes} nodes running with P2P connection")
        print("✅ Validator wallets created and registered")
        print("✅ User wallets created with IBE funding")
        print("✅ Cross-node transactions demonstrated")
        print("\n🔗 Node URLs:")
        for i in range(num_nodes):
            print(f"   Node {i+1}: http://localhost:{demo.get_api_port(i)}")
        print("\n⏹️  Press Ctrl+C to stop the demo")

        # Keep running until interrupted
        while True:
            time.sleep(10)
            demo.show_network_status()

    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    finally:
        demo.cleanup()

if __name__ == '__main__':
    main() 