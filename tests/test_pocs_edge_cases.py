import pytest
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import LahkaBlockchain, Transaction, TransactionType, Validator
from address import generate_address


class TestPoCSEdgeCases:
    """Test PoCS score edge cases and boundary conditions"""
    
    def setup_method(self):
        """Set up fresh blockchain for each test"""
        self.lahka = LahkaBlockchain()
    
    def test_extreme_stake_values(self):
        """Test with very high (1M+) and very low (0.1) stakes"""
        gas_limit = 21000
        gas_price = 1.0
        # Test extremely high stake
        high_stake_addr = generate_address()
        high_stake = 999999.0
        high_funding = high_stake + gas_limit * gas_price
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", high_stake_addr, high_funding, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block()
        assert self.lahka.register_validator(high_stake_addr, high_stake), "High stake registration should succeed"
        self.lahka.mine_block()
        
        # Test very low stake (but above minimum)
        low_stake_addr = generate_address()
        low_stake = 10.1
        low_funding = low_stake + gas_limit * gas_price
        genesis_account = self.lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        self.lahka.add_transaction(Transaction("genesis", low_stake_addr, low_funding, TransactionType.TRANSFER, nonce=nonce))
        self.lahka.mine_block()
        assert self.lahka.register_validator(low_stake_addr, low_stake), "Low stake registration should succeed"
        self.lahka.mine_block()
        
        # Calculate PoCS scores
        high_stake_validator = self.lahka.validators[high_stake_addr]
        low_stake_validator = self.lahka.validators[low_stake_addr]
        
        current_time = time.time()
        high_score = high_stake_validator.calculate_pocs_score(current_time)
        low_score = low_stake_validator.calculate_pocs_score(current_time)
        
        # High stake should have much higher score
        assert high_score > low_score * 100, "High stake should have significantly higher score"
        assert high_score > 0, "High stake score should be positive"
        assert low_score > 0, "Low stake score should be positive"
    
    def test_negative_contribution_scores(self):
        """Test handling of negative contribution scores"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        
        # Set negative contribution score
        validator.contribution_score = -100.0
        
        # Calculate PoCS score
        current_time = time.time()
        score = validator.calculate_pocs_score(current_time)
        
        # Score should still be positive (due to stake component)
        assert score > 0, "PoCS score should remain positive even with negative contribution"
        
        # Test with extreme negative values
        validator.contribution_score = -999999.0
        extreme_score = validator.calculate_pocs_score(current_time)
        assert extreme_score > 0, "PoCS score should remain positive even with extreme negative contribution"
    
    def test_score_overflow_handling(self):
        """Test with extremely large scores that might overflow"""
        gas_limit = 21000
        gas_price = 1.0
        addr = generate_address()
        stake = 999999.0
        funding = stake + gas_limit * gas_price
        self.lahka.add_transaction(Transaction("genesis", addr, funding, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, stake)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        
        # Set extremely high values for all components
        validator.contribution_score = 999999.0
        validator.reliability_score = 999999.0
        validator.reputation_score = 999999.0
        validator.collaboration_score = 999999.0
        validator.network_health_contribution = 999999.0
        
        # Calculate PoCS score
        current_time = time.time()
        score = validator.calculate_pocs_score(current_time)
        
        # Score should be finite and positive
        assert score > 0, "Score should be positive"
        assert score < float('inf'), "Score should not be infinite"
        assert score > 999999.0, "Score should be very high with extreme values"
    
    def test_temporal_decay_edge_cases(self):
        """Test stake decay after very long periods (years)"""
        gas_limit = 21000
        gas_price = 1.0
        addr = generate_address()
        stake = 500.0
        funding = stake + gas_limit * gas_price
        self.lahka.add_transaction(Transaction("genesis", addr, funding, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, stake)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        
        # Simulate very long inactivity (10 years)
        very_old_time = time.time() - (10 * 365 * 24 * 3600)  # 10 years ago
        validator.last_activity = very_old_time
        
        # Calculate PoCS score
        current_time = time.time()
        decayed_score = validator.calculate_pocs_score(current_time)
        
        # Score should be significantly reduced but not zero
        assert decayed_score > 0, "Decayed score should still be positive"
        assert decayed_score < 500.0, "Decayed score should be less than original stake"
        
        # Test with extremely long inactivity (100 years)
        extreme_old_time = time.time() - (100 * 365 * 24 * 3600)  # 100 years ago
        validator.last_activity = extreme_old_time
        
        extreme_decayed_score = validator.calculate_pocs_score(current_time)
        assert extreme_decayed_score > 0, "Extreme decayed score should still be positive"
        # Note: After a certain point, decay plateaus at minimum (0.1 * stake)
        # So extreme decay might not be lower than regular decay
        assert extreme_decayed_score <= decayed_score, "Extreme decay should not increase score"
    
    def test_zero_stake_validators(self):
        """Test validators who stake all their funds"""
        gas_limit = 21000
        gas_price = 1.0
        addr = generate_address()
        stake = 10.0
        funding = stake + gas_limit * gas_price
        self.lahka.add_transaction(Transaction("genesis", addr, funding, TransactionType.TRANSFER))
        self.lahka.mine_block()
        assert self.lahka.register_validator(addr, stake), "Should be able to stake minimum amount"
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        score = validator.calculate_pocs_score(current_time)
        
        # Score should be positive but low
        assert score > 0, "Zero balance validator should still have positive score"
        assert score < 51.0, "Zero balance validator should have low score"
        
        # Check balance after staking (should be gas cost, not zero)
        balance = self.lahka.get_balance(addr)
        assert balance > 0.0, "Balance should be positive after staking (gas cost remains)"
        assert balance < funding, "Balance should be less than original funding"
    
    def test_validator_with_maximum_penalties(self):
        """Test validator with 5x penalty multiplier"""
        gas_limit = 21000
        gas_price = 1.0
        addr = generate_address()
        stake = 500.0
        funding = stake + gas_limit * gas_price
        self.lahka.add_transaction(Transaction("genesis", addr, funding, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, stake)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        
        # Apply multiple penalties to reach maximum multiplier
        for i in range(10):  # Apply 10 penalties to ensure 5x multiplier
            validator.apply_penalty("test_penalty", 10.0, f"Penalty {i}")
        
        # Verify penalty multiplier is at maximum
        assert validator.current_penalty_multiplier >= 5.0, "Penalty multiplier should be at maximum"
        assert validator.rehabilitation_progress == 0.0, "Rehabilitation should start at 0 after penalties"
        
        # Calculate PoCS score
        current_time = time.time()
        penalized_score = validator.calculate_pocs_score(current_time)
        
        # Score should be significantly reduced
        assert penalized_score > 0, "Penalized score should still be positive"
        assert penalized_score < 500.0, "Penalized score should be less than stake"
        
        # Test rehabilitation (now faster with updated formula)
        print(f"Starting rehabilitation with progress: {validator.rehabilitation_progress}")
        for i in range(20):  # Reduced from 100 to 20 due to faster rehabilitation
            validator.earn_contribution_credits("rehabilitation", 5.0, f"Rehab {i}")
            print(f"After rehab {i+1}: progress={validator.rehabilitation_progress}, multiplier={validator.current_penalty_multiplier}")
        
        # Check if rehabilitation reduced penalty
        assert validator.current_penalty_multiplier < 5.0, "Penalty multiplier should be reduced after rehabilitation"
    
    def test_score_caching_edge_cases(self):
        """Test PoCS score caching behavior"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        
        # Calculate score first time
        current_time = time.time()
        score1 = validator.calculate_pocs_score(current_time)
        
        # Calculate score immediately after (should use cache)
        score2 = validator.calculate_pocs_score(current_time)
        assert score1 == score2, "Cached score should be identical"
        
        # Force recalculation
        score3 = validator.calculate_pocs_score(current_time, force_recalculate=True)
        assert score1 == score3, "Forced recalculation should give same result"
        
        # Wait for cache to expire and recalculate
        time.sleep(0.1)  # Small delay
        validator._score_cache_duration = 0.01  # Very short cache duration
        score4 = validator.calculate_pocs_score(time.time())
        # Allow for small floating-point differences due to time drift
        assert abs(score1 - score4) < 0.1, "Expired cache should give similar result (within 0.1 tolerance)"
    
    def test_dynamic_weight_adjustments(self):
        """Test dynamic weight adjustments under different network conditions"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        
        # Test high load condition
        validator.adjust_dynamic_weight("high_load", 1.2)
        high_load_score = validator.calculate_pocs_score(current_time)
        
        # Test low load condition
        validator.adjust_dynamic_weight("low_load", 0.8)
        low_load_score = validator.calculate_pocs_score(current_time)
        
        # Test normal condition
        validator.adjust_dynamic_weight("normal", 1.0)
        normal_score = validator.calculate_pocs_score(current_time)
        
        # Scores should be different based on network conditions
        assert high_load_score > low_load_score, "High load should increase score"
        assert normal_score > low_load_score, "Normal should be higher than low load"
        assert high_load_score > normal_score, "High load should be higher than normal"
    
    def test_collaboration_score_effects(self):
        """Test collaboration score effects on PoCS score"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        
        # Calculate baseline score
        baseline_score = validator.calculate_pocs_score(current_time)
        
        # Add collaboration score
        validator.update_collaboration_score("code_review", 50.0)
        collaboration_score = validator.calculate_pocs_score(current_time)
        
        # Collaboration should increase score
        assert collaboration_score > baseline_score, "Collaboration should increase score"
        
        # Add more collaboration
        validator.update_collaboration_score("documentation", 30.0)
        more_collaboration_score = validator.calculate_pocs_score(current_time)
        
        assert more_collaboration_score > collaboration_score, "More collaboration should increase score further"
    
    def test_network_health_contribution_effects(self):
        """Test network health contribution effects on PoCS score"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        
        # Calculate baseline score
        baseline_score = validator.calculate_pocs_score(current_time)
        
        # Add network health contribution
        validator.update_network_health_contribution("latency_improvement", 25.0)
        health_score = validator.calculate_pocs_score(current_time)
        
        # Network health should increase score
        assert health_score > baseline_score, "Network health should increase score"
        
        # Add more network health contributions
        validator.update_network_health_contribution("security_audit", 15.0)
        more_health_score = validator.calculate_pocs_score(current_time)
        
        assert more_health_score > health_score, "More network health should increase score further"
    
    def test_reputation_score_effects(self):
        """Test reputation score effects on PoCS score"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        
        # Calculate baseline score (default reputation = 100.0)
        baseline_score = validator.calculate_pocs_score(current_time)
        print(f"Baseline score (reputation=100.0): {baseline_score}")
        
        # Set high reputation (higher than default) and invalidate cache
        validator.reputation_score = 150.0  # Increased from 95.0 to 150.0
        validator._last_score_calculation = 0.0  # Invalidate cache
        high_reputation_score = validator.calculate_pocs_score(current_time)
        print(f"High reputation score (reputation=150.0): {high_reputation_score}")
        
        # Set low reputation (lower than default) and invalidate cache
        validator.reputation_score = 20.0
        validator._last_score_calculation = 0.0  # Invalidate cache
        low_reputation_score = validator.calculate_pocs_score(current_time)
        print(f"Low reputation score (reputation=20.0): {low_reputation_score}")
        
        # High reputation should increase score
        assert high_reputation_score > baseline_score, "High reputation should increase score"
        assert low_reputation_score < baseline_score, "Low reputation should decrease score"
        assert high_reputation_score > low_reputation_score, "High reputation should be better than low"
    
    def test_reliability_score_effects(self):
        """Test reliability score effects on PoCS score"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        
        # Calculate baseline score (default reliability = 100.0)
        baseline_score = validator.calculate_pocs_score(current_time)
        print(f"Baseline score (reliability=100.0): {baseline_score}")
        
        # Set high reliability (higher than default) and invalidate cache
        validator.reliability_score = 150.0  # Increased from 95.0 to 150.0
        validator._last_score_calculation = 0.0  # Invalidate cache
        high_reliability_score = validator.calculate_pocs_score(current_time)
        print(f"High reliability score (reliability=150.0): {high_reliability_score}")
        
        # Set low reliability (lower than default) and invalidate cache
        validator.reliability_score = 20.0
        validator._last_score_calculation = 0.0  # Invalidate cache
        low_reliability_score = validator.calculate_pocs_score(current_time)
        print(f"Low reliability score (reliability=20.0): {low_reliability_score}")
        
        # High reliability should increase score
        assert high_reliability_score > baseline_score, "High reliability should increase score"
        assert low_reliability_score < baseline_score, "Low reliability should decrease score"
        assert high_reliability_score > low_reliability_score, "High reliability should be better than low"
    
    def test_contribution_score_effects(self):
        """Test contribution score effects on PoCS score"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        
        # Calculate baseline score (default contribution = 0.0)
        baseline_score = validator.calculate_pocs_score(current_time)
        print(f"Baseline score (contribution=0.0): {baseline_score}")
        
        # Add high contribution (this should invalidate cache automatically)
        validator.update_contribution_score(100.0, "major_contribution")
        high_contribution_score = validator.calculate_pocs_score(current_time)
        print(f"High contribution score (contribution=10.0): {high_contribution_score}")
        
        # Add more contribution (this should invalidate cache automatically)
        validator.update_contribution_score(200.0, "major_contribution")
        higher_contribution_score = validator.calculate_pocs_score(current_time)
        print(f"Higher contribution score (contribution=29.0): {higher_contribution_score}")
        
        # High contribution should increase score
        assert high_contribution_score > baseline_score, "High contribution should increase score"
        assert higher_contribution_score > high_contribution_score, "Higher contribution should increase score more"
    
    def test_diversity_bonus_effects(self):
        """Test diversity bonus effects on PoCS score"""
        addr = generate_address()
        self.lahka.add_transaction(Transaction("genesis", addr, 100.0, TransactionType.TRANSFER))
        self.lahka.mine_block()
        self.lahka.register_validator(addr, 50.0)
        self.lahka.mine_block()
        
        validator = self.lahka.validators[addr]
        current_time = time.time()
        
        # Calculate baseline score (default diversity = 0.0)
        baseline_score = validator.calculate_pocs_score(current_time)
        print(f"Baseline score (diversity=0.0): {baseline_score}")
        
        # Add diversity bonus and invalidate cache
        validator.diversity_bonus = 50.0
        validator._last_score_calculation = 0.0  # Invalidate cache
        diversity_score = validator.calculate_pocs_score(current_time)
        print(f"Diversity score (diversity=50.0): {diversity_score}")
        
        # Diversity should increase score
        assert diversity_score > baseline_score, "Diversity bonus should increase score"
        
        # Test with different diversity values
        validator.diversity_bonus = 100.0
        validator._last_score_calculation = 0.0  # Invalidate cache
        high_diversity_score = validator.calculate_pocs_score(current_time)
        print(f"High diversity score (diversity=100.0): {high_diversity_score}")
        
        assert high_diversity_score > diversity_score, "Higher diversity should increase score more" 