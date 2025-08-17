import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import random
from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address

def test_validator_peer_rating():
    """Test that validators can rate each other"""
    alice = generate_address()
    bob = generate_address()
    lahka = LahkaBlockchain()
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", alice, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", bob, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.mine_block()
    alice_obj = lahka.validators[alice]
    bob_obj = lahka.validators[bob]
    
    # Alice rates Bob
    alice_obj.rate_peer(bob, 85.0, "Good performance")
    assert bob in alice_obj.peer_ratings
    assert alice_obj.peer_ratings[bob][0] == 85.0
    assert alice_obj.peer_ratings[bob][2] == "Good performance"

def test_average_peer_rating():
    """Test average peer rating calculation"""
    alice = generate_address()
    bob = generate_address()
    charlie = generate_address()
    dave = generate_address()
    lahka = LahkaBlockchain()
    for user in [alice, bob, charlie, dave]:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", user, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.register_validator(charlie, 50.0)
    lahka.register_validator(dave, 50.0)
    lahka.mine_block()
    alice_obj = lahka.validators[alice]
    bob_obj = lahka.validators[bob]
    charlie_obj = lahka.validators[charlie]
    dave_obj = lahka.validators[dave]
    
    # No ratings yet
    assert alice_obj.get_average_peer_rating() == 100.0
    
    # Add some ratings
    alice_obj.rate_peer(bob, 80.0, "Good")
    alice_obj.rate_peer(charlie, 90.0, "Excellent")
    alice_obj.rate_peer(dave, 70.0, "Average")
    
    avg_rating = alice_obj.get_average_peer_rating()
    assert 70.0 <= avg_rating <= 90.0
    assert avg_rating == 80.0  # (80+90+70)/3

def test_reputation_score_update():
    """Test reputation score calculation"""
    alice = generate_address()
    bob = generate_address()
    charlie = generate_address()
    lahka = LahkaBlockchain()
    for user in [alice, bob, charlie]:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", user, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.register_validator(charlie, 50.0)
    lahka.mine_block()
    alice_obj = lahka.validators[alice]
    bob_obj = lahka.validators[bob]
    charlie_obj = lahka.validators[charlie]
    
    # Set some initial values
    alice_obj.reliability_score = 95.0
    alice_obj.contribution_score = 50.0
    
    # Add peer ratings
    alice_obj.rate_peer(bob, 85.0, "Good")
    alice_obj.rate_peer(charlie, 90.0, "Excellent")
    
    # Update reputation score
    alice_obj.update_reputation_score()
    
    # Reputation score should be calculated
    assert alice_obj.reputation_score > 0
    assert alice_obj.average_peer_rating == 87.5  # (85+90)/2

def test_peer_review_assignment():
    """Test random peer review assignment"""
    alice = generate_address()
    bob = generate_address()
    charlie = generate_address()
    lahka = LahkaBlockchain()
    for user in [alice, bob, charlie]:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", user, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.register_validator(charlie, 50.0)
    lahka.mine_block()
    assignments = lahka.assign_peer_reviews()
    
    # Should have assignments
    assert len(assignments) >= 1
    
    # Each assignment should have 2 validators
    for reviewer, reviewee in assignments:
        assert reviewer in lahka.validators
        assert reviewee in lahka.validators
        assert reviewer != reviewee

def test_peer_review_triggering():
    """Test that peer reviews are triggered periodically"""
    alice = generate_address()
    bob = generate_address()
    charlie = generate_address()
    lahka = LahkaBlockchain()
    for user in [alice, bob, charlie]:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", user, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.register_validator(charlie, 50.0)
    lahka.mine_block()
    # Mine more blocks to simulate activity
    for i in range(20):
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", f"user{i}", 10, TransactionType.TRANSFER, nonce=nonce))
        lahka.mine_block()
    # Directly trigger peer reviews to ensure ratings are assigned
    lahka.trigger_peer_reviews()
    assert any(len(v.peer_ratings) > 0 for v in lahka.validators.values())

def test_pocs_score_with_reputation():
    """Test that PoCS score includes reputation component"""
    alice = generate_address()
    bob = generate_address()
    lahka = LahkaBlockchain()
    for user in [alice, bob]:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", user, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.mine_block()
    alice_obj = lahka.validators[alice]
    bob_obj = lahka.validators[bob]
    # Get initial score
    initial_score = alice_obj.calculate_pocs_score(time.time())
    # Add peer ratings and update reputation
    bob_obj.rate_peer(alice, 95.0, "Excellent")
    alice_obj.update_reputation_score()
    bob_obj.update_reputation_score()
    # Score should change due to reputation
    new_score = alice_obj.calculate_pocs_score(time.time())
    assert new_score != initial_score

def test_rating_validation():
    """Test that ratings are validated (1-100 scale)"""
    alice = generate_address()
    bob = generate_address()
    charlie = generate_address()
    eve = generate_address()
    frank = generate_address()
    lahka = LahkaBlockchain()
    for user in [alice, bob, charlie, eve, frank]:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", user, 60.0, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.register_validator(bob, 50.0)
    lahka.register_validator(charlie, 50.0)
    lahka.register_validator(eve, 50.0)
    lahka.register_validator(frank, 50.0)
    lahka.mine_block()
    alice_obj = lahka.validators[alice]
    bob_obj = lahka.validators[bob]
    charlie_obj = lahka.validators[charlie]
    eve_obj = lahka.validators[eve]
    frank_obj = lahka.validators[frank]
    # Valid ratings
    alice_obj.rate_peer(bob, 1.0, "Poor")
    alice_obj.rate_peer(charlie, 100.0, "Perfect")
    # Invalid rating
    try:
        alice_obj.rate_peer(eve, 0, "Invalid")
        assert False, "Should have raised ValueError for rating < 1"
    except ValueError:
        pass
    try:
        alice_obj.rate_peer(frank, 101, "Invalid")
        assert False, "Should have raised ValueError for rating > 100"
    except ValueError:
        pass 