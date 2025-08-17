#!/usr/bin/env python3
"""
Lakha Blockchain HTTP API Server
"""

import json
import time
import logging
import threading
import asyncio
import argparse
import hashlib
from functools import wraps
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS

# Adjust import paths for the new directory structure
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address, is_valid_address

# --- Globals --- #
blockchain: LahkaBlockchain = None
authority_address: str = None

# --- Logging --- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Authentication --- #
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != authority_address:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Blueprints --- #

# Status Blueprint (Public)
status_bp = Blueprint('status', __name__)

@status_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@status_bp.route('/status', methods=['GET'])
def get_status():
    chain_info = blockchain.get_chain_info()
    return jsonify({'status': 'success', 'data': chain_info})

@status_bp.route('/validators', methods=['GET'])
def get_validators():
    validators = {addr: val.to_dict() for addr, val in blockchain.validators.items()}
    return jsonify({'status': 'success', 'data': validators})

@status_bp.route('/validators/<address>', methods=['GET'])
def get_validator(address):
    try:
        validator = blockchain.validators.get(address)
        if not validator:
            return jsonify({'status': 'error', 'message': 'Validator not found'}), 404
        
        # Get performance metrics
        metrics = validator.get_performance_metrics()
        
        return jsonify({
            'status': 'success',
            'data': {
                'validator': validator.to_dict(),
                'metrics': metrics
            }
        })
    except Exception as e:
        logger.error(f"Error getting validator {address}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Blockchain Blueprint (Public)
blockchain_bp = Blueprint('blockchain', __name__)

@blockchain_bp.route('/blocks', methods=['GET'])
def get_blocks():
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 10)), 100)
    start = (page - 1) * limit
    end = start + limit
    blocks = [b.to_dict() for b in blockchain.chain[start:end]]
    return jsonify({
        'status': 'success',
        'data': {
            'blocks': blocks,
            'page': page,
            'limit': limit,
            'total': len(blockchain.chain)
        }
    })

@blockchain_bp.route('/transactions/pending', methods=['GET'])
def get_pending_transactions():
    pending_txs = [tx.to_dict() for tx in blockchain.pending_transactions]
    return jsonify({
        'status': 'success',
        'data': {
            'transactions': pending_txs,
            'count': len(pending_txs)
        }
    })

@blockchain_bp.route('/transactions', methods=['GET'])
def get_transactions():
    all_transactions = []
    for block in blockchain.chain:
        all_transactions.extend(block.transactions)

    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 10)), 100)
    start = (page - 1) * limit
    end = start + limit
    
    transactions = [tx.to_dict() for tx in all_transactions[start:end]]
    
    return jsonify({
        'status': 'success',
        'data': {
            'transactions': transactions,
            'page': page,
            'limit': limit,
            'total': len(all_transactions)
        }
    })

@blockchain_bp.route('/faucet', methods=['POST'])
def faucet():
    data = request.get_json()
    if not data or 'address' not in data:
        return jsonify({'status': 'error', 'message': 'Address is required'}), 400

    address = data['address']
    amount = float(data.get('amount', 100.0))

    if not is_valid_address(address):
        return jsonify({'status': 'error', 'message': 'Invalid address'}), 400

    genesis_account = blockchain.ledger.get_account('genesis')
    if not genesis_account:
        return jsonify({'status': 'error', 'message': 'Genesis account not found'}), 500

    faucet_tx = Transaction(
        from_address='genesis',
        to_address=address,
        amount=amount,
        transaction_type=TransactionType.TRANSFER,
        nonce=genesis_account.nonce
    )

    if blockchain.add_transaction(faucet_tx):
        return jsonify({
            'status': 'success',
            'data': {
                'message': f'{amount} tokens sent to {address}',
                'transaction_hash': faucet_tx.hash
            }
        })
    else:
        return jsonify({'status': 'error', 'message': 'Faucet transaction failed'}), 400

@blockchain_bp.route('/accounts/<address>/balance', methods=['GET'])
def get_balance(address):
    balance = blockchain.ledger.get_balance(address)
    return jsonify({
        'status': 'success',
        'data': {
            'address': address,
            'balance': balance
        }
    })

