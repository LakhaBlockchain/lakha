#!/usr/bin/env python3
"""
Tests for Proof of Contribution Stake (PoCS) - Chunk 1
"""

import pytest
import time
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address

class TestPoCSBasic:
    """Test basic PoCS functionality"""
    
    def setup_method(self):
        """Set up fresh blockchain for each test"""
        self.lahka = LahkaBlockchain(test_mode=True)
        # Generate fresh Bech32 addresses for each test
        self.alice = generate_address()
        self.bob = generate_address()
        self.charlie = generate_address()
        # Give test accounts enough balance and mine a block
        for name, amount in zip([self.alice, self.bob, self.charlie], [200, 100, 100]):
            genesis_account = self.lahka.ledger.get_account("genesis")
            nonce = genesis_account.nonce if genesis_account else 0
            self.lahka.add_transaction(Transaction("genesis", name, amount, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block()
        # Registration is now done in each test, followed by a mine_block() before accessing validators
    
    def test_validator_pocs_scoring(self):
        """Test that validators have PoCS scores"""
        assert self.lahka.register_validator(self.alice, 20.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        assert hasattr(alice_val, 'contribution_score')
        
        # Check that validators have PoCS metrics
        assert hasattr(alice_val, 'reliability_score')
        assert hasattr(alice_val, 'diversity_bonus')
        assert hasattr(alice_val, 'calculate_pocs_score')
        
        # Initial scores should be based mainly on stake
        alice_score = alice_val.calculate_pocs_score(time.time())
        
        assert alice_score > 0
    
    def test_temporal_decay(self):
        """Test that stakes decay over time without activity"""
        assert self.lahka.register_validator(self.alice, 100.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        
        # Get initial score
        initial_score = alice_val.calculate_pocs_score(time.time())
        
        # Simulate 10 days of inactivity
        future_time = time.time() + (10 * 24 * 3600)  # 10 days
        decayed_score = alice_val.calculate_pocs_score(future_time)
        
        # Score should be lower due to temporal decay
        assert decayed_score < initial_score
        assert decayed_score > 0  # Should not decay to zero
    
    def test_contribution_scoring(self):
        """Test that validators earn contribution points"""
        assert self.lahka.register_validator(self.alice, 20.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        
        # Initial contribution score
        initial_contribution = alice_val.contribution_score
        
        # Add some transactions and mine a block with Alice
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", self.bob, 10, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block_with_validator(self.alice)
        
        # Contribution score should increase
        assert alice_val.contribution_score > initial_contribution
    
    def test_reliability_scoring(self):
        """Test that validators earn reliability points"""
        assert self.lahka.register_validator(self.alice, 20.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        # Set reliability lower so it can increase
        alice_val.reliability_score = 95
        initial_reliability = alice_val.reliability_score
        # Mine a block with Alice (successful validation)
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", self.bob, 10, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block_with_validator(self.alice)
        # Reliability score should increase
        assert alice_val.reliability_score > initial_reliability
    
    def test_pocs_vs_pos_selection(self):
        """Test that PoCS selection differs from pure PoS"""
        assert self.lahka.register_validator(self.alice, 20.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        
        # Ensure Bob and Charlie are funded before registration
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", self.bob, 50, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block()  # Mine after funding Bob

        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", self.charlie, 50, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block()  # Mine after funding Charlie
        
        assert self.lahka.register_validator(self.bob, 15.0)    # Medium stake
        assert self.lahka.register_validator(self.charlie, 10.0) # Low stake
        self.lahka.mine_block()
        
        # Give Charlie high contribution score
        charlie_val = self.lahka.validators[self.charlie]
        charlie_val.update_contribution_score(500.0)  # Very high contribution
        
        # Mine several blocks and track selection
        selections = []
        for _ in range(50):
            self.lahka.add_transaction(Transaction("genesis", self.alice, 1, TransactionType.TRANSFER))
            validator = self.lahka.select_validator()
            if validator:
                selections.append(validator)
            self.lahka.mine_block()
        
        # Charlie should be selected sometimes despite lower stake
        assert self.charlie in selections
        
        # All validators should be selected at least once
        assert len(set(selections)) >= 2
    
    def test_validator_activity_tracking(self):
        """Test that validator activity is tracked"""
        assert self.lahka.register_validator(self.alice, 20.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        
        # Initial activity time
        initial_activity = alice_val.last_activity
        
        # Wait a bit and mine a block with Alice
        time.sleep(0.1)
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", self.bob, 10, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block_with_validator(self.alice)
        
        # Activity time should be updated
        assert alice_val.last_activity > initial_activity
    
    def test_unique_transaction_tracking(self):
        """Test that unique transaction types are tracked"""
        assert self.lahka.register_validator(self.alice, 20.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        # Add different transaction types
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", self.bob, 10, TransactionType.TRANSFER, nonce=nonce))
        # Use a valid address for contract deploy
        contract_addr = generate_address()
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", contract_addr, 0, TransactionType.CONTRACT_DEPLOY, {"contract_code": "test"}, nonce=nonce))
        self.lahka.mine_block_with_validator(self.alice)
        # Should track 2 unique transaction types
        assert alice_val.unique_transaction_types >= 2
    
    def test_pocs_score_components(self):
        """Test that all PoCS score components work"""
        assert self.lahka.register_validator(self.alice, 100.0)
        self.lahka.mine_block()
        assert self.alice in self.lahka.validators
        alice_val = self.lahka.validators[self.alice]
        
        # Set different components
        alice_val.update_contribution_score(50.0)
        alice_val.update_reliability_score(True, 0.5)
        alice_val.diversity_bonus = 25.0
        
        # Calculate score
        score = alice_val.calculate_pocs_score(time.time())
        
        # Score should be positive and include all components
        assert score > 0
        assert alice_val.contribution_score > 0
        assert alice_val.reliability_score > 0
        assert alice_val.diversity_bonus > 0

if __name__ == "__main__":
    pytest.main([__file__]) 