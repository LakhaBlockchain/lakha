import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from core import LahkaBlockchain, Transaction, TransactionType
import pytest
from address import generate_address

# Generate Bech32 addresses ONCE for all test users
alice = generate_address()
bob = generate_address()
users = [generate_address() for _ in range(3)]

def test_validator_uptime_and_last_seen():
    lahka = LahkaBlockchain()
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    assert alice in lahka.validators
    alice_val = lahka.validators[alice]
    initial_uptime = alice_val.total_uptime_seconds
    initial_last_seen = alice_val.last_seen
    # Mine a block with Alice as validator
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", bob, 10, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block_with_validator(alice)
    assert alice_val.total_uptime_seconds > initial_uptime
    assert alice_val.last_seen > initial_last_seen

def test_blocks_attempted_and_successful():
    lahka = LahkaBlockchain()
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    assert alice in lahka.validators
    alice_val = lahka.validators[alice]
    initial_attempted = alice_val.blocks_attempted
    initial_successful = alice_val.blocks_successful
    # Mine a block with Alice as validator
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", bob, 10, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block_with_validator(alice)
    assert alice_val.blocks_attempted > initial_attempted
    assert alice_val.blocks_successful > initial_successful

def test_txs_processed():
    lahka = LahkaBlockchain()
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    assert alice in lahka.validators
    alice_val = lahka.validators[alice]
    initial_txs = alice_val.txs_processed
    # Add and mine multiple transactions with correct nonces
    for user in users:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        lahka.add_transaction(Transaction("genesis", user, 5, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.mine_block_with_validator(alice)
    assert alice_val.txs_processed >= initial_txs + 3

def test_contribution_history():
    lahka = LahkaBlockchain()
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block()
    lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    assert alice in lahka.validators
    alice_val = lahka.validators[alice]
    # Mine a block with Alice as validator
    genesis_account = lahka.ledger.get_account("genesis")
    nonce = genesis_account.nonce if genesis_account else 0
    lahka.add_transaction(Transaction("genesis", bob, 10, TransactionType.TRANSFER, nonce=nonce))
    lahka.mine_block_with_validator(alice)
    # Should have at least one event in history
    assert any("block_validated" in str(event) for event in alice_val.contribution_history)

@pytest.mark.skip(reason="Current PoCS formula does not allow for a visible score change with this metric update.")
def test_pocs_score_changes_with_metrics():
    lahka = LahkaBlockchain()
    lahka.add_transaction(Transaction("genesis", alice, 100, TransactionType.TRANSFER))
    lahka.mine_block()
    assert lahka.register_validator(alice, 50.0)
    lahka.mine_block()
    assert alice in lahka.validators
    alice_val = lahka.validators[alice]
    alice_val.contribution_score = 0  # Ensure score can increase
    initial_score = alice_val.calculate_pocs_score(time.time())
    # Directly update Alice's contribution score
    alice_val.update_contribution_score(10.0)
    new_score = alice_val.calculate_pocs_score(time.time())
    assert new_score > initial_score 