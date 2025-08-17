import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import random
from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address

# Generate Bech32 addresses for all test validators
validator_addresses = [generate_address() for _ in range(20)]
user_addresses = [generate_address() for _ in range(10)]

def test_optimized_validator_selection():
    """Test optimized validator selection performance"""
    lahka = LahkaBlockchain()
    # Generate addresses for this test
    addresses = [generate_address() for _ in range(5)]
    # Fund all
    for address, stake in zip(addresses, [50.0, 75.0, 100.0, 25.0, 60.0]):
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", address, stake + 10, TransactionType.TRANSFER, nonce=nonce))
        lahka.mine_block()
    lahka.mine_block()
    # Register validators with different stakes
    for address, stake in zip(addresses, [50.0, 75.0, 100.0, 25.0, 60.0]):
        lahka.register_validator(address, stake)
    lahka.mine_block()
    for address in addresses:
        assert address in lahka.validators
    
    # Test optimized selection
    selected = lahka.optimize_validator_selection()
    assert selected is not None
    assert selected in lahka.validators
    
    # Test multiple selections
    selections = []
    for _ in range(10):
        selected = lahka.optimize_validator_selection()
        selections.append(selected)
    
    # Should have some variety in selection
    assert len(set(selections)) > 1

def test_network_conditions_adjustment():
    """Test network condition adjustments"""
    lahka = LahkaBlockchain()
    alice = generate_address()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    alice_val = lahka.validators[alice]
    
    # Test high load condition
    lahka.update_network_conditions("high_load")
    assert hasattr(alice_val, 'dynamic_weight_adjustment')
    assert alice_val.dynamic_weight_adjustment > 1.0
    
    # Test low load condition
    lahka.update_network_conditions("low_load")
    assert alice_val.dynamic_weight_adjustment < 1.0
    
    # Test normal condition
    lahka.update_network_conditions("normal")
    assert alice_val.dynamic_weight_adjustment == 1.0

def test_collaboration_scoring():
    """Test cross-validator collaboration scoring"""
    lahka = LahkaBlockchain()
    alice = generate_address()
    bob = generate_address()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", bob, 100, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.mine_block()
    alice_val = lahka.validators[alice]
    bob_val = lahka.validators[bob]
    
    # Record collaboration activities
    lahka.record_collaboration(alice, "code_review", 10.0)
    lahka.record_collaboration(alice, "mentoring", 5.0)
    lahka.record_collaboration(bob, "security_audit", 15.0)
    
    assert hasattr(alice_val, 'collaboration_score')
    assert hasattr(bob_val, 'collaboration_score')
    assert alice_val.collaboration_score > 0
    assert bob_val.collaboration_score > 0

def test_network_health_contribution():
    """Test network health contribution tracking"""
    lahka = LahkaBlockchain()
    alice = generate_address()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    alice_val = lahka.validators[alice]
    
    # Record network health contributions
    lahka.record_network_health_contribution(alice, "latency_optimization", 8.0)
    lahka.record_network_health_contribution(alice, "bandwidth_improvement", 12.0)
    
    assert hasattr(alice_val, 'network_health_contribution')
    assert alice_val.network_health_contribution > 0

def test_performance_metrics():
    """Test comprehensive performance metrics"""
    lahka = LahkaBlockchain()
    alice = generate_address()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    alice_val = lahka.validators[alice]
    
    # Add some activities
    alice_val.earn_contribution_credits("code_audit", 20.0, "Test audit")
    alice_val.apply_penalty("test", 5.0, "Test penalty")
    
    # Get performance metrics
    metrics = alice_val.get_performance_metrics()
    
    assert 'pocs_score' in metrics
    assert 'stake' in metrics
    assert 'reputation' in metrics
    assert 'reliability' in metrics
    assert 'contribution_score' in metrics
    assert 'collaboration_score' in metrics
    assert 'network_health' in metrics
    assert 'penalty_multiplier' in metrics
    assert 'rehabilitation_progress' in metrics
    assert 'contribution_credits' in metrics
    assert 'blocks_success_rate' in metrics
    assert 'uptime_percentage' in metrics
    assert 'response_time_avg' in metrics
    assert 'total_activities' in metrics
    assert 'total_penalties' in metrics
    assert 'dynamic_weight' in metrics

def test_network_performance_summary():
    """Test network performance summary"""
    lahka = LahkaBlockchain()
    
    # Setup multiple validators
    stakes = [50.0, 75.0, 100.0]
    for i in range(3):
        address = validator_addresses[i]
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", address, stakes[i] + 10, TransactionType.TRANSFER, nonce=nonce))
        lahka.mine_block()
    # Fund additional addresses that will be registered
    for idx, stake in zip([5, 6, 7], [50.0, 75.0, 100.0]):
        address = validator_addresses[idx]
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", address, stake + 10, TransactionType.TRANSFER, nonce=nonce))
        lahka.mine_block()
    
    lahka.mine_block()
    
    # Register validators and verify they exist
    assert lahka.register_validator(validator_addresses[5], 50.0)
    assert lahka.register_validator(validator_addresses[6], 75.0)
    assert lahka.register_validator(validator_addresses[7], 100.0)
    
    # Verify validators are registered
    assert validator_addresses[5] in lahka.validators
    assert validator_addresses[6] in lahka.validators
    assert validator_addresses[7] in lahka.validators
    
    # Add some activities and penalties
    lahka.validators[validator_addresses[5]].earn_contribution_credits("code_audit", 10.0, "Test")
    lahka.validators[validator_addresses[6]].apply_penalty("test", 5.0, "Test penalty")
    lahka.record_collaboration(validator_addresses[7], "mentoring", 8.0)
    
    # Get network summary
    summary = lahka.get_network_performance_summary()
    
    assert summary['total_validators'] == 3
    assert summary['active_validators'] == 3
    assert summary['total_stake'] == 225.0
    assert 'average_metrics' in summary
    assert summary['total_penalties'] > 0
    assert summary['total_activities'] > 0
    assert 'network_health_score' in summary
    assert 'collaboration_score' in summary

