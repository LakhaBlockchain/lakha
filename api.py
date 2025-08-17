#!/usr/bin/env python3
"""
Lakha Blockchain HTTP API
Provides RESTful endpoints for blockchain interaction
"""

import json
import time
import logging
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from address import generate_address, is_valid_address
from core import LahkaBlockchain, Transaction, TransactionType
from typing import Dict, Any, Optional
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LakhaAPI:
    """HTTP API server for Lakha blockchain"""
    
    def __init__(self, blockchain: LahkaBlockchain, host='0.0.0.0', port=5000):
        self.blockchain = blockchain
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.mining_active = False
        self.mining_thread = None
        self.p2p_task = None
        
        # Register routes
        self._register_routes()
        
        # Start P2P network if configured
        if self.blockchain.p2p_port:
            import asyncio
            import threading
            def run_p2p():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.blockchain.start_network())
                    # Wait a bit for P2P connections to establish
                    time.sleep(2)
                    loop.run_forever()
                except Exception as e:
                    logger.error(f"P2P network error: {e}")
            
            self.p2p_thread = threading.Thread(target=run_p2p, daemon=True)
            self.p2p_thread.start()
            # Store the event loop for broadcasting
            self.p2p_loop = None
            # Wait for P2P network to start (increased from 3 to 8 seconds)
            time.sleep(8)
        
    def _register_routes(self):
        """Register all API routes"""
        
        # Health and status endpoints
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'version': '1.0.0'
            })
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get blockchain status"""
            try:
                chain_info = self.blockchain.get_chain_info()
                # Temporarily disable network performance to fix error
                network_performance = {}
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'chain_length': chain_info['chain_length'],
                        'pending_transactions': chain_info['pending_transactions'],
                        'validators': chain_info['validators'],
                        'contracts': chain_info['contracts'],
                        'latest_block': chain_info['latest_block'],
                        'network_performance': network_performance
                    }
                })
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Block endpoints
        @self.app.route('/api/blocks', methods=['GET'])
        def get_blocks():
            """Get blocks with pagination"""
            try:
                page = int(request.args.get('page', 1))
                limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 blocks per request
                start = (page - 1) * limit
                end = start + limit
                
                blocks = []
                for i in range(start, min(end, len(self.blockchain.chain))):
                    blocks.append(self.blockchain.chain[i].to_dict())
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'blocks': blocks,
                        'page': page,
                        'limit': limit,
                        'total': len(self.blockchain.chain),
                        'has_more': end < len(self.blockchain.chain)
                    }
                })
            except Exception as e:
                logger.error(f"Error getting blocks: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/blocks/<int:block_index>', methods=['GET'])
        def get_block(block_index):
            """Get specific block by index"""
            try:
                if block_index >= len(self.blockchain.chain):
                    return jsonify({'status': 'error', 'message': 'Block not found'}), 404
                
                block = self.blockchain.chain[block_index].to_dict()
                return jsonify({
                    'status': 'success',
                    'data': block
                })
            except Exception as e:
                logger.error(f"Error getting block {block_index}: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/blocks/latest', methods=['GET'])
        def get_latest_block():
            """Get the latest block"""
            try:
                latest_block = self.blockchain.get_latest_block().to_dict()
                return jsonify({
                    'status': 'success',
                    'data': latest_block
                })
            except Exception as e:
                logger.error(f"Error getting latest block: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Transaction endpoints
        @self.app.route('/api/transactions', methods=['GET'])
        def get_transactions():
            """Get transactions with pagination"""
            try:
                page = int(request.args.get('page', 1))
                limit = min(int(request.args.get('limit', 10)), 100)
                start = (page - 1) * limit
                end = start + limit
                
                # Get transactions from all blocks
                all_transactions = []
                for block in self.blockchain.chain:
                    all_transactions.extend(block.transactions)
                
                transactions = []
                for i in range(start, min(end, len(all_transactions))):
                    transactions.append(all_transactions[i].to_dict())
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'transactions': transactions,
                        'page': page,
                        'limit': limit,
                        'total': len(all_transactions),
                        'has_more': end < len(all_transactions)
                    }
                })
            except Exception as e:
                logger.error(f"Error getting transactions: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/transactions/pending', methods=['GET'])
        def get_pending_transactions():
            """Get pending transactions"""
            try:
                pending_txs = [tx.to_dict() for tx in self.blockchain.pending_transactions]
                return jsonify({
                    'status': 'success',
                    'data': {
                        'transactions': pending_txs,
                        'count': len(pending_txs)
                    }
                })
            except Exception as e:
                logger.error(f"Error getting pending transactions: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/transactions', methods=['POST'])
        def submit_transaction():
            """Submit a new transaction"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'No data provided'}), 400
                
                # Validate required fields
                required_fields = ['from_address', 'to_address', 'amount', 'transaction_type']
                for field in required_fields:
                    if field not in data:
                        return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
                
                # Create transaction
                tx = Transaction(
                    from_address=data['from_address'],
                    to_address=data['to_address'],
                    amount=float(data['amount']),
                    transaction_type=TransactionType(data['transaction_type']),
                    data=data.get('data', {}),
                    gas_limit=int(data.get('gas_limit', 21000)),
                    gas_price=float(data.get('gas_price', 1.0)),
                    nonce=int(data.get('nonce', 0))
                )
                
                # Add transaction to pool
                success = self.blockchain.add_transaction(tx)
                if not success:
                    return jsonify({'status': 'error', 'message': 'Transaction validation failed'}), 400
                
                # Broadcast transaction to P2P network
                if self.blockchain.p2p_node:
                    try:
                        # Check if P2P node has connections
                        if hasattr(self.blockchain.p2p_node, 'connections') and len(self.blockchain.p2p_node.connections) > 0:
                            # Create a new event loop for broadcasting
                            import asyncio
                            import threading
                            
                            def broadcast_in_thread():
                                try:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(self.blockchain.broadcast_transaction(tx))
                                    loop.close()
                                except Exception as e:
                                    logger.error(f"Broadcast thread error: {e}")
                            
                            # Run broadcast in a separate thread
                            broadcast_thread = threading.Thread(target=broadcast_in_thread, daemon=True)
                            broadcast_thread.start()
                            
                            logger.info(f"Broadcasting transaction {tx.hash} to {len(self.blockchain.p2p_node.connections)} peers")
                        else:
                            logger.warning(f"No P2P connections available for broadcasting transaction {tx.hash}")
                    except Exception as e:
                        logger.error(f"Failed to broadcast transaction {tx.hash}: {e}")
                        logger.error(f"P2P node status: {self.blockchain.p2p_node is not None}")
                        logger.error(f"P2P connections: {len(self.blockchain.p2p_node.connections) if hasattr(self.blockchain.p2p_node, 'connections') else 'Unknown'}")
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'transaction_hash': tx.hash,
                        'message': 'Transaction submitted successfully'
                    }
                })
            except Exception as e:
                logger.error(f"Error submitting transaction: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/transactions/<tx_hash>', methods=['GET'])
        def get_transaction(tx_hash):
            """Get transaction by hash"""
            try:
                # Search in all blocks
                for block in self.blockchain.chain:
                    for tx in block.transactions:
                        if tx.hash == tx_hash:
                            return jsonify({
                                'status': 'success',
                                'data': tx.to_dict()
                            })
                
                # Search in pending transactions
                for tx in self.blockchain.pending_transactions:
                    if tx.hash == tx_hash:
                        return jsonify({
                            'status': 'success',
                            'data': tx.to_dict()
                        })
                
                return jsonify({'status': 'error', 'message': 'Transaction not found'}), 404
            except Exception as e:
                logger.error(f"Error getting transaction {tx_hash}: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Account endpoints
        @self.app.route('/api/accounts', methods=['GET'])
        def get_accounts():
            """Get all accounts"""
            try:
                accounts_summary = self.blockchain.ledger.get_accounts_summary()
                return jsonify({
                    'status': 'success',
                    'data': accounts_summary
                })
            except Exception as e:
                logger.error(f"Error getting accounts: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/accounts/<address>', methods=['GET'])
        def get_account(address):
            """Get account by address"""
            try:
                account = self.blockchain.ledger.get_account(address)
                if not account:
                    return jsonify({'status': 'error', 'message': 'Account not found'}), 404
                
                # Get transaction history
                history = self.blockchain.ledger.get_account_history(address, limit=50)
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'account': account.to_dict(),
                        'history': [entry.to_dict() for entry in history]
                    }
                })
            except Exception as e:
                logger.error(f"Error getting account {address}: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/accounts/<address>/balance', methods=['GET'])
        def get_balance(address):
            """Get account balance"""
            try:
                balance = self.blockchain.ledger.get_balance(address)
                return jsonify({
                    'status': 'success',
                    'data': {
                        'address': address,
                        'balance': balance
                    }
                })
            except Exception as e:
                logger.error(f"Error getting balance for {address}: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/accounts/<address>/nonce', methods=['GET'])
        def get_nonce(address):
            """Get account nonce"""
            try:
                account = self.blockchain.ledger.get_account(address)
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
        
        # Contract endpoints
        @self.app.route('/api/contracts', methods=['GET'])
        def get_contracts():
            """Get all contracts"""
            try:
                contracts = {}
                for addr, contract in self.blockchain.contract_engine.contracts.items():
                    contracts[addr] = contract.to_dict()
                
                return jsonify({
                    'status': 'success',
                    'data': contracts
                })
            except Exception as e:
                logger.error(f"Error getting contracts: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/contracts/<contract_address>', methods=['GET'])
        def get_contract(contract_address):
            """Get contract by address"""
            try:
                contract = self.blockchain.contract_engine.contracts.get(contract_address)
                if not contract:
                    return jsonify({'status': 'error', 'message': 'Contract not found'}), 404
                
                return jsonify({
                    'status': 'success',
                    'data': contract.to_dict()
                })
            except Exception as e:
                logger.error(f"Error getting contract {contract_address}: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/contracts/<contract_address>/state', methods=['GET'])
        def get_contract_state(contract_address):
            """Get contract state"""
            try:
                key_path = request.args.get('key_path', '')
                state = self.blockchain.contract_engine.get_contract_state(contract_address, key_path)
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'contract_address': contract_address,
                        'key_path': key_path,
                        'state': state
                    }
                })
            except Exception as e:
                logger.error(f"Error getting contract state for {contract_address}: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Validator endpoints
        @self.app.route('/api/validators', methods=['GET'])
        def get_validators():
            """Get all validators"""
            try:
                validators = {}
                for addr, validator in self.blockchain.validators.items():
                    validators[addr] = validator.to_dict()
                
                return jsonify({
                    'status': 'success',
                    'data': validators
                })
            except Exception as e:
                logger.error(f"Error getting validators: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/validators/<address>', methods=['GET'])
        def get_validator(address):
            """Get validator by address"""
            try:
                validator = self.blockchain.validators.get(address)
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
        
        @self.app.route('/api/validators', methods=['POST'])
        def register_validator():
            """Register a new validator"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'No data provided'}), 400
                
                address = data.get('address')
                stake_amount = float(data.get('stake_amount', 10.0))
                
                if not address:
                    return jsonify({'status': 'error', 'message': 'Address is required'}), 400
                
                success = self.blockchain.register_validator(address, stake_amount)
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
            except Exception as e:
                logger.error(f"Error registering validator: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Mining endpoints
        @self.app.route('/api/mining/start', methods=['POST'])
        def start_mining():
            """Start mining"""
            try:
                if self.mining_active:
                    return jsonify({'status': 'error', 'message': 'Mining already active'}), 400
                
                self.mining_active = True
                self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
                self.mining_thread.start()
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'message': 'Mining started successfully'
                    }
                })
            except Exception as e:
                logger.error(f"Error starting mining: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/mining/stop', methods=['POST'])
        def stop_mining():
            """Stop mining"""
            try:
                self.mining_active = False
                return jsonify({
                    'status': 'success',
                    'data': {
                        'message': 'Mining stopped successfully'
                    }
                })
            except Exception as e:
                logger.error(f"Error stopping mining: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/mining/status', methods=['GET'])
        def mining_status():
            """Get mining status"""
            try:
                return jsonify({
                    'status': 'success',
                    'data': {
                        'mining_active': self.mining_active,
                        'pending_transactions': len(self.blockchain.pending_transactions)
                    }
                })
            except Exception as e:
                logger.error(f"Error getting mining status: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/p2p/status', methods=['GET'])
        def p2p_status():
            """Get P2P network status"""
            try:
                p2p_info = {
                    'enabled': self.blockchain.p2p_node is not None,
                    'p2p_port': self.blockchain.p2p_port,
                    'p2p_peers': self.blockchain.p2p_peers,
                    'connections': 0,
                    'thread_running': False
                }
                
                if self.blockchain.p2p_node:
                    p2p_info['connections'] = len(self.blockchain.p2p_node.connections)
                    p2p_info['thread_running'] = hasattr(self, 'p2p_thread') and self.p2p_thread.is_alive()
                
                return jsonify({
                    'status': 'success',
                    'data': p2p_info
                })
            except Exception as e:
                logger.error(f"Error getting P2P status: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/mining/mine', methods=['POST'])
        def mine_block():
            """Manually mine a single block"""
            try:
                if not self.blockchain.pending_transactions:
                    return jsonify({
                        'status': 'error', 
                        'message': 'No pending transactions to mine'
                    }), 400
                
                # Mine a single block
                success = self.blockchain.mine_block()
                if success:
                    latest_block = self.blockchain.get_latest_block()
                    
                    # Broadcast block to P2P network
                    if self.blockchain.p2p_node:
                        try:
                            # Check if P2P node has connections
                            if hasattr(self.blockchain.p2p_node, 'connections') and len(self.blockchain.p2p_node.connections) > 0:
                                # Create a new event loop for broadcasting
                                import asyncio
                                import threading
                                
                                def broadcast_in_thread():
                                    try:
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        loop.run_until_complete(self.blockchain.broadcast_block(latest_block))
                                        loop.close()
                                    except Exception as e:
                                        logger.error(f"Broadcast thread error: {e}")
                                
                                # Run broadcast in a separate thread
                                broadcast_thread = threading.Thread(target=broadcast_in_thread, daemon=True)
                                broadcast_thread.start()
                                
                                logger.info(f"Broadcasting block #{latest_block.index} to {len(self.blockchain.p2p_node.connections)} peers")
                            else:
                                logger.warning(f"No P2P connections available for broadcasting block #{latest_block.index}")
                        except Exception as e:
                            logger.error(f"Failed to broadcast block #{latest_block.index}: {e}")
                            logger.error(f"P2P node status: {self.blockchain.p2p_node is not None}")
                            logger.error(f"P2P connections: {len(self.blockchain.p2p_node.connections) if hasattr(self.blockchain.p2p_node, 'connections') else 'Unknown'}")
                    
                    return jsonify({
                        'status': 'success',
                        'data': {
                            'message': f'Block #{latest_block.index} mined successfully',
                            'block_hash': latest_block.hash,
                            'transactions_processed': len(latest_block.transactions),
                            'pending_remaining': len(self.blockchain.pending_transactions)
                        }
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to mine block'
                    }), 500
            except Exception as e:
                logger.error(f"Error mining block: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Utility endpoints
        @self.app.route('/api/utils/generate-address', methods=['POST'])
        def generate_new_address():
            """Generate a new Bech32 address"""
            try:
                address = generate_address()
                return jsonify({
                    'status': 'success',
                    'data': {
                        'address': address
                    }
                })
            except Exception as e:
                logger.error(f"Error generating address: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/utils/validate-address', methods=['POST'])
        def validate_address():
            """Validate a Bech32 address"""
            try:
                data = request.get_json()
                if not data or 'address' not in data:
                    return jsonify({'status': 'error', 'message': 'Address is required'}), 400
                
                address = data['address']
                is_valid = is_valid_address(address)
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'address': address,
                        'is_valid': is_valid
                    }
                })
            except Exception as e:
                logger.error(f"Error validating address: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # MemoryVault endpoints
        @self.app.route('/api/memoryvault/generate-from-story', methods=['POST'])
        def generate_address_from_story():
            """Generate address from personal story using MemoryVault and auto-fund it"""
            try:
                data = request.get_json()
                if not data or 'story' not in data:
                    return jsonify({'status': 'error', 'message': 'Story is required'}), 400
                
                story = data['story']
                auto_fund = data.get('auto_fund', True)  # Default to auto-funding
                funding_amount = float(data.get('funding_amount', 0.000001))  # Default 1 IBE (1/1,000,000 LAK)
                
                # Import MemoryVault functions
                try:
                    from address import generate_address_from_story as mv_generate
                    result = mv_generate(story)
                    
                    # Auto-fund the generated address if requested
                    if auto_fund and result.get('address'):
                        funding_result = self._fund_address(result['address'], funding_amount)
                        if funding_result['success']:
                            result['funding'] = {
                                'funded': True,
                                'amount': funding_amount,
                                'transaction_hash': funding_result['transaction_hash'],
                                'message': f'Address funded with {funding_amount} LAK tokens'
                            }
                        else:
                            result['funding'] = {
                                'funded': False,
                                'error': funding_result['error'],
                                'message': 'Address generated but funding failed'
                            }
                    else:
                        result['funding'] = {
                            'funded': False,
                            'message': 'Auto-funding disabled'
                        }
                    
                    return jsonify({
                        'status': 'success',
                        'data': result
                    })
                except ImportError:
                    return jsonify({'status': 'error', 'message': 'MemoryVault not available'}), 500
                
            except Exception as e:
                logger.error(f"Error generating address from story: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/memoryvault/generate-from-mnemonic', methods=['POST'])
        def generate_address_from_mnemonic():
            """Generate address from mnemonic phrase and optionally auto-fund it"""
            try:
                data = request.get_json()
                if not data or 'mnemonic' not in data:
                    return jsonify({'status': 'error', 'message': 'Mnemonic is required'}), 400
                
                mnemonic = data['mnemonic']
                auto_fund = data.get('auto_fund', False)  # Default to False for recovery
                funding_amount = float(data.get('funding_amount', 0.000001))  # Default 1 IBE (1/1,000,000 LAK)
                
                # Import MemoryVault functions
                try:
                    from address import generate_address_from_mnemonic as mv_recover
                    result = mv_recover(mnemonic)
                    
                    # Auto-fund the recovered address if requested
                    if auto_fund and result.get('address'):
                        funding_result = self._fund_address(result['address'], funding_amount)
                        if funding_result['success']:
                            result['funding'] = {
                                'funded': True,
                                'amount': funding_amount,
                                'transaction_hash': funding_result['transaction_hash'],
                                'message': f'Address funded with {funding_amount} LAK tokens'
                            }
                        else:
                            result['funding'] = {
                                'funded': False,
                                'error': funding_result['error'],
                                'message': 'Address recovered but funding failed'
                            }
                    else:
                        result['funding'] = {
                            'funded': False,
                            'message': 'Auto-funding disabled for recovery'
                        }
                    
                    return jsonify({
                        'status': 'success',
                        'data': result
                    })
                except ImportError:
                    return jsonify({'status': 'error', 'message': 'MemoryVault not available'}), 500
                
            except Exception as e:
                logger.error(f"Error generating address from mnemonic: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/memoryvault/validate-story', methods=['POST'])
        def validate_story_personalness():
            """Validate story personalness for MemoryVault"""
            try:
                data = request.get_json()
                if not data or 'story' not in data:
                    return jsonify({'status': 'error', 'message': 'Story is required'}), 400
                
                story = data['story']
                
                # Import MemoryVault functions
                try:
                    from address import validate_story_personalness as mv_validate
                    result = mv_validate(story)
                    
                    return jsonify({
                        'status': 'success',
                        'data': result
                    })
                except ImportError:
                    return jsonify({'status': 'error', 'message': 'MemoryVault not available'}), 500
                
            except Exception as e:
                logger.error(f"Error validating story: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/memoryvault/create-funded-wallet', methods=['POST'])
        def create_funded_wallet():
            """Create a new MemoryVault wallet with automatic funding (Solana-style), with interactive story validation and user confirmation."""
            try:
                data = request.get_json()
                if not data or 'story' not in data:
                    return jsonify({'status': 'error', 'message': 'Story is required'}), 400
                
                story = data['story']
                funding_amount = float(data.get('funding_amount', 0.000001))  # Default 1 IBE (1/1,000,000 LAK)
                force = bool(data.get('force', False))
                
                # Import MemoryVault functions
                try:
                    from address import generate_address_from_story as mv_generate
                    from address import validate_story_personalness as mv_validate
                    
                    # First validate the story
                    validation = mv_validate(story)
                    personalness_score = validation.get('personalness_score', 0.0)
                    suggestions = validation.get('suggestions', []) if 'suggestions' in validation else []
                    
                    if personalness_score < 0.5 and not force:
                        # Return feedback and require explicit confirmation to proceed
                        return jsonify({
                            'status': 'warning',
                            'message': 'Story is not personal enough. Please include more personal details or confirm you want to proceed.',
                            'data': {
                                'validation': validation,
                                'suggestions': suggestions,
                                'can_proceed': True,
                                'force_required': True
                            }
                        }), 200
                    
                    # Generate the address
                    result = mv_generate(story)
                    
                    # Auto-fund the generated address
                    funding_result = self._fund_address(result['address'], funding_amount)
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
                except ImportError:
                    return jsonify({'status': 'error', 'message': 'MemoryVault not available'}), 500
                
            except Exception as e:
                logger.error(f"Error creating funded wallet: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Faucet endpoint
        @self.app.route('/api/faucet', methods=['POST'])
        def faucet():
            """Request test tokens from faucet"""
            try:
                data = request.get_json()
                if not data or 'address' not in data:
                    return jsonify({'status': 'error', 'message': 'Address is required'}), 400
                
                address = data['address']
                amount = float(data.get('amount', 100.0))  # Default 100 tokens
                
                # Validate address
                if not is_valid_address(address):
                    return jsonify({'status': 'error', 'message': 'Invalid address'}), 400
                
                # Get genesis account to determine correct nonce
                genesis_account = self.blockchain.ledger.get_account('genesis')
                if not genesis_account:
                    return jsonify({'status': 'error', 'message': 'Genesis account not found'}), 500
                
                # Create faucet transaction with correct nonce
                faucet_tx = Transaction(
                    from_address='genesis',
                    to_address=address,
                    amount=amount,
                    transaction_type=TransactionType.TRANSFER,
                    gas_limit=21000,
                    gas_price=1.0,
                    nonce=genesis_account.nonce  # Use correct nonce
                )
                
                success = self.blockchain.add_transaction(faucet_tx)
                if not success:
                    return jsonify({'status': 'error', 'message': 'Faucet transaction failed'}), 400
                
                # Broadcast faucet transaction to P2P network
                if self.blockchain.p2p_node:
                    try:
                        # Check if P2P node has connections
                        if hasattr(self.blockchain.p2p_node, 'connections') and len(self.blockchain.p2p_node.connections) > 0:
                            # Create a new event loop for broadcasting
                            import asyncio
                            import threading
                            
                            def broadcast_in_thread():
                                try:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(self.blockchain.broadcast_transaction(faucet_tx))
                                    loop.close()
                                except Exception as e:
                                    logger.error(f"Broadcast thread error: {e}")
                            
                            # Run broadcast in a separate thread
                            broadcast_thread = threading.Thread(target=broadcast_in_thread, daemon=True)
                            broadcast_thread.start()
                            
                            logger.info(f"Broadcasting faucet transaction {faucet_tx.hash} to {len(self.blockchain.p2p_node.connections)} peers")
                        else:
                            logger.warning(f"No P2P connections available for broadcasting faucet transaction {faucet_tx.hash}")
                    except Exception as e:
                        logger.error(f"Failed to broadcast faucet transaction {faucet_tx.hash}: {e}")
                        logger.error(f"P2P node status: {self.blockchain.p2p_node is not None}")
                        logger.error(f"P2P connections: {len(self.blockchain.p2p_node.connections) if hasattr(self.blockchain.p2p_node, 'connections') else 'Unknown'}")
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'message': f'{amount} tokens sent to {address}',
                        'transaction_hash': faucet_tx.hash
                    }
                })
            except Exception as e:
                logger.error(f"Error processing faucet request: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Web interface
        @self.app.route('/', methods=['GET'])
        def web_interface():
            """Simple web interface for blockchain interaction"""
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Lakha Blockchain API</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                    .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }
                    .method { font-weight: bold; color: #0066cc; }
                    .url { font-family: monospace; color: #333; }
                    .description { color: #666; margin-top: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Lakha Blockchain API</h1>
                    <p>Welcome to the Lakha blockchain HTTP API. Use the endpoints below to interact with the blockchain.</p>
                    
                    <div class="section">
                        <h2>📊 Status & Health</h2>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/health</div>
                            <div class="description">Health check endpoint</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/status</div>
                            <div class="description">Get blockchain status and network performance</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>📦 Blocks</h2>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/blocks?page=1&limit=10</div>
                            <div class="description">Get blocks with pagination</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/blocks/latest</div>
                            <div class="description">Get the latest block</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/blocks/{block_index}</div>
                            <div class="description">Get specific block by index</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>💸 Transactions</h2>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/transactions?page=1&limit=10</div>
                            <div class="description">Get transactions with pagination</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/transactions/pending</div>
                            <div class="description">Get pending transactions</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/transactions</div>
                            <div class="description">Submit a new transaction</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/transactions/{tx_hash}</div>
                            <div class="description">Get transaction by hash</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>👤 Accounts</h2>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/accounts</div>
                            <div class="description">Get all accounts</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/accounts/{address}</div>
                            <div class="description">Get account by address</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/accounts/{address}/balance</div>
                            <div class="description">Get account balance</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/accounts/{address}/nonce</div>
                            <div class="description">Get account nonce</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🔧 Smart Contracts</h2>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/contracts</div>
                            <div class="description">Get all contracts</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/contracts/{contract_address}</div>
                            <div class="description">Get contract by address</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/contracts/{contract_address}/state?key_path=</div>
                            <div class="description">Get contract state</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>⚡ Validators</h2>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/validators</div>
                            <div class="description">Get all validators</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/validators/{address}</div>
                            <div class="description">Get validator by address</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/validators</div>
                            <div class="description">Register a new validator</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>⛏️ Mining</h2>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/mining/start</div>
                            <div class="description">Start mining</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/mining/stop</div>
                            <div class="description">Stop mining</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="url">/api/mining/status</div>
                            <div class="description">Get mining status</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🛠️ Utilities</h2>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/utils/generate-address</div>
                            <div class="description">Generate a new Bech32 address</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/utils/validate-address</div>
                            <div class="description">Validate a Bech32 address</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🎭 MemoryVault</h2>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/memoryvault/create-funded-wallet</div>
                            <div class="description">Create funded wallet from story (Solana-style)</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/memoryvault/generate-from-story</div>
                            <div class="description">Generate address from personal story (with optional funding)</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/memoryvault/generate-from-mnemonic</div>
                            <div class="description">Generate address from mnemonic phrase (with optional funding)</div>
                        </div>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/memoryvault/validate-story</div>
                            <div class="description">Validate story personalness</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🚰 Faucet</h2>
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="url">/api/faucet</div>
                            <div class="description">Request test tokens from faucet</div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return html
    
    def _mining_loop(self):
        """Background mining loop"""
        while self.mining_active:
            try:
                if self.blockchain.pending_transactions:
                    success = self.blockchain.mine_block()
                    if success:
                        logger.info("Mined a new block")
                    else:
                        logger.warning("Failed to mine block")
                time.sleep(1)  # Wait 1 second between mining attempts
            except Exception as e:
                logger.error(f"Error in mining loop: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the Flask API server"""
        logger.info(f"Starting Lakha API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)
    
    def _fund_address(self, address: str, amount: float) -> dict:
        """Helper method to fund an address with LAK tokens"""
        try:
            # Validate address
            if not is_valid_address(address):
                return {'success': False, 'error': 'Invalid address'}
            
            # Get genesis account to determine correct nonce
            genesis_account = self.blockchain.ledger.get_account('genesis')
            if not genesis_account:
                return {'success': False, 'error': 'Genesis account not found'}
            
            # Create funding transaction with minimal gas for simple transfer
            funding_tx = Transaction(
                from_address='genesis',
                to_address=address,
                amount=amount,
                transaction_type=TransactionType.TRANSFER,
                gas_limit=100,  # Reduced gas limit for simple transfer
                gas_price=1.0,
                nonce=genesis_account.nonce
            )
            
            # Add transaction to pool
            success = self.blockchain.add_transaction(funding_tx)
            if not success:
                return {'success': False, 'error': 'Transaction validation failed'}
            
            # Broadcast funding transaction to P2P network
            if self.blockchain.p2p_node:
                try:
                    if hasattr(self.blockchain.p2p_node, 'connections') and len(self.blockchain.p2p_node.connections) > 0:
                        import asyncio
                        import threading
                        
                        def broadcast_in_thread():
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(self.blockchain.broadcast_transaction(funding_tx))
                                loop.close()
                            except Exception as e:
                                logger.error(f"Broadcast thread error: {e}")
                        
                        broadcast_thread = threading.Thread(target=broadcast_in_thread, daemon=True)
                        broadcast_thread.start()
                        
                        logger.info(f"Broadcasting funding transaction {funding_tx.hash} to {len(self.blockchain.p2p_node.connections)} peers")
                    else:
                        logger.warning(f"No P2P connections available for broadcasting funding transaction {funding_tx.hash}")
                except Exception as e:
                    logger.error(f"Failed to broadcast funding transaction {funding_tx.hash}: {e}")
            
            return {
                'success': True,
                'transaction_hash': funding_tx.hash,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Error funding address {address}: {e}")
            return {'success': False, 'error': str(e)}
    
    def stop(self):
        """Stop the API server"""
        self.mining_active = False
        logger.info("Stopping Lakha API server")

def main():
    """Main entry point for the API server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lakha Blockchain HTTP API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--db-path', default='lakha_db', help='Database path')
    parser.add_argument('--p2p-port', type=int, help='P2P port (optional)')
    parser.add_argument('--p2p-peers', nargs='*', help='P2P peer addresses')
    
    args = parser.parse_args()
    
    # Create blockchain instance
    blockchain = LahkaBlockchain(
        test_mode=False,
        db_path=args.db_path,
        p2p_port=args.p2p_port,
        p2p_peers=args.p2p_peers
    )
    
    # Create API instance
    api = LakhaAPI(blockchain, host=args.host, port=args.port)
    
    print(f"🚀 Starting Lakha Blockchain API on {args.host}:{args.port}")
    print(f"📁 Database: {args.db_path}")
    if args.p2p_port:
        print(f"🌐 P2P Port: {args.p2p_port}")
    if args.p2p_peers:
        print(f"🔗 P2P Peers: {args.p2p_peers}")
    
    try:
        api.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        api.stop()
        blockchain.close()

if __name__ == '__main__':
    main() 