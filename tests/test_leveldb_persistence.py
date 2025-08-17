import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import shutil
from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address

def test_leveldb_persistence():
    # Use a test-specific DB path
    db_path = 'test_lakha_db'
    # Clean up any previous test DB
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    # 1. Create blockchain, add a block, close
    blockchain = LahkaBlockchain(db_path=db_path)
    alice = generate_address()
    bob = generate_address()
    tx = Transaction('genesis', alice, 100, TransactionType.TRANSFER)
    blockchain.add_transaction(tx)
    blockchain.mine_block()
    print(f"[DEBUG] After mining: chain length = {len(blockchain.chain)}")
    for b in blockchain.chain:
        print(f"[DEBUG] Block index: {b.index}, tx count: {len(b.transactions)}")
    blockchain.close()

    # 2. Simulate restart: new instance, same DB path
    blockchain2 = LahkaBlockchain(db_path=db_path)
    blockchain2._load_chain_from_db()
    print(f"[DEBUG] After restart: chain length = {len(blockchain2.chain)}")
    for b in blockchain2.chain:
        print(f"[DEBUG] Block index: {b.index}, tx count: {len(b.transactions)}")

    # 3. Check that the block and account are present
    assert len(blockchain2.chain) > 1  # Genesis + 1
    block1 = blockchain2.storage.get_block(1)
    assert block1 is not None, "Block 1 should be present in LevelDB"
    found = any(tx['to_address'] == alice for tx in block1['transactions'])
    assert found, "Alice's transaction should be in block 1"
    account = blockchain2.storage.get_account(alice)
    assert account is not None
    assert account['balance'] == 100.0

    # Clean up test DB
    blockchain2.close()
    shutil.rmtree(db_path) 