def test_integration_scenario():
    """Test complete PoCS integration scenario"""
    lahka = LahkaBlockchain()
    
    # Setup network with multiple validators
    validator_stakes = {validator_addresses[8]: 50.0, validator_addresses[9]: 100.0, validator_addresses[10]: 75.0, validator_addresses[11]: 60.0, validator_addresses[12]: 80.0}
    for validator, stake in validator_stakes.items():
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", validator, stake + 10, TransactionType.TRANSFER, nonce=nonce))
        lahka.mine_block()
    
    lahka.mine_block()
    
    # Register validators with different characteristics
    assert lahka.register_validator(validator_addresses[8], 50.0)   # Low stake, high contributor
    assert lahka.register_validator(validator_addresses[9], 100.0)    # High stake, reliable
    assert lahka.register_validator(validator_addresses[10], 75.0) # Medium stake, penalized
    assert lahka.register_validator(validator_addresses[11], 60.0)   # Medium stake, collaborator
    assert lahka.register_validator(validator_addresses[12], 80.0)     # High stake, network health contributor
    
    # Verify all validators are registered
    for validator in validator_stakes:
        assert validator in lahka.validators
    
    # Simulate various activities
    # Alice: Contribution mining pathway
    lahka.validators[validator_addresses[8]].earn_contribution_credits("code_audit", 30.0, "Major audit")
    lahka.validators[validator_addresses[8]].earn_contribution_credits("documentation", 20.0, "API docs")
    
    # Bob: High reliability
    lahka.validators[validator_addresses[9]].update_reliability_score(True, 0.5)
    lahka.validators[validator_addresses[9]].update_reliability_score(True, 0.3)
    
    # Charlie: Gets penalized, then rehabilitates
    lahka.validators[validator_addresses[10]].apply_penalty("malicious_behavior", 15.0, "First offense")
    lahka.validators[validator_addresses[10]].earn_contribution_credits("bug_report", 25.0, "Found critical bug")
    
    # Diana: Collaboration activities
    lahka.record_collaboration(validator_addresses[11], "code_review", 12.0)
    lahka.record_collaboration(validator_addresses[11], "mentoring", 8.0)
    
    # Eve: Network health contributions
    lahka.record_network_health_contribution(validator_addresses[12], "latency_optimization", 15.0)
    lahka.record_network_health_contribution(validator_addresses[12], "security_audit", 20.0)
    
    # Test network conditions
    lahka.update_network_conditions("high_load")
    
    # Mine several blocks to test selection
    for _ in range(5):
        lahka.add_transaction(Transaction("genesis", f"user_{random.randint(1, 100)}", 1, TransactionType.TRANSFER))
        lahka.mine_block()
    
    # Get final network summary
    summary = lahka.get_network_performance_summary()
    
    # Verify all validators are active
    assert summary['active_validators'] == 5
    assert summary['total_validators'] == 5
    
    # Verify activities and penalties are recorded
    assert summary['total_activities'] > 0
    assert summary['total_penalties'] > 0
    
    # Verify collaboration and network health scores
    assert summary['collaboration_score'] > 0
    assert summary['network_health_score'] > 0

def test_performance_benchmark():
    """Test performance with many validators"""
    lahka = LahkaBlockchain()
    # Setup 20 validators: fund all, then mine
    for i, address in enumerate(validator_addresses):
        stake = 50.0 + (i * 5.0)
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", address, stake + 10, TransactionType.TRANSFER, nonce=nonce))
        lahka.mine_block()
    lahka.mine_block()
    # Register all validators
    for i, address in enumerate(validator_addresses):
        stake = 50.0 + (i * 5.0)
        assert lahka.register_validator(address, stake)
    lahka.mine_block()
    for address in validator_addresses:
        assert address in lahka.validators
    # Add some random activities
    for i, address in enumerate(validator_addresses):
        validator = lahka.validators[address]
        validator.update_contribution_score(i * 2.0)
        validator.update_reliability_score(True, 1.0)
    
    # Test selection performance
    start_time = time.time()
    for _ in range(100):
        selected = lahka.optimize_validator_selection()
        assert selected is not None
    end_time = time.time()
    
    # Should complete 100 selections in reasonable time (< 1 second)
    assert (end_time - start_time) < 1.0
    
    # Test network summary performance
    start_time = time.time()
    summary = lahka.get_network_performance_summary()
    end_time = time.time()
    
    # Should complete summary in reasonable time (< 0.1 second)
    assert (end_time - start_time) < 0.1
    
    # Verify summary data
    assert summary['total_validators'] == 20
    assert summary['active_validators'] == 20
    assert summary['total_stake'] > 0 