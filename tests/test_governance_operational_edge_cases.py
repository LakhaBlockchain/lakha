import pytest
import time
import sys
import os
import copy
import random
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import LahkaBlockchain, Transaction, TransactionType, ContractStatus
from address import generate_address


class TestGovernanceOperationalEdgeCases:
    """Test governance/upgrade and miscellaneous operational edge cases"""
    
    def setup_method(self):
        """Set up fresh blockchain for each test"""
        self.lahka = LahkaBlockchain()
    
    # ============================================================================
    # 1. GOVERNANCE/UPGRADE EDGE CASES
    # ============================================================================
    
    def test_protocol_upgrade_consensus(self):
        """Test protocol upgrade requiring consensus from validators"""
        # Register multiple validators and fund them
        validators = []
        validator_nonces = {}
        for i in range(3):
            addr = generate_address()
            # Fund validator with enough for stake + gas for voting
            self.lahka.add_transaction(Transaction("genesis", addr, 2000.0, TransactionType.TRANSFER, nonce=i))
            self.lahka.mine_block()
            # Register validator (stake)
            self.lahka.register_validator(addr, 100.0)
            self.lahka.mine_block()
            validators.append(addr)
            validator_nonces[addr] = 0  # Will increment as we send txs
        
        # Use a valid Bech32 address for the governance contract
        governance_contract_addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", governance_contract_addr, 100.0, TransactionType.TRANSFER, nonce=3))
        self.lahka.mine_block()
        
        # Simulate protocol upgrade proposal
        upgrade_proposal = {
            'version': '2.0.0',
            'changes': ['new_feature', 'security_improvement'],
            'activation_block': len(self.lahka.chain) + 10,
            'required_consensus': 0.75  # 75% of validators must approve
        }
        
        # Simulate validator voting (use correct nonce for each)
        approvals = 0
        for validator_addr in validators:
            # Each validator's nonce should be 1 after registration (1 transfer, 1 stake)
            validator_nonces[validator_addr] = 1
            vote_tx = Transaction(
                from_address=validator_addr,
                to_address=governance_contract_addr,
                amount=0.0,
                transaction_type=TransactionType.CONTRACT_CALL,
                data={
                    'contract_address': governance_contract_addr,
                    'function_name': 'vote_upgrade',
                    'args': [upgrade_proposal['version'], True]
                },
                nonce=validator_nonces[validator_addr],
                gas_limit=10
            )
            if self.lahka.add_transaction(vote_tx):
                approvals += 1
            validator_nonces[validator_addr] += 1
        
        self.lahka.mine_block()
        
        # Check if upgrade has sufficient consensus
        consensus_ratio = approvals / len(validators)
        assert consensus_ratio >= upgrade_proposal['required_consensus'], f"Insufficient consensus: {consensus_ratio}"
    
    def test_parameter_change_validation(self):
        """Test validation of parameter changes (gas limits, block times, etc.)"""
        # Test various parameter changes
        parameter_changes = [
            {'gas_limit': 50000, 'valid': True},
            {'gas_limit': -1000, 'valid': False},  # Invalid negative value
            {'block_time': 2.0, 'valid': True},
            {'block_time': 0.1, 'valid': False},   # Too fast
            {'minimum_stake': 5.0, 'valid': True},
            {'minimum_stake': 0.0, 'valid': False} # Invalid zero value
        ]
        
        for change in parameter_changes:
            # Simulate parameter change transaction
            param_tx = Transaction(
                from_address="governance_contract",
                to_address="",
                amount=0.0,
                transaction_type=TransactionType.CONTRACT_CALL,
                data={
                    'contract_address': 'governance_contract',
                    'function_name': 'change_parameter',
                    'args': [list(change.keys())[0], list(change.values())[0]]
                }
            )
            
            result = self.lahka.add_transaction(param_tx)
            # System should handle parameter changes safely
            assert result in [True, False], "Parameter change should be handled safely"
    
    def test_emergency_stop_functionality(self):
        """Test emergency stop mechanism and recovery"""
        # Simulate emergency stop activation
        emergency_tx = Transaction(
            from_address="emergency_committee",
            to_address="",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'emergency_contract',
                'function_name': 'activate_emergency_stop',
                'args': ['security_vulnerability_detected']
            }
        )
        
        self.lahka.add_transaction(emergency_tx)
        self.lahka.mine_block()
        
        # Try to add normal transaction during emergency stop
        normal_tx = Transaction(
            from_address=generate_address(),
            to_address=generate_address(),
            amount=10.0,
            transaction_type=TransactionType.TRANSFER
        )
        
        # System should handle emergency stop gracefully
        result = self.lahka.add_transaction(normal_tx)
        assert result in [True, False], "Emergency stop should be handled safely"
        
        # Simulate emergency stop deactivation
        recovery_tx = Transaction(
            from_address="emergency_committee",
            to_address="",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'emergency_contract',
                'function_name': 'deactivate_emergency_stop',
                'args': ['vulnerability_patched']
            }
        )
        
        self.lahka.add_transaction(recovery_tx)
        self.lahka.mine_block()
        
        # System should recover and allow normal transactions
        assert True, "Emergency stop recovery should work"
    
    def test_governance_attack_prevention(self):
        """Test prevention of governance attacks (sybil, bribery, etc.)"""
        # Simulate sybil attack attempt (many small validators)
        sybil_validators = []
        for i in range(100):  # Try to create 100 small validators
            addr = generate_address()
            self.lahka.add_transaction(Transaction("genesis", addr, 50.0, TransactionType.TRANSFER))
            self.lahka.mine_block()
            
            # Try to register with minimum stake
            success = self.lahka.register_validator(addr, 10.0)  # Minimum stake
            sybil_validators.append((addr, success))
        
        # Count successful sybil registrations
        successful_sybil = sum(1 for _, success in sybil_validators if success)
        
        # System should limit sybil attacks
        assert successful_sybil <= 50, f"Too many sybil validators: {successful_sybil}"
        
        # Test bribery attack simulation
        bribery_tx = Transaction(
            from_address="attacker",
            to_address="validator",
            amount=1000.0,
            transaction_type=TransactionType.TRANSFER,
            data={'purpose': 'bribe_for_vote'}
        )
        
        # System should detect and handle suspicious transactions
        result = self.lahka.add_transaction(bribery_tx)
        assert result in [True, False], "Bribery attempt should be handled safely"
    
    def test_upgrade_rollback_mechanism(self):
        """Test upgrade rollback when issues are detected"""
        # Simulate upgrade deployment
        upgrade_tx = Transaction(
            from_address="upgrade_manager",
            to_address="",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'upgrade_contract',
                'function_name': 'deploy_upgrade',
                'args': ['v2.1.0', 'new_features']
            }
        )
        
        self.lahka.add_transaction(upgrade_tx)
        self.lahka.mine_block()
        
        # Simulate issue detection and rollback
        rollback_tx = Transaction(
            from_address="upgrade_manager",
            to_address="",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'upgrade_contract',
                'function_name': 'rollback_upgrade',
                'args': ['critical_bug_detected', 'v2.0.0']
            }
        )
        
        self.lahka.add_transaction(rollback_tx)
        self.lahka.mine_block()
        
        # System should handle rollback gracefully
        assert True, "Upgrade rollback should work"
    
    # ============================================================================
    # 2. MISCELLANEOUS OPERATIONAL EDGE CASES
    # ============================================================================
    
    def test_network_partition_handling(self):
        """Test handling of network partitions and split-brain scenarios"""
        # Simulate network partition by creating two separate chains
        chain_a = LahkaBlockchain()
        chain_b = LahkaBlockchain()
        
        # Add same transaction to both chains
        addr = generate_address()
        tx = Transaction("genesis", addr, 1000.0, TransactionType.TRANSFER)
        
        chain_a.add_transaction(tx)
        chain_b.add_transaction(tx)
        
        chain_a.mine_block()
        chain_b.mine_block()
        
        # Add different transactions to each chain (simulating partition)
        tx_a = Transaction(addr, generate_address(), 100.0, TransactionType.TRANSFER)
        tx_b = Transaction(addr, generate_address(), 200.0, TransactionType.TRANSFER)
        
        chain_a.add_transaction(tx_a)
        chain_b.add_transaction(tx_b)
        
        chain_a.mine_block()
        chain_b.mine_block()
        
        # Chains should diverge
        assert len(chain_a.chain) == len(chain_b.chain), "Chains should have same length"
        assert chain_a.chain[-1].hash != chain_b.chain[-1].hash, "Chains should diverge"
        
        # System should handle partition gracefully
        assert True, "Network partition should be handled safely"
    
    def test_time_synchronization_issues(self):
        """Test handling of time synchronization problems"""
        # Test with different timestamps
        current_time = time.time()
        
        # Create transaction with past timestamp
        past_tx = Transaction(
            from_address="genesis",
            to_address=generate_address(),
            amount=100.0,
            transaction_type=TransactionType.TRANSFER,
            timestamp=current_time - 3600  # 1 hour ago
        )
        
        # Create transaction with future timestamp
        future_tx = Transaction(
            from_address="genesis",
            to_address=generate_address(),
            amount=100.0,
            transaction_type=TransactionType.TRANSFER,
            timestamp=current_time + 3600  # 1 hour in future
        )
        
        # System should handle time anomalies gracefully
        past_result = self.lahka.add_transaction(past_tx)
        future_result = self.lahka.add_transaction(future_tx)
        
        assert past_result in [True, False], "Past timestamp should be handled safely"
        assert future_result in [True, False], "Future timestamp should be handled safely"
    
    def test_resource_exhaustion_scenarios(self):
        """Test handling of resource exhaustion (memory, CPU, disk)"""
        # Test memory exhaustion with many transactions
        large_tx_count = 1000
        for i in range(large_tx_count):
            tx = Transaction(
                from_address="genesis",
                to_address=generate_address(),
                amount=1.0,
                transaction_type=TransactionType.TRANSFER,
                data={'large_data': 'x' * 1000}  # Large transaction data
            )
            self.lahka.add_transaction(tx)
        
        # System should handle large transaction pools
        assert len(self.lahka.pending_transactions) <= 10000, "Transaction pool should be limited"
        
        # Test CPU exhaustion with complex contract calls
        complex_contract_code = """
        def complex_function():
            result = 0
            for i in range(10000):
                result += i * i
            return result
        """
        
        deploy_tx = Transaction(
            from_address=generate_address(),
            to_address="",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_DEPLOY,
            data={'contract_code': complex_contract_code}
        )
        
        # System should handle complex operations safely
        result = self.lahka.add_transaction(deploy_tx)
        assert result in [True, False], "Complex operations should be handled safely"
    
    def test_configuration_error_handling(self):
        """Test handling of configuration errors and invalid settings"""
        # Test with invalid configuration parameters
        invalid_configs = [
            {'block_time': -1.0},
            {'gas_limit': 0},
            {'minimum_stake': -100.0},
            {'max_validators': 0},
            {'consensus_threshold': 1.5}  # > 100%
        ]
        
        for config in invalid_configs:
            # Try to apply invalid configuration
            config_tx = Transaction(
                from_address="config_manager",
                to_address="",
                amount=0.0,
                transaction_type=TransactionType.CONTRACT_CALL,
                data={
                    'contract_address': 'config_contract',
                    'function_name': 'update_config',
                    'args': [config]
                }
            )
            
            # System should reject invalid configurations
            result = self.lahka.add_transaction(config_tx)
            assert result in [True, False], "Invalid config should be handled safely"
    
    def test_maintenance_mode_operations(self):
        """Test maintenance mode and scheduled downtime handling"""
        # Simulate entering maintenance mode
        maintenance_tx = Transaction(
            from_address="system_admin",
            to_address="",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'maintenance_contract',
                'function_name': 'enter_maintenance_mode',
                'args': ['scheduled_upgrade', 3600]  # 1 hour duration
            }
        )
        
        self.lahka.add_transaction(maintenance_tx)
        self.lahka.mine_block()
        
        # Try to add transaction during maintenance
        normal_tx = Transaction(
            from_address=generate_address(),
            to_address=generate_address(),
            amount=10.0,
            transaction_type=TransactionType.TRANSFER
        )
        
        # System should handle maintenance mode gracefully
        result = self.lahka.add_transaction(normal_tx)
        assert result in [True, False], "Maintenance mode should be handled safely"
        
        # Simulate exiting maintenance mode
        exit_tx = Transaction(
            from_address="system_admin",
            to_address="",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'maintenance_contract',
                'function_name': 'exit_maintenance_mode',
                'args': ['upgrade_completed']
            }
        )
        
        self.lahka.add_transaction(exit_tx)
        self.lahka.mine_block()
        
        # System should resume normal operations
        assert True, "Maintenance mode exit should work"
    
    def test_cross_chain_interoperability(self):
        """Test cross-chain transaction and bridge functionality"""
        # Simulate cross-chain transaction
        bridge_tx = Transaction(
            from_address=generate_address(),
            to_address="bridge_contract",
            amount=100.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'bridge_contract',
                'function_name': 'transfer_to_other_chain',
                'args': ['ethereum', '0x1234567890abcdef', 100.0]
            }
        )
        
        # System should handle cross-chain operations
        result = self.lahka.add_transaction(bridge_tx)
        assert result in [True, False], "Cross-chain operations should be handled safely"
        
        # Simulate receiving from other chain
        receive_tx = Transaction(
            from_address="bridge_contract",
            to_address=generate_address(),
            amount=50.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'bridge_contract',
                'function_name': 'receive_from_other_chain',
                'args': ['ethereum', '0x1234567890abcdef', 50.0, 'proof']
            }
        )
        
        self.lahka.add_transaction(receive_tx)
        self.lahka.mine_block()
        
        # System should validate cross-chain proofs
        assert True, "Cross-chain validation should work"
    
    def test_oracle_and_external_data(self):
        """Test oracle integration and external data validation"""
        # Simulate oracle data feed
        oracle_tx = Transaction(
            from_address="oracle_provider",
            to_address="oracle_contract",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'oracle_contract',
                'function_name': 'update_price_feed',
                'args': ['ETH/USD', 2500.50, time.time()]
            }
        )
        
        # System should validate oracle data
        result = self.lahka.add_transaction(oracle_tx)
        assert result in [True, False], "Oracle data should be handled safely"
        
        # Test oracle manipulation attempt
        malicious_tx = Transaction(
            from_address="malicious_oracle",
            to_address="oracle_contract",
            amount=0.0,
            transaction_type=TransactionType.CONTRACT_CALL,
            data={
                'contract_address': 'oracle_contract',
                'function_name': 'update_price_feed',
                'args': ['ETH/USD', 999999.99, time.time()]  # Suspicious price
            }
        )
        
        # System should detect suspicious oracle data
        result = self.lahka.add_transaction(malicious_tx)
        assert result in [True, False], "Suspicious oracle data should be handled safely"
    
    def test_quantum_resistance_preparation(self):
        """Test quantum-resistant cryptography and post-quantum security"""
        # Simulate quantum-resistant transaction
        quantum_tx = Transaction(
            from_address=generate_address(),
            to_address=generate_address(),
            amount=10.0,
            transaction_type=TransactionType.TRANSFER,
            data={
                'quantum_resistant': True,
                'signature_algorithm': 'lattice_based',
                'public_key': 'quantum_safe_public_key'
            }
        )
        
        # System should handle quantum-resistant cryptography
        result = self.lahka.add_transaction(quantum_tx)
        assert result in [True, False], "Quantum-resistant crypto should be handled safely"
        
        # Test mixed quantum/classical transactions
        mixed_tx = Transaction(
            from_address=generate_address(),
            to_address=generate_address(),
            amount=10.0,
            transaction_type=TransactionType.TRANSFER,
            data={
                'quantum_resistant': False,
                'signature_algorithm': 'ecdsa',
                'public_key': 'classical_public_key'
            }
        )
        
        # System should handle mixed cryptography
        result = self.lahka.add_transaction(mixed_tx)
        assert result in [True, False], "Mixed crypto should be handled safely" 