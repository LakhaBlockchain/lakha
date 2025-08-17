import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import shutil
import subprocess
import time
from core import LahkaBlockchain, Transaction, TransactionType, generate_address
import plyvel
import json

# 1. Multiple Blocks and Transactions
def test_multiple_blocks_and_transactions(tmp_path):
    db_path = str(tmp_path / "db")
    blockchain = LahkaBlockchain(db_path=db_path)
    alice = generate_address()
    bob = generate_address()
    carol = generate_address()
    # Fund Alice and Bob
    tx1 = Transaction('genesis', alice, 100, TransactionType.TRANSFER, gas_limit=1)
    tx2 = Transaction('genesis', bob, 100, TransactionType.TRANSFER, nonce=1, gas_limit=1)
    blockchain.add_transaction(tx1)
    blockchain.mine_block()
    blockchain.add_transaction(tx2)
    blockchain.mine_block()
    # Alice sends to Carol
    tx3 = Transaction(alice, carol, 50, TransactionType.TRANSFER, nonce=0, gas_limit=1)
    blockchain.add_transaction(tx3)
    blockchain.mine_block()
    blockchain.close()
    # Restart
    blockchain2 = LahkaBlockchain(db_path=db_path)
    # Check all blocks and txs
    assert len(blockchain2.chain) == 4  # genesis + 3
    tx_hashes = [tx.hash for b in blockchain2.chain[1:] for tx in b.transactions]
    assert tx1.hash in tx_hashes
    assert tx2.hash in tx_hashes
    assert tx3.hash in tx_hashes
    # Check balances
    assert blockchain2.get_balance(alice) == 49
    assert blockchain2.get_balance(bob) == 100
    assert blockchain2.get_balance(carol) == 50
    blockchain2.close()

# 2. Account and Validator State
def test_account_and_validator_state(tmp_path):
    db_path = str(tmp_path / "db")
    blockchain = LahkaBlockchain(db_path=db_path)
    alice = generate_address()
    # Fund Alice
    tx1 = Transaction('genesis', alice, 100, TransactionType.TRANSFER, gas_limit=1)
    blockchain.add_transaction(tx1)
    blockchain.mine_block()
    # Register Alice as validator (stake 20)
    tx2 = Transaction(alice, 'stake_pool', 20, TransactionType.STAKE, nonce=0, gas_limit=1)
    blockchain.add_transaction(tx2)
    blockchain.mine_block()
    blockchain.close()
    # Restart
    blockchain2 = LahkaBlockchain(db_path=db_path)
    # Check Alice's account
    acc = blockchain2.ledger.get_account(alice)
    assert acc is not None
    assert acc.balance < 100  # Should be 100 - 20 - gas
    # Check validator
    assert alice in blockchain2.validators
    val = blockchain2.validators[alice]
    assert val.stake == 20
    blockchain2.close()

# 3. Smart Contracts
def test_smart_contract_persistence(tmp_path):
    db_path = str(tmp_path / "db")
    blockchain = LahkaBlockchain(db_path=db_path)
    alice = generate_address()
    # Fund Alice
    tx1 = Transaction('genesis', alice, 100, TransactionType.TRANSFER, gas_limit=1)
    blockchain.add_transaction(tx1)
    blockchain.mine_block()
    # Deploy contract
    contract_code = 'dummy_code'
    tx2 = Transaction(
        alice, '', 0, TransactionType.CONTRACT_DEPLOY, nonce=0, gas_limit=1,
        data={'contract_code': contract_code, 'initial_state': {'x': 42}}
    )
    blockchain.add_transaction(tx2)
    blockchain.mine_block()
    # Get deployed address
    deployed_addr = tx2.data.get('deployed_address')
    assert deployed_addr is not None
    # Interact with contract
    tx3 = Transaction(
        alice, '', 0, TransactionType.CONTRACT_CALL, nonce=1, gas_limit=1,
        data={'contract_address': deployed_addr, 'function_name': 'set_state', 'args': ['y', 99]}
    )
    blockchain.add_transaction(tx3)
    blockchain.mine_block()
    blockchain.close()
    # Restart
    blockchain2 = LahkaBlockchain(db_path=db_path)
    # Check contract state
    state = blockchain2.get_contract_state(deployed_addr)
    assert state['x'] == 42
    assert state['y'] == 99
    blockchain2.close()

def test_partial_write_crash_recovery(tmp_path):
    db_path = str(tmp_path / "db")
    # Step 1: Write a block, then simulate a crash (os._exit)
    code = f'''
import sys
sys.path.insert(0, "{os.getcwd()}")
from core import LahkaBlockchain, Transaction, TransactionType, generate_address
blockchain = LahkaBlockchain(db_path=r"{db_path}")
alice = generate_address()
tx1 = Transaction('genesis', alice, 100, TransactionType.TRANSFER, gas_limit=1)
blockchain.add_transaction(tx1)
blockchain.mine_block()
import os
os._exit(1)
'''
    subprocess.run([sys.executable, '-c', code])
    # Step 2: Restart and check integrity
    blockchain2 = LahkaBlockchain(db_path=db_path)
    # Should have at least genesis and one block
    assert len(blockchain2.chain) >= 2
    # Alice's balance should be present
    alice_balance = None
    for acc in blockchain2.ledger.accounts.values():
        if acc.address != 'genesis':
            alice_balance = acc.balance
    assert alice_balance is not None


def test_manual_leveldb_inspection(tmp_path):
    db_path = str(tmp_path / "db")
    blockchain = LahkaBlockchain(db_path=db_path)
    alice = generate_address()
    tx1 = Transaction('genesis', alice, 100, TransactionType.TRANSFER, gas_limit=1)
    blockchain.add_transaction(tx1)
    blockchain.mine_block()
    blockchain.close()
    # Manual inspection: print all keys/values
    db = plyvel.DB(db_path, create_if_missing=False)
    print("[MANUAL INSPECTION] LevelDB contents:")
    for key, value in db:
        try:
            k = key.decode()
        except Exception:
            k = str(key)
        try:
            v = value.decode()
        except Exception:
            v = str(value)
        print(f"{k}: {v}")
    db.close()


def test_cross_instance_consistency(tmp_path):
    db_path = str(tmp_path / "db")
    blockchain = LahkaBlockchain(db_path=db_path)
    alice = generate_address()
    tx1 = Transaction('genesis', alice, 100, TransactionType.TRANSFER, gas_limit=1)
    blockchain.add_transaction(tx1)
    blockchain.mine_block()
    blockchain.close()  # Close before opening second instance
    # Open a second instance (read-only)
    blockchain2 = LahkaBlockchain(db_path=db_path)
    assert blockchain2.get_balance(alice) == 100
    assert blockchain2.chain[-1].transactions[0].to_address == alice
    blockchain2.close()


def test_edge_cases_empty_and_failed_blocks(tmp_path):
    db_path = str(tmp_path / "db")
    blockchain = LahkaBlockchain(db_path=db_path)
    # Mine an empty block (should not be added)
    result = blockchain.mine_block()
    assert result is False or len(blockchain.chain) == 1  # Only genesis
    # Add a failed transaction (insufficient funds)
    alice = generate_address()
    tx1 = Transaction(alice, 'genesis', 1000, TransactionType.TRANSFER, gas_limit=1)
    added = blockchain.add_transaction(tx1)
    assert not added  # Should be rejected
    # Fund Alice so contract call can be added
    tx_fund = Transaction('genesis', alice, 1, TransactionType.TRANSFER, gas_limit=1)
    blockchain.add_transaction(tx_fund)
    blockchain.mine_block()
    # Add a contract call with no contract (should fail on processing)
    tx2 = Transaction(alice, '', 0, TransactionType.CONTRACT_CALL, gas_limit=1, data={'contract_address': 'nonexistent', 'function_name': 'set_state', 'args': ['z', 1]})
    added2 = blockchain.add_transaction(tx2)
    assert added2  # It can be added, but will fail on processing
    # Try to mine block with only failed tx
    mined = blockchain.mine_block()
    # Block may be added, but tx will not change state
    blockchain.close() 