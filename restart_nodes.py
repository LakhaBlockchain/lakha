#!/usr/bin/env python3
"""
Node Restart Script
Helps restart all nodes with clean state for proper synchronization
"""

import subprocess
import time
import os
import shutil

def clean_databases():
    """Clean all node databases"""
    print("🧹 Cleaning node databases...")
    
    db_paths = [
        'lakha_db_node1',
        'lakha_db_node2', 
        'lakha_db_node3'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                shutil.rmtree(db_path)
                print(f"   ✅ Cleaned {db_path}")
            except Exception as e:
                print(f"   ❌ Error cleaning {db_path}: {e}")
        else:
            print(f"   ℹ️  {db_path} does not exist")

def start_nodes():
    """Start all nodes"""
    print("\n🚀 Starting nodes...")
    
    # Node 1 (no peers, will be the leader)
    print("   Starting Node 1 (port 5000, P2P 8001)...")
    node1_cmd = [
        'python', 'api.py', 
        '--port', '5000', 
        '--db-path', 'lakha_db_node1', 
        '--p2p-port', '8001'
    ]
    
    # Node 2 (connects to Node 1)
    print("   Starting Node 2 (port 5001, P2P 8002)...")
    node2_cmd = [
        'python', 'api.py', 
        '--port', '5001', 
        '--db-path', 'lakha_db_node2', 
        '--p2p-port', '8002',
        '--p2p-peers', 'ws://localhost:8001'
    ]
    
    # Node 3 (connects to Node 1 and Node 2)
    print("   Starting Node 3 (port 5002, P2P 8003)...")
    node3_cmd = [
        'python', 'api.py', 
        '--port', '5002', 
        '--db-path', 'lakha_db_node3', 
        '--p2p-port', '8003',
        '--p2p-peers', 'ws://localhost:8001', 'ws://localhost:8002'
    ]
    
    print("\n📋 Commands to run in separate terminals:")
    print("=" * 60)
    print("Terminal 1 (Node 1):")
    print("   " + " ".join(node1_cmd))
    print("\nTerminal 2 (Node 2):")
    print("   " + " ".join(node2_cmd))
    print("\nTerminal 3 (Node 3):")
    print("   " + " ".join(node3_cmd))
    print("=" * 60)
    
    print("\n⏳ Wait for all nodes to start, then run:")
    print("   python test_complete_p2p_flow.py")

def check_node_status():
    """Check if nodes are running"""
    print("\n🔍 Checking node status...")
    
    import requests
    
    for port in [5000, 5001, 5002]:
        try:
            response = requests.get(f'http://localhost:{port}/api/health', timeout=2)
            if response.status_code == 200:
                print(f"   ✅ Node {port}: Running")
            else:
                print(f"   ❌ Node {port}: Not responding properly")
        except Exception as e:
            print(f"   ❌ Node {port}: Not running - {e}")

def main():
    """Main function"""
    print("🔄 Node Restart Script")
    print("=" * 50)
    
    print("This script will help you restart all nodes with clean databases.")
    print("This ensures proper P2P synchronization from the start.")
    
    choice = input("\nDo you want to clean databases? (y/n): ").lower().strip()
    
    if choice == 'y':
        clean_databases()
        start_nodes()
    else:
        print("Skipping database cleanup.")
        start_nodes()
    
    print("\n⏳ After starting all nodes, wait 10 seconds then run:")
    print("   python check_node_status.py")

if __name__ == '__main__':
    main() 