@blockchain_bp.route('/accounts/<address>/nonce', methods=['GET'])
def get_nonce(address):
    try:
        account = blockchain.ledger.get_account(address)
        nonce = account.nonce if account else 0
        return jsonify({
            'status': 'success',
            'data': {
                'address': address,
                'nonce': nonce
            }
        })
    except Exception as e:
        logger.error(f"Error getting nonce for {address}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@blockchain_bp.route('/validators', methods=['POST'])
def register_validator():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    address = data.get('address')
    stake_amount = float(data.get('stake_amount', 10.0))
    
    if not address:
        return jsonify({'status': 'error', 'message': 'Address is required'}), 400
    
    success = blockchain.register_validator(address, stake_amount)
    if not success:
        return jsonify({'status': 'error', 'message': 'Validator registration failed'}), 400
    
    return jsonify({
        'status': 'success',
        'data': {
            'message': 'Validator registered successfully',
            'address': address,
            'stake_amount': stake_amount
        }
    })

# Transaction Blueprint (Protected)
transaction_bp = Blueprint('transaction', __name__)

# MemoryVault Blueprint (Public)
memoryvault_bp = Blueprint('memoryvault', __name__)

@memoryvault_bp.route('/memoryvault/validate-story', methods=['POST'])
def validate_story_personalness():
    data = request.get_json()
    if not data or 'story' not in data:
        return jsonify({'status': 'error', 'message': 'Story is required'}), 400
    
    story = data['story']
    
    from address import validate_story_personalness as mv_validate
    result = mv_validate(story)
    
    return jsonify({
        'status': 'success',
        'data': result
    })

@memoryvault_bp.route('/memoryvault/create-funded-wallet', methods=['POST'])
def create_funded_wallet():
    data = request.get_json()
    if not data or 'story' not in data:
        return jsonify({'status': 'error', 'message': 'Story is required'}), 400
    
    story = data['story']
    funding_amount = float(data.get('funding_amount', 0.000001))
    
    from address import generate_address_from_story as mv_generate
    from address import validate_story_personalness as mv_validate
    
    validation = mv_validate(story)
    
    result = mv_generate(story)
    
    funding_result = _fund_address(result['address'], funding_amount)
    if funding_result['success']:
        result['funding'] = {
            'funded': True,
            'amount': funding_amount,
            'transaction_hash': funding_result['transaction_hash'],
            'message': f'Wallet funded with {funding_amount} LAK tokens'
        }
        result['wallet_ready'] = True
        result['validation'] = validation
    else:
        result['funding'] = {
            'funded': False,
            'error': funding_result['error'],
            'message': 'Address generated but funding failed'
        }
        result['wallet_ready'] = False
        result['validation'] = validation
        
    return jsonify({
        'status': 'success',
        'data': result
    })

def _fund_address(address: str, amount: float) -> dict:
    """Helper method to fund an address with LAK tokens"""
    try:
        if not is_valid_address(address):
            return {'success': False, 'error': 'Invalid address'}
        
        genesis_account = blockchain.ledger.get_account('genesis')
        if not genesis_account:
            return {'success': False, 'error': 'Genesis account not found'}
        
        funding_tx = Transaction(
            from_address='genesis',
            to_address=address,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            nonce=genesis_account.nonce
        )
        
        if blockchain.add_transaction(funding_tx):
            return {
                'success': True,
                'transaction_hash': funding_tx.hash,
                'amount': amount
            }
        else:
            return {'success': False, 'error': 'Transaction validation failed'}
            
    except Exception as e:
        logger.error(f"Error funding address {address}: {e}")
        return {'success': False, 'error': str(e)}

def _verify_sha256_signature(address: str, message: str, signature: str) -> bool:
    """
    Verifies a SHA256 signature.
    NOTE: This is a simplified, insecure verification for demonstration purposes.
    In a real blockchain, this would involve public-key cryptography (e.g., ECDSA).
    """
    # For this simplified model, we assume the 'private key' is just a secret known to the address.
    # In a real system, the address would be derived from a public key, and the signature
    # would be verifiable against that public key.
    # Here, we're just re-hashing the message with a 'secret' derived from the address.
    # This is NOT secure for production.
    
    # Re-create the expected signature using the address as a 'secret'
    expected_signature = hashlib.sha256((message + address).encode()).hexdigest()
    return expected_signature == signature

@blockchain_bp.route('/mining/mine', methods=['POST'])
def mine_block():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    address = data.get('address')
    message = data.get('message')
    signature = data.get('signature')

    if not all([address, message, signature]):
        return jsonify({'status': 'error', 'message': 'Missing address, message, or signature'}), 400

    # Verify the signature
    if not _verify_sha256_signature(address, message, signature):
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 401

    # Check if the address is a registered validator
    if address not in blockchain.validators:
        return jsonify({'status': 'error', 'message': 'Only registered validators can mine'}), 403

    if not blockchain.pending_transactions:
        return jsonify({'status': 'error', 'message': 'No pending transactions to mine'}), 400
    
    success = blockchain.mine_block()
    if success:
        latest_block = blockchain.get_latest_block()
        # Optional: Add P2P broadcasting logic here if needed
        return jsonify({'status': 'success', 'data': latest_block.to_dict()})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to mine block'}), 500

# --- App Factory --- #
def create_app(db_path, p2p_port, p2p_peers, auth_address):
    global blockchain, authority_address
    
    app = Flask(__name__)
    CORS(app)

    # Initialize blockchain and set authority address
    blockchain = LahkaBlockchain(
        db_path=db_path,
        p2p_port=p2p_port,
        p2p_peers=p2p_peers
    )
    authority_address = auth_address

    # Register blueprints
    app.register_blueprint(status_bp, url_prefix='/api')
    app.register_blueprint(blockchain_bp, url_prefix='/api')
    app.register_blueprint(transaction_bp, url_prefix='/api')
    app.register_blueprint(memoryvault_bp, url_prefix='/api')

    # Optional: Start P2P network in a background thread
    if p2p_port:
        def run_p2p():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(blockchain.start_network())
            loop.run_forever()
        p2p_thread = threading.Thread(target=run_p2p, daemon=True)
        p2p_thread.start()

    return app

# --- Main Execution --- #
def main():
    parser = argparse.ArgumentParser(description='Lakha RPC Node Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--db-path', required=True, help='Database path')
    parser.add_argument('--p2p-port', type=int, help='P2P port')
    parser.add_argument('--p2p-peers', nargs='*', help='P2P peer addresses')
    parser.add_argument('--authority-keypair', required=True, help='Path to the authority keypair JSON file')

    args = parser.parse_args()

    # Load authority address from keypair file
    try:
        with open(args.authority_keypair, 'r') as f:
            keypair = json.load(f)
            auth_address = keypair.get('address')
            if not auth_address:
                raise ValueError("Address not found in keypair file.")
    except Exception as e:
        logger.error(f"Failed to load authority keypair: {e}")
        sys.exit(1)

    app = create_app(
        db_path=args.db_path,
        p2p_port=args.p2p_port,
        p2p_peers=args.p2p_peers,
        auth_address=auth_address
    )

    logger.info(f"Starting Lakha RPC Node authorized for: {auth_address}")
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()
