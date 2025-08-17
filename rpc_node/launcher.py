#!/usr/bin/env python3
"""
Lakha RPC Node Launcher
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Run Lakha RPC Node')
    parser.add_argument('--port', type=int, default=5000, help='API port')
    parser.add_argument('--db-path', default='rpc_node/db', help='Database path')
    parser.add_argument('--p2p-port', type=int, help='P2P port')
    parser.add_argument('--p2p-peers', nargs='*', help='P2P peer addresses')
    parser.add_argument('--authority-keypair', required=True, help='Path to the authority keypair JSON file')

    args = parser.parse_args()

    # Ensure the server script exists
    server_path = Path(__file__).parent / 'server.py'
    if not server_path.exists():
        print(f"❌ Error: {server_path} not found.")
        sys.exit(1)

    # Create database directory if it doesn't exist
    Path(args.db_path).mkdir(parents=True, exist_ok=True)

    # Construct the command to run the server
    cmd = [
        sys.executable, str(server_path),
        '--port', str(args.port),
        '--db-path', args.db_path,
        '--authority-keypair', args.authority_keypair
    ]

    if args.p2p_port:
        cmd.extend(['--p2p-port', str(args.p2p_port)])

    if args.p2p_peers:
        cmd.extend(['--p2p-peers'] + args.p2p_peers)

    print(f"🚀 Starting Lakha RPC Node on port {args.port}")
    print(f"   Database: {args.db_path}")
    print(f"   Authority: {args.authority_keypair}")
    print(f"   Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print(f"\n🛑 Node on port {args.port} stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Node on port {args.port} failed: {e}")

if __name__ == '__main__':
    main()
