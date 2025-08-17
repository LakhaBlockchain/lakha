#!/usr/bin/env python3
"""
Lakha Pre-Testnet Setup Script
Clean single-node setup for pre-testnet deployment
"""

import os
import sys
import time
import json
import shutil
import subprocess
import requests
from pathlib import Path

class PreTestnetSetup:
    def __init__(self, db_path='lakha_db_pretestnet', api_port=5000):
        self.db_path = db_path
        self.api_port = api_port
        self.api_url = f'http://localhost:{api_port}'
        self.node_process = None
        self.genesis_wallet = None
        
    def clean_database(self):
        """Clean/reset the database for fresh start"""
        print("🧹 Cleaning database...")
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)
        Path(self.db_path).mkdir(exist_ok=True)
        print(f"✅ Fresh database: {self.db_path}")
    
    def start_node(self):
        """Start the blockchain node"""
        print(f"🚀 Starting Lakha node on port {self.api_port}...")
        cmd = [sys.executable, 'api.py', '--port', str(self.api_port), '--db-path', self.db_path]
        
        try:
            self.node_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)
            return self.check_node_health()
        except Exception as e:
            print(f"❌ Failed to start node: {e}")
            return False
    
    def check_node_health(self):
        """Check if the node is healthy"""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def create_genesis_wallet(self):
        """Create genesis wallet using MemoryVault"""
        print("🔑 Creating genesis wallet...")
        story = "I am the genesis validator of the Lakha blockchain."
        
        try:
            response = requests.post(
                f"{self.api_url}/api/memoryvault/create-funded-wallet",
                json={"story": story, "funding_amount": 10000.0},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'success':
                    self.genesis_wallet = result['data']
                    print(f"✅ Genesis wallet: {self.genesis_wallet['address']}")
                    return self.genesis_wallet
        except Exception as e:
            print(f"❌ Error: {e}")
        return None
    
    def register_validator(self):
        """Register genesis wallet as validator"""
        if not self.genesis_wallet:
            return False
        
        print("🏛️ Registering validator...")
        try:
            response = requests.post(
                f"{self.api_url}/api/validators",
                json={"address": self.genesis_wallet['address'], "stake_amount": 1000.0},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def mine_blocks(self, count=3):
        """Mine initial blocks"""
        print(f"⛏️ Mining {count} blocks...")
        for i in range(count):
            try:
                requests.post(f"{self.api_url}/api/mining/mine", timeout=10)
                time.sleep(1)
            except:
                pass
    
    def run_setup(self):
        """Run complete setup"""
        print("🚀 Lakha Pre-Testnet Setup")
        print("="*40)
        
        self.clean_database()
        
        if not self.start_node():
            print("❌ Failed to start node")
            return
        
        if not self.create_genesis_wallet():
            print("❌ Failed to create genesis wallet")
            return
        
        if not self.register_validator():
            print("❌ Failed to register validator")
            return
        
        self.mine_blocks(3)
        
        print("\n✅ Pre-testnet setup complete!")
        print(f"🌐 API: {self.api_url}")
        print("💡 Press Ctrl+C to stop")

def main():
    setup = PreTestnetSetup()
    setup.run_setup()

if __name__ == '__main__':
    main() 