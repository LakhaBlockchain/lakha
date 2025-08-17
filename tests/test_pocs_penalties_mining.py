import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address

def test_penalty_application():
    """Test that penalties are applied correctly with escalating multipliers"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    alice_val = lahka.validators[alice]
    
    # Apply first penalty
    alice_val.apply_penalty("malicious_behavior", 10.0, "First offense")
    assert len(alice_val.penalty_history) == 1
    assert alice_val.current_penalty_multiplier > 1.0
    
    # Apply second penalty (should have higher multiplier)
    initial_multiplier = alice_val.current_penalty_multiplier
    alice_val.apply_penalty("malicious_behavior", 10.0, "Second offense")
    assert alice_val.current_penalty_multiplier > initial_multiplier

def test_penalty_multiplier_calculation():
    """Test escalating penalty multiplier calculation"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    alice_val = lahka.validators[alice]
    
    # No penalties yet
    assert alice_val.calculate_penalty_multiplier() == 1.0
    
    # Add penalties
    alice_val.apply_penalty("test", 5.0, "Test penalty")
    assert alice_val.calculate_penalty_multiplier() > 1.0
    
    alice_val.apply_penalty("test", 5.0, "Test penalty 2")
    assert alice_val.calculate_penalty_multiplier() > 1.5

def test_rehabilitation_progress():
    """Test rehabilitation progress through positive contributions"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    alice_val = lahka.validators[alice]
    
    # Apply penalty
    alice_val.apply_penalty("test", 10.0, "Test penalty")
    initial_multiplier = alice_val.current_penalty_multiplier
    
    # Make positive contributions
    alice_val.update_rehabilitation_progress(50.0)
    assert alice_val.rehabilitation_progress == 50.0
    
    # Complete rehabilitation
    alice_val.update_rehabilitation_progress(50.0)
    assert alice_val.rehabilitation_progress == 0.0  # Reset
    assert alice_val.current_penalty_multiplier < initial_multiplier

def test_contribution_credits():
    """Test earning and using contribution credits"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    alice_val = lahka.validators[alice]
    
    # Earn credits
    alice_val.earn_contribution_credits("code_audit", 20.0, "Audited smart contract")
    assert alice_val.contribution_credits == 20.0
    assert len(alice_val.contribution_activities) == 1
    
    # Earn more credits
    alice_val.earn_contribution_credits("documentation", 10.0, "Wrote docs")
    assert alice_val.contribution_credits == 30.0
    
    # Convert credits to stake
    initial_stake = alice_val.stake
    stake_earned = alice_val.convert_credits_to_stake(20.0)
    assert stake_earned == 2.0  # 20 credits * 0.1
    assert alice_val.stake == initial_stake + 2.0
    assert alice_val.contribution_credits == 10.0

def test_contribution_summary():
    """Test contribution summary generation"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    alice_val = lahka.validators[alice]
    
    # Add some activities
    alice_val.earn_contribution_credits("code_audit", 20.0, "Audit 1")
    alice_val.earn_contribution_credits("documentation", 10.0, "Docs 1")
    alice_val.earn_contribution_credits("code_audit", 15.0, "Audit 2")
    
    summary = alice_val.get_contribution_summary()
    assert summary['total_credits_earned'] == 45.0
    assert summary['current_credits'] == 45.0
    assert 'code_audit' in summary['activity_types']
    assert 'documentation' in summary['activity_types']

def test_community_governance_override():
    """Test community governance penalty override"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    alice_val = lahka.validators[alice]
    
    # Apply penalty
    alice_val.apply_penalty("test", 10.0, "Test penalty")
    initial_multiplier = alice_val.current_penalty_multiplier
    
    # Community override
    lahka.community_override_penalty(alice, 1.0, "Community decided to forgive")
    assert alice_val.current_penalty_multiplier == 1.0
    
    # Should be logged in penalty history
    assert any("community_override" in str(penalty) for penalty in alice_val.penalty_history)

def test_contribution_mining_activities():
    """Test available contribution mining activities"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    activities = lahka.get_contribution_mining_activities()
    
    assert 'code_audit' in activities
    assert 'documentation' in activities
    assert 'community_support' in activities
    assert 'bug_report' in activities
    assert 'educational_content' in activities
    
    # Check activity details
    code_audit = activities['code_audit']
    assert code_audit['credits_per_hour'] == 10.0
    assert code_audit['max_credits'] == 100.0

def test_penalty_impact_on_scores():
    """Test that penalties affect PoCS scores"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    alice_val = lahka.validators[alice]
    
    # Get initial score
    initial_score = alice_val.calculate_pocs_score(time.time())
    
    # Apply penalty
    alice_val.apply_penalty("malicious_behavior", 20.0, "Serious offense")
    
    # Score should be lower
    new_score = alice_val.calculate_pocs_score(time.time())
    assert new_score < initial_score

def test_contribution_mining_pathway():
    """Test complete contribution mining pathway"""
    alice = generate_address()
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    alice_val = lahka.validators[alice]
    
    # Start with no stake (new participant)
    alice_val.stake = 0.0
    
    # Earn credits through various activities
    alice_val.earn_contribution_credits("code_audit", 50.0, "Major audit")
    alice_val.earn_contribution_credits("bug_report", 40.0, "Found critical bug")
    alice_val.earn_contribution_credits("documentation", 30.0, "Wrote comprehensive docs")
    
    # Convert all credits to stake
    stake_earned = alice_val.convert_credits_to_stake(120.0)
    assert stake_earned == 12.0  # 120 credits * 0.1
    assert alice_val.stake == 12.0
    
    # Now they can participate in validation
    assert alice_val.calculate_pocs_score(time.time()) > 0 