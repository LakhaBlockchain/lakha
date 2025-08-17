import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import Ledger, Account, LedgerEntry
from address import generate_address

# Generate Bech32 addresses ONCE for all test users
alice = generate_address()
bob = generate_address()
charlie = generate_address()
dave = generate_address()

def test_ledger_basic():
    """Test basic ledger functionality"""
    ledger = Ledger()
    
    # Test account creation
    account = ledger.create_account(alice, 100.0)
    assert account.address == alice
    assert account.balance == 100.0
    
    # Test balance retrieval
    balance = ledger.get_balance(alice)
    assert balance == 100.0
    
    # Test non-existent account
    balance = ledger.get_balance(bob)
    assert balance == 0.0
    
    # Test transaction recording
    ledger.record_transaction(
        transaction_hash="tx123",
        block_number=1,
        from_address=alice,
        to_address=bob,
        amount=50.0,
        transaction_type="transfer",
        description="Test transfer",
        gas_cost=1.0
    )
    
    # Check balances after transaction
    assert ledger.get_balance(alice) == 49.0  # 100 - 50 - 1 (gas)
    assert ledger.get_balance(bob) == 50.0
    
    # Test account history
    history = ledger.get_account_history(alice)
    assert len(history) == 2  # Debit and gas cost entries
    
    # Test total supply
    total_supply = ledger.get_total_supply()
    assert total_supply == 99.0  # 49 + 50
    
    print("✅ Ledger basic functionality test passed!")

def test_ledger_account_management():
    """Test account management features"""
    ledger = Ledger()
    
    # Test get_or_create_account
    account = ledger.get_or_create_account(charlie)
    assert account.address == charlie
    assert account.balance == 0.0
    
    # Test account summary
    ledger.create_account(dave, 200.0)
    summary = ledger.get_accounts_summary()
    assert charlie in summary
    assert dave in summary
    assert summary[dave]["balance"] == 200.0
    
    print("✅ Ledger account management test passed!")

if __name__ == "__main__":
    test_ledger_basic()
    test_ledger_account_management()
    print("\n🎉 All ledger tests passed!") 