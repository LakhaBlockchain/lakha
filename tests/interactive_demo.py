import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import LahkaBlockchain, Transaction, TransactionType
from address import generate_address
import json

# Generate Bech32 addresses ONCE for all demo users
alice = generate_address()
bob = generate_address()
charlie = generate_address()
teacher = generate_address()
addresses = [alice, bob, charlie, teacher]

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_blockchain_state(lahka, title="Current Blockchain State"):
    print_separator(title)
    print(f"📊 Chain Length: {len(lahka.chain)} blocks")
    print(f"⏳ Pending Transactions: {len(lahka.pending_transactions)}")
    print(f"👥 Validators: {len(lahka.validators)}")
    print(f"📄 Smart Contracts: {len(lahka.contract_engine.contracts)}")
    print(f"💰 Total Supply: {lahka.ledger.get_total_supply():.2f} LAHKA")

def print_balances(lahka, title="Account Balances"):
    print_separator(title)
    accounts = lahka.ledger.get_accounts_summary()
    for address, info in accounts.items():
        print(f"🏦 {address}: {info['balance']:.2f} LAHKA (tx: {info['transaction_count']})")

def print_validators(lahka, title="Validators"):
    print_separator(title)
    for address, validator in lahka.validators.items():
        print(f"👤 {address}:")
        print(f"   💰 Staked: {validator.stake:.2f} LAHKA")
        print(f"   🏆 Blocks Validated: {validator.blocks_validated}")
        print(f"   💎 Total Rewards: {validator.total_rewards:.2f} LAHKA")
        print(f"   ⭐ Reputation: {validator.reputation:.1f}")

def print_contracts(lahka, title="Smart Contracts"):
    print_separator(title)
    for address, contract in lahka.contract_engine.contracts.items():
        print(f"📄 Contract {address[:10]}...:")
        print(f"   👤 Owner: {contract.owner}")
        print(f"   📊 Status: {contract.status.value}")
        print(f"   📅 Created: {contract.created_at}")
        print(f"   💾 State: {json.dumps(contract.data, indent=2)}")

def print_recent_blocks(lahka, title="Recent Blocks", count=5):
    print_separator(title)
    for block in lahka.chain[-count:]:
        print(f"🔗 Block #{block.index}:")
        print(f"   ⏰ Timestamp: {block.timestamp}")
        print(f"   👤 Validator: {block.validator}")
        print(f"   📝 Transactions: {len(block.transactions)}")
        print(f"   🔗 Previous Hash: {block.previous_hash[:10]}...")
        print(f"   🆔 Hash: {block.hash[:10]}...")

def print_transaction_details(tx, title="Transaction Details"):
    print_separator(title)
    print(f"🆔 Hash: {tx.hash}")
    print(f"👤 From: {tx.from_address}")
    print(f"👥 To: {tx.to_address}")
    print(f"💰 Amount: {tx.amount:.2f} LAHKA")
    print(f"📋 Type: {tx.transaction_type.value}")
    print(f"⛽ Gas Limit: {tx.gas_limit}")
    print(f"⛽ Gas Price: {tx.gas_price}")
    print(f"⏰ Timestamp: {tx.timestamp}")
    if tx.data:
        print(f"📄 Data: {json.dumps(tx.data, indent=2)}")

def interactive_demo():
    print("🚀 LAHKA BLOCKCHAIN INTERACTIVE DEMO")
    print("=" * 60)
    
    # Create blockchain
    print("\n📦 Creating new LAHKA blockchain...")
    lahka = LahkaBlockchain()
    print_blockchain_state(lahka, "Initial State")
    
    # Show genesis block
    print_recent_blocks(lahka, "Genesis Block", 1)
    
    print(f"\n👥 Creating test addresses: {', '.join(addresses)}")
    
    # Add transfer transactions
    print("\n📤 Adding transfer transactions...")
    for i, address in enumerate(addresses):
        transfer_tx = Transaction(
            from_address="genesis",
            to_address=address,
            amount=100.0,
            transaction_type=TransactionType.TRANSFER
        )
        lahka.add_transaction(transfer_tx)
        print(f"   ✅ Added transfer: genesis → {address} (100 LAHKA)")
    
    print_blockchain_state(lahka, "After Adding Transfers")
    
    # Mine first block
    print("\n⛏️ Mining first block (genesis validator)...")
    success = lahka.mine_block()
    print(f"   {'✅' if success else '❌'} Block mined: {success}")
    
    print_blockchain_state(lahka, "After First Block")
    print_balances(lahka, "Balances After First Block")
    print_recent_blocks(lahka, "Blockchain After First Block", 2)
    
    # Register validators
    print("\n👥 Registering validators...")
    validator_stakes = {
        alice: 20.0,
        bob: 15.0,
        teacher: 30.0
    }
    
    for address, stake in validator_stakes.items():
        success = lahka.register_validator(address, stake)
        print(f"   {'✅' if success else '❌'} {address}: {stake} LAHKA staked")
    
    print_blockchain_state(lahka, "After Validator Registration")
    
    # Mine second block
    print("\n⛏️ Mining second block (PoS validators)...")
    success = lahka.mine_block()
    print(f"   {'✅' if success else '❌'} Block mined: {success}")
    
    print_blockchain_state(lahka, "After Second Block")
    print_balances(lahka, "Balances After Second Block")
    print_validators(lahka, "Validator Status")
    
    # Deploy smart contract
    print("\n📄 Deploying smart contract...")
    contract_code = """
    class SchoolRecords:
        def __init__(self):
            self.students = {}
            self.grades = {}
        
        def add_student(self, student_id, name):
            self.students[student_id] = name
            return True
        
        def add_grade(self, student_id, subject, grade):
            if student_id not in self.grades:
                self.grades[student_id] = {}
            self.grades[student_id][subject] = grade
            return True
        
        def get_student_info(self, student_id):
            return {
                'name': self.students.get(student_id, 'Unknown'),
                'grades': self.grades.get(student_id, {})
            }
    """
    
    deploy_tx = Transaction(
        from_address=alice,
        to_address="",
        transaction_type=TransactionType.CONTRACT_DEPLOY,
        data={
            'contract_code': contract_code,
            'initial_state': {
                'students': {},
                'grades': {}
            }
        },
        gas_limit=50
    )
    lahka.add_transaction(deploy_tx)
    print("   ✅ Contract deployment transaction added")
    
    # Mine third block
    print("\n⛏️ Mining third block (contract deployment)...")
    success = lahka.mine_block()
    print(f"   {'✅' if success else '❌'} Block mined: {success}")
    
    print_blockchain_state(lahka, "After Contract Deployment")
    print_contracts(lahka, "Deployed Contracts")
    
    # Show final state
    print_separator("FINAL BLOCKCHAIN STATE")
    print_blockchain_state(lahka, "Complete State")
    print_balances(lahka, "Final Balances")
    print_validators(lahka, "Final Validator Status")
    print_recent_blocks(lahka, "Complete Blockchain", 4)
    
    # Show some transaction history
    print_separator("TRANSACTION HISTORY")
    for address in addresses[:2]:  # Show first 2 addresses
        history = lahka.ledger.get_account_history(address, 5)
        print(f"\n📜 {address}'s recent transactions:")
        for entry in history:
            print(f"   💰 {entry.amount:+.2f} LAHKA - {entry.description}")
    
    print("\n🎉 Interactive demo completed!")
    print("💡 You can now explore the blockchain state and see how everything works!")

if __name__ == "__main__":
    interactive_demo() 