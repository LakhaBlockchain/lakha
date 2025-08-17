import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address

# Generate Bech32 addresses ONCE for all test users
alice = generate_address()
bob = generate_address()
charlie = generate_address()
teacher = generate_address()
addresses = [alice, bob, charlie, teacher]

def test_blockchain_basic():
    """Test basic blockchain functionality: transfers, validator registration, and contract deployment"""
    # Create Lahka blockchain
    lahka = LahkaBlockchain()
    
    # Give initial tokens
    for address in addresses:
        genesis_account = lahka.ledger.get_account("genesis")
        nonce = genesis_account.nonce if genesis_account else 0
        transfer_tx = Transaction(
            from_address="genesis",
            to_address=address,
            amount=100.0,
            transaction_type=TransactionType.TRANSFER,
            nonce=nonce
        )
        lahka.add_transaction(transfer_tx)
        lahka.mine_block()  # Mine after each transfer to increment nonce
    assert lahka.get_balance(alice) == 100.0
    assert lahka.get_balance(bob) == 100.0
    assert lahka.get_balance(teacher) == 100.0
    
    # Mine first block with genesis validator
    success = lahka.mine_block()
    assert success, "Block 1 should be mined by genesis validator"
    assert lahka.get_balance(alice) == 100.0
    assert lahka.get_balance(bob) == 100.0
    assert lahka.get_balance(teacher) == 100.0
    
    # Register validators
    assert lahka.register_validator(alice, 20.0), "Alice validator registration should succeed"
    assert lahka.register_validator(bob, 15.0), "Bob validator registration should succeed"
    assert lahka.register_validator(teacher, 30.0), "Teacher validator registration should succeed"
    
    # Mine block to process validator registrations
    success = lahka.mine_block()
    assert success, "Block 2 should be mined by a validator"
    assert len(lahka.validators) == 3
    
    # Deploy a simple contract
    contract_code = """
    class SimpleContract:
        def __init__(self):
            self.counter = 0
        
        def increment(self):
            self.counter += 1
            return self.counter
        
        def get_counter(self):
            return self.counter
    """
    
    deploy_tx = Transaction(
        from_address=alice,
        to_address="",
        transaction_type=TransactionType.CONTRACT_DEPLOY,
        data={
            'contract_code': contract_code,
            'initial_state': {'counter': 0}
        },
        gas_limit=50  # Low gas limit for contract deployment
    )
    lahka.add_transaction(deploy_tx)
    
    # Mine block to deploy contract
    success = lahka.mine_block()
    assert success, "Block 3 should be mined for contract deployment"
    assert len(lahka.contract_engine.contracts) == 1
    
    # Verify final state
    assert len(lahka.chain) == 4  # Genesis + 3 mined blocks
    assert len(lahka.validators) == 3
    assert len(lahka.contract_engine.contracts) == 1
    assert len(lahka.pending_transactions) == 0 