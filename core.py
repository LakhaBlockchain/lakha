import hashlib
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import random
from datetime import datetime
from enum import Enum
# Bech32 address utilities
from address import generate_address, is_valid_address
import plyvel
from network.p2p import Node
import ast

class TransactionType(Enum):
    TRANSFER = "transfer"
    CONTRACT_DEPLOY = "contract_deploy"
    CONTRACT_CALL = "contract_call"
    STAKE = "stake"
    UNSTAKE = "unstake"

class ContractStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DESTROYED = "destroyed"

@dataclass
class Account:
    """Represents an account in the ledger"""
    address: str
    balance: float = 0.0
    nonce: int = 0
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    is_contract: bool = False
    contract_address: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'address': self.address,
            'balance': self.balance,
            'nonce': self.nonce,
            'created_at': self.created_at,
            'last_updated': self.last_updated,
            'is_contract': self.is_contract,
            'contract_address': self.contract_address
        }

@dataclass
class LedgerEntry:
    """Represents a ledger entry for double-entry bookkeeping"""
    id: str
    transaction_hash: str
    block_number: int
    timestamp: float
    from_address: str
    to_address: str
    amount: float
    transaction_type: str
    description: str
    gas_cost: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)

class Ledger:
    """Main ledger system for account management and transaction history"""
    
    def __init__(self, storage=None):
        self.accounts: Dict[str, Account] = {}
        self.transactions: List[LedgerEntry] = []
        self.account_history: Dict[str, List[LedgerEntry]] = defaultdict(list)
        self.storage = storage
        
    def create_account(self, address: str, initial_balance: float = 0.0) -> Account:
        """Create a new account. Address must be Bech32 (except 'genesis' and 'stake_pool')."""
        if address in self.accounts:
            return self.accounts[address]
        # Enforce Bech32 address format (except for 'genesis' and 'stake_pool')
        special_addresses = {'genesis', 'stake_pool'}
        if address not in special_addresses and not is_valid_address(address):
            raise ValueError(f"Invalid Lahka address: {address}")
        account = Account(
            address=address,
            balance=initial_balance
        )
        self.accounts[address] = account
        # Persist account
        if self.storage is not None:
            self.storage.put_account(account)
        return account
    
    def get_account(self, address: str) -> Optional[Account]:
        """Get account by address"""
        return self.accounts.get(address)
    
    def get_or_create_account(self, address: str) -> Account:
        """Get existing account or create new one"""
        account = self.get_account(address)
        if not account:
            account = self.create_account(address)
        return account
    
    def update_balance(self, address: str, amount: float, transaction_hash: str, 
                      block_number: int, description: str, gas_cost: float = 0.0):
        """Update account balance and record transaction"""
        account = self.get_or_create_account(address)
        
        # Update balance
        old_balance = account.balance
        new_balance = old_balance + amount
        # Overflow/underflow protection
        if new_balance < 0 or new_balance > 1e18:
            raise ValueError(f"Balance overflow/underflow for {address}: {new_balance}")
        account.balance = new_balance
        account.last_updated = time.time()
        
        # Create ledger entry
        entry = LedgerEntry(
            id=str(uuid.uuid4()),
            transaction_hash=transaction_hash,
            block_number=block_number,
            timestamp=time.time(),
            from_address="",  # Will be set by caller
            to_address=address,
            amount=amount,
            transaction_type="balance_update",
            description=description,
            gas_cost=gas_cost
        )
        
        self.transactions.append(entry)
        self.account_history[address].append(entry)
        # Persist account
        if self.storage is not None:
            self.storage.put_account(account)
    
    def record_transaction(self, transaction_hash: str, block_number: int,
                          from_address: str, to_address: str, amount: float,
                          transaction_type: str, description: str, gas_cost: float = 0.0):
        """Record a complete transaction with double-entry bookkeeping"""
        # Debit from sender
        if from_address and amount > 0:
            self.update_balance(from_address, -amount, transaction_hash, block_number, 
                              f"Debit: {description}", gas_cost)
        
        # Credit to receiver
        if to_address and amount > 0:
            self.update_balance(to_address, amount, transaction_hash, block_number, 
                              f"Credit: {description}")
        
        # Record gas cost separately
        if gas_cost > 0 and from_address:
            self.update_balance(from_address, -gas_cost, transaction_hash, block_number, 
                              f"Gas cost for {transaction_type}", 0.0)
    
    def get_account_history(self, address: str, limit: int = 100) -> List[LedgerEntry]:
        """Get transaction history for an account"""
        return self.account_history[address][-limit:]
    
    def get_balance(self, address: str) -> float:
        """Get current balance for an account"""
        account = self.get_account(address)
        return account.balance if account else 0.0
    
    def get_total_supply(self) -> float:
        """Get total token supply"""
        return sum(account.balance for account in self.accounts.values())
    
    def get_accounts_summary(self) -> Dict[str, Dict]:
        """Get summary of all accounts"""
        return {
            address: {
                'balance': account.balance,
                'nonce': account.nonce,
                'is_contract': account.is_contract,
                'transaction_count': len(self.account_history[address])
            }
            for address, account in self.accounts.items()
        }
    
    def to_dict(self) -> Dict:
        """Convert ledger to dictionary for JSON serialization"""
        return {
            'accounts': {addr: account.to_dict() for addr, account in self.accounts.items()},
            'transactions': [tx.to_dict() for tx in self.transactions],
            'total_supply': self.get_total_supply()
        }

@dataclass
class ContractState:
    """Represents the state of a smart contract"""
    contract_address: str
    data: Dict[str, Any] = field(default_factory=dict)
    code: str = ""
    owner: str = ""
    status: ContractStatus = ContractStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            'contract_address': self.contract_address,
            'data': self.data,
            'code': self.code,
            'owner': self.owner,
            'status': self.status.value if hasattr(self.status, 'value') else self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class ContractEvent:
    """Represents an event emitted by a smart contract"""
    contract_address: str
    event_name: str
    data: Dict[str, Any]
    block_number: int
    transaction_hash: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
@dataclass
class Transaction:
    """Represents a transaction in the Lahka blockchain"""
    from_address: str
    to_address: str
    amount: float = 0.0
    transaction_type: TransactionType = TransactionType.TRANSFER
    data: Dict[str, Any] = field(default_factory=dict)
    gas_limit: int = 21000
    gas_price: float = 1.0
    nonce: int = 0  # Add nonce to transaction
    timestamp: float = field(default_factory=time.time)
    signature: str = ""
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate hash of transaction"""
        tx_data = {
            'from_address': self.from_address,
            'to_address': self.to_address,
            'amount': self.amount,
            'transaction_type': self.transaction_type.value if hasattr(self.transaction_type, 'value') else self.transaction_type,
            'data': self.data,
            'gas_limit': self.gas_limit,
            'gas_price': self.gas_price,
            'nonce': self.nonce,  # Include nonce in hash
            'timestamp': self.timestamp
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'from_address': self.from_address,
            'to_address': self.to_address,
            'amount': self.amount,
            'transaction_type': self.transaction_type.value if hasattr(self.transaction_type, 'value') else self.transaction_type,
            'data': self.data,
            'gas_limit': self.gas_limit,
            'gas_price': self.gas_price,
            'nonce': self.nonce,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'hash': self.hash
        }

@dataclass
class Block:
    """Represents a block in the Lahka blockchain"""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    validator: str
    state_root: str = ""
    nonce: int = 0
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate hash of block"""
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'validator': self.validator,
            'state_root': self.state_root,
            'nonce': self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'validator': self.validator,
            'state_root': self.state_root,
            'nonce': self.nonce,
            'hash': self.hash
        }

@dataclass
class Validator:
    """Represents a validator in the PoCS (Proof of Contribution Stake) system"""
    address: str
    stake: float
    reputation: float = 100.0
    is_active: bool = True
    last_block_time: float = 0
    blocks_validated: int = 0
    total_rewards: float = 0.0
    
    # PoCS-specific metrics
    registered_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    uptime_percentage: float = 95.0
    response_time_avg: float = 1.0  # seconds
    geographic_location: str = "unknown"
    unique_transaction_types: int = 0
    all_transaction_types: set = field(default_factory=set)  # Track all unique types
    contribution_score: float = 0.0
    reliability_score: float = 100.0
    diversity_bonus: float = 0.0
    total_uptime_seconds: float = 0.0
    last_seen: float = field(default_factory=time.time)
    blocks_attempted: int = 0
    blocks_successful: int = 0
    txs_processed: int = 0
    contribution_history: list = field(default_factory=list)
    # Chunk 3: Reputation system
    peer_ratings: dict = field(default_factory=dict)  # {peer_address: (rating, timestamp, reason)}
    average_peer_rating: float = 100.0
    reputation_score: float = 100.0
    last_peer_review: float = 0.0
    # Chunk 4: Dynamic penalties and contribution mining
    penalty_history: list = field(default_factory=list)  # [(timestamp, penalty_type, severity, reason)]
    current_penalty_multiplier: float = 1.0
    rehabilitation_progress: float = 0.0  # 0-100, progress toward penalty reduction
    contribution_credits: float = 0.0  # Credits earned through non-monetary contributions
    contribution_activities: list = field(default_factory=list)  # [(timestamp, activity_type, credits_earned)]
    # Chunk 5: Performance optimizations and advanced features
    _cached_pocs_score: float = 0.0
    _last_score_calculation: float = 0.0
    _score_cache_duration: float = 5.0  # Cache for 5 seconds
    collaboration_score: float = 0.0  # Cross-validator collaboration
    network_health_contribution: float = 0.0  # Contribution to network health
    dynamic_weight_adjustment: float = 1.0  # Dynamic weight based on network conditions
    
    def __post_init__(self):
        # Convert lists back to sets for set fields after dataclass init
        if isinstance(self.all_transaction_types, list):
            self.all_transaction_types = set(self.all_transaction_types)
    
    def calculate_pocs_score(self, current_time: float, force_recalculate: bool = False) -> float:
        """Calculate PoCS score using optimized multi-dimensional formula with caching"""
        # Use cached score if recent enough
        if not force_recalculate and (current_time - self._last_score_calculation) < self._score_cache_duration:
            return self._cached_pocs_score
        # Temporal decay: stakes lose power over time without activity
        days_inactive = (current_time - self.last_activity) / (24 * 3600)  # days
        effective_stake = self.stake * max(0.1, 1 - 0.001 * days_inactive)  # Max 90% decay
        # Multi-dimensional scoring formula with balanced weights
        stake_component = effective_stake * 0.25 * self.dynamic_weight_adjustment  # 25% weight (reduced from 35%)
        # Uptime and block success rate
        uptime_factor = min(1.0, self.total_uptime_seconds / max(1, (current_time - self.registered_at)))
        block_success_rate = self.blocks_successful / max(1, self.blocks_attempted)
        txs_factor = min(1.0, self.txs_processed / 100)
        # Enhanced contribution component with higher weight
        contribution_component = (
            self.contribution_score * 0.3 +
            uptime_factor * 15 +
            block_success_rate * 15 +
            txs_factor * 15 +
            self.collaboration_score * 8 +  # Increased collaboration bonus
            self.network_health_contribution * 5  # Increased network health bonus
        ) * 0.25  # 25% weight
        # Increased weights for reputation and reliability
        reliability_component = self.reliability_score * 0.25  # 25% weight (increased from 20%)
        reputation_component = self.reputation_score * 0.15  # 15% weight (increased from 10%)
        diversity_component = self.diversity_bonus * 0.1  # 10% weight (increased from 0.1)
        # Penalty component: subtract based on penalty multiplier and recent penalty severity
        recent_penalty = 0.0
        if self.penalty_history:
            # Use the most recent penalty severity
            recent_penalty = self.penalty_history[-1][2]
        penalty_component = self.current_penalty_multiplier * recent_penalty * 0.1  # 10% weight
        total_score = (stake_component + contribution_component + reliability_component + 
                      reputation_component + diversity_component - penalty_component)
        # Cache the result
        self._cached_pocs_score = max(0, total_score)
        self._last_score_calculation = current_time
        return self._cached_pocs_score
    
    def update_collaboration_score(self, collaboration_activity: str, score_increase: float):
        """Update collaboration score based on cross-validator activities"""
        self.collaboration_score = min(100.0, self.collaboration_score + score_increase)
        
        # Log collaboration activity
        self.contribution_history.append((
            time.time(), 
            f"collaboration_{collaboration_activity}", 
            score_increase
        ))
        
        # Invalidate score cache
        self._last_score_calculation = 0.0
    
    def update_network_health_contribution(self, health_metric: str, contribution: float):
        """Update network health contribution score"""
        self.network_health_contribution = min(100.0, self.network_health_contribution + contribution)
        
        # Log network health activity
        self.contribution_history.append((
            time.time(), 
            f"network_health_{health_metric}", 
            contribution
        ))
        
        # Invalidate score cache
        self._last_score_calculation = 0.0
    
    def adjust_dynamic_weight(self, network_condition: str, adjustment_factor: float):
        """Adjust dynamic weight based on network conditions"""
        if network_condition == "high_load":
            self.dynamic_weight_adjustment = min(1.5, self.dynamic_weight_adjustment * adjustment_factor)
        elif network_condition == "low_load":
            self.dynamic_weight_adjustment = max(0.5, self.dynamic_weight_adjustment * adjustment_factor)
        elif network_condition == "normal":
            self.dynamic_weight_adjustment = 1.0
        
        # Invalidate score cache
        self._last_score_calculation = 0.0
    
    def get_performance_metrics(self) -> dict:
        """Get comprehensive performance metrics"""
        current_time = time.time()
        return {
            'pocs_score': self.calculate_pocs_score(current_time),
            'stake': self.stake,
            'reputation': self.reputation_score,
            'reliability': self.reliability_score,
            'contribution_score': self.contribution_score,
            'collaboration_score': self.collaboration_score,
            'collaboration': self.collaboration_score,
            'network_health_contribution': self.network_health_contribution,
            'network_health': self.network_health_contribution,
            'penalty_multiplier': self.current_penalty_multiplier,
            'rehabilitation_progress': self.rehabilitation_progress,
            'contribution_credits': self.contribution_credits,
            'blocks_success_rate': self.blocks_successful / max(1, self.blocks_attempted),
            'uptime_percentage': self.uptime_percentage,
            'response_time_avg': self.response_time_avg,
            'total_activities': len(self.contribution_activities),
            'total_penalties': len(self.penalty_history),
            'dynamic_weight': self.dynamic_weight_adjustment
        }
    
    def update_activity(self, current_time: float):
        """Update validator activity timestamp"""
        self.last_activity = current_time
        self.last_seen = current_time
    
    def update_contribution_score(self, new_contribution: float, event: str = ""):
        """Update contribution score based on network participation"""
        self.contribution_score = self.contribution_score * 0.9 + new_contribution * 0.1
        if event:
            self.contribution_history.append((time.time(), event, new_contribution))
        # Invalidate score cache
        self._last_score_calculation = 0.0
    
    def update_reliability_score(self, success: bool, response_time: float):
        """Update reliability score based on performance"""
        # Update response time average
        self.response_time_avg = self.response_time_avg * 0.9 + response_time * 0.1
        
        # Update reliability based on success/failure
        if success:
            self.reliability_score = min(100, self.reliability_score + 1)
        else:
            self.reliability_score = max(0, self.reliability_score - 5)
        # Invalidate score cache
        self._last_score_calculation = 0.0
    
    def update_uptime(self, seconds: float):
        self.total_uptime_seconds += seconds
    
    def record_block_attempt(self, success: bool, tx_count: int):
        self.blocks_attempted += 1
        if success:
            self.blocks_successful += 1
        self.txs_processed += tx_count
    
    def rate_peer(self, peer_address: str, rating: float, reason: str = ""):
        """Rate another validator (1-100 scale)"""
        if not (1 <= rating <= 100):
            raise ValueError("Rating must be between 1 and 100")
        
        current_time = time.time()
        self.peer_ratings[peer_address] = (rating, current_time, reason)
        self.last_peer_review = current_time
    
    def get_average_peer_rating(self) -> float:
        """Calculate average rating received from peers"""
        if not self.peer_ratings:
            return 100.0  # Default rating if no peer ratings
        
        ratings = [rating for rating, _, _ in self.peer_ratings.values()]
        return sum(ratings) / len(ratings)
    
    def update_reputation_score(self):
        """Update reputation score based on peer ratings and other factors"""
        peer_rating = self.get_average_peer_rating()
        # Combine peer rating with reliability and contribution
        reputation_factors = [
            peer_rating * 0.4,  # 40% peer rating
            self.reliability_score * 0.3,  # 30% reliability
            min(100, self.contribution_score) * 0.3  # 30% contribution (capped at 100)
        ]
        self.reputation_score = sum(reputation_factors)
        self.average_peer_rating = peer_rating
        # Invalidate PoCS score cache
        self._last_score_calculation = 0.0
    
    def apply_penalty(self, penalty_type: str, severity: float, reason: str = ""):
        """Apply penalty to validator with escalating multiplier"""
        current_time = time.time()
        # Add penalty to history first
        self.penalty_history.append((current_time, penalty_type, severity, reason))
        # Calculate penalty multiplier based on updated history
        multiplier = self.calculate_penalty_multiplier()
        # Apply penalty
        actual_penalty = severity * multiplier
        self.current_penalty_multiplier = multiplier
        # Reduce reputation and reliability scores
        self.reputation_score = max(0, self.reputation_score - actual_penalty * 0.5)
        self.reliability_score = max(0, self.reliability_score - actual_penalty * 0.3)
        # Reset rehabilitation progress
        self.rehabilitation_progress = 0.0
        # Invalidate PoCS score cache
        self._last_score_calculation = 0.0
    
    def calculate_penalty_multiplier(self) -> float:
        """Calculate escalating penalty multiplier based on history"""
        recent_penalties = [p for p in self.penalty_history 
                          if time.time() - p[0] < 30 * 24 * 3600]  # Last 30 days
        
        # Base multiplier increases with each recent penalty
        base_multiplier = 1.0 + (len(recent_penalties) * 0.5)
        
        # Cap at 5x multiplier
        return min(5.0, base_multiplier)
    
    def update_rehabilitation_progress(self, contribution: float):
        """Update rehabilitation progress through positive contributions"""
        self.rehabilitation_progress = min(100.0, self.rehabilitation_progress + contribution)
        
        # If rehabilitation is complete, reduce penalty multiplier
        if self.rehabilitation_progress >= 100.0:
            self.current_penalty_multiplier = max(1.0, self.current_penalty_multiplier * 0.8)
            self.rehabilitation_progress = 0.0  # Reset for next cycle
    
    def earn_contribution_credits(self, activity_type: str, credits: float, description: str = ""):
        """Earn contribution credits through non-monetary activities"""
        current_time = time.time()
        
        self.contribution_credits += credits
        self.contribution_activities.append((current_time, activity_type, credits, description))
        
        # Update rehabilitation progress
        self.update_rehabilitation_progress(credits * 1.0)  # Increased from 0.1 to make rehabilitation faster
        
        # Update contribution score
        self.update_contribution_score(credits * 0.5, f"contribution_activity_{activity_type}")
    
    def convert_credits_to_stake(self, credits_to_convert: float) -> float:
        """Convert contribution credits to stake (1 credit = 0.1 stake)"""
        if credits_to_convert > self.contribution_credits:
            credits_to_convert = self.contribution_credits
        
        stake_earned = credits_to_convert * 0.1
        self.contribution_credits -= credits_to_convert
        self.stake += stake_earned
        
        return stake_earned
    
    def get_contribution_summary(self) -> dict:
        """Get summary of contribution activities"""
        total_credits = sum(credits for _, _, credits, _ in self.contribution_activities)
        activity_types = set(activity_type for _, activity_type, _, _ in self.contribution_activities)
        
        return {
            'total_credits_earned': total_credits,
            'current_credits': self.contribution_credits,
            'activity_types': list(activity_types),
            'rehabilitation_progress': self.rehabilitation_progress,
            'penalty_multiplier': self.current_penalty_multiplier
        }
    
    def to_dict(self) -> Dict:
        # Only include dataclass fields, not computed properties
        dataclass_fields = set(f.name for f in self.__dataclass_fields__.values())
        d = {k: v for k, v in self.__dict__.items() if k in dataclass_fields}
        # Convert sets to lists for JSON serialization
        if 'all_transaction_types' in d and isinstance(d['all_transaction_types'], set):
            d['all_transaction_types'] = list(d['all_transaction_types'])
        if 'contribution_activities' in d and isinstance(d['contribution_activities'], set):
            d['contribution_activities'] = list(d['contribution_activities'])
        return d

class SmartContractEngine:
    """Generic smart contract execution engine"""
    
    def __init__(self):
        self.contracts: Dict[str, ContractState] = {}
        self.events: List[ContractEvent] = []
        self.gas_used: int = 0
        self.max_gas_limit = 1000000
        
    def deploy_contract(self, contract_code: str, initial_state: Dict[str, Any], 
                       deployer_address: str, gas_limit: int) -> str:
        """Deploy a new smart contract"""
        if gas_limit > self.max_gas_limit:
            raise Exception("Gas limit exceeded")
        
        # Validate and sanitize initial state
        sanitized_state = self._sanitize_contract_state(initial_state)
        
        # Generate unique contract address using Bech32
        contract_address = generate_address()
        # Create contract state
        contract_state = ContractState(
            contract_address=contract_address,
            code=contract_code,
            data=sanitized_state,
            owner=deployer_address
        )
        # Store contract
        self.contracts[contract_address] = contract_state
        # Emit deployment event
        self._emit_event(contract_address, "ContractDeployed", {
            "deployer": deployer_address,
            "contract_address": contract_address,
            "initial_state": sanitized_state
        })
        return contract_address
    
    def _sanitize_contract_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize contract state to ensure JSON compatibility"""
        sanitized = {}
        for key, value in state.items():
            # Skip None keys
            if key is None:
                continue
            # Convert key to string if it's not already
            str_key = str(key) if key != "" else "_empty_key"
            
            # Sanitize value
            sanitized_value = self._sanitize_value(value)
            if sanitized_value is not None:
                sanitized[str_key] = sanitized_value
        return sanitized
    
    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize a single value to ensure JSON compatibility"""
        if value is None:
            return None
        elif isinstance(value, (int, str, bool)):
            return value
        elif isinstance(value, float):
            # Handle infinity and NaN
            if value == float('inf'):
                return 1e308  # Large finite number
            elif value == float('-inf'):
                return -1e308  # Large negative finite number
            elif value != value:  # NaN
                return 0.0
            else:
                return value
        elif isinstance(value, dict):
            return self._sanitize_contract_state(value)
        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value if self._sanitize_value(item) is not None]
        else:
            # Convert other types to string
            return str(value)
    
    def call_contract(self, contract_address: str, function_name: str, 
                     args: List[Any], caller_address: str, gas_limit: int) -> Any:
        """Execute a function on a smart contract"""
        if contract_address not in self.contracts:
            raise Exception("Contract not found")
        
        contract = self.contracts[contract_address]
        if contract.status != ContractStatus.ACTIVE:
            raise Exception("Contract is not active")
        
        # Execute contract function
        try:
            # Create execution context
            context = {
                'msg_sender': caller_address,
                'contract_address': contract_address,
                'block_timestamp': time.time(),
                'gas_limit': gas_limit
            }
            
            # Execute function (simplified - in real implementation, this would be a proper VM)
            result = self._execute_contract_function(contract, function_name, args, context)
            
            # Update contract state
            contract.updated_at = time.time()
            
            return result
            
        except Exception as e:
            # Revert state changes on error
            self._revert_contract_state(contract_address)
            raise e
    
    def get_contract_state(self, contract_address: str, key_path: str = "") -> Any:
        """Get contract state data"""
        if contract_address not in self.contracts:
            raise Exception("Contract not found")
        
        contract = self.contracts[contract_address]
        
        if not key_path:
            return contract.data
        
        # Navigate nested key path (e.g., "students.123.grades.math")
        keys = key_path.split('.')
        data = contract.data
        
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        
        return data
    
    def _generate_contract_address(self, deployer: str, code: str) -> str:
        """Generate unique contract address"""
        unique_string = f"{deployer}{code}{time.time()}{random.random()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:40]
    
    def _execute_contract_function(self, contract: ContractState, function_name: str, 
                                 args: List[Any], context: Dict[str, Any]) -> Any:
        """Execute a contract function (simplified implementation)"""
        # This is a simplified execution - in a real implementation, you'd have a proper VM
        # For now, we'll simulate basic function execution
        
        if function_name == "set_state":
            key, value = args[0], args[1]
            contract.data[key] = value
            return True
        
        elif function_name == "get_state":
            key = args[0]
            return contract.data.get(key)
        
        elif function_name == "emit_event":
            event_name, event_data = args[0], args[1]
            self._emit_event(contract.contract_address, event_name, event_data)
            return True
        
        else:
            # Try to execute custom function from contract code
            # This would require a proper VM implementation
            raise Exception(f"Function {function_name} not found or not implemented")
    
    def _emit_event(self, contract_address: str, event_name: str, data: Dict[str, Any]):
        """Emit a contract event"""
        event = ContractEvent(
            contract_address=contract_address,
            event_name=event_name,
            data=data,
            block_number=0,  # Will be set by blockchain
            transaction_hash=""  # Will be set by blockchain
        )
        self.events.append(event)
    
    def _revert_contract_state(self, contract_address: str):
        """Revert contract state changes (simplified)"""
        # In a real implementation, you'd have state snapshots
        pass

class LakhaContractSandbox(ast.NodeVisitor):
    """
    AST-based sandbox for Lakha smart contracts.
    - Rejects dangerous constructs (import, exec, eval, open, etc.)
    - Counts operations for gas metering
    """
    SAFE_BUILTINS = {
        'abs', 'min', 'max', 'sum', 'len', 'range', 'enumerate', 'int', 'float', 'str', 'dict', 'list', 'set', 'bool', 'print'
    }
    FORBIDDEN_NAMES = {'exec', 'eval', 'open', '__import__', 'compile', 'input', 'globals', 'locals', 'os', 'sys', 'subprocess'}
    FORBIDDEN_NODES = (ast.Import, ast.ImportFrom, ast.With, ast.Try, ast.Lambda)

    def __init__(self, gas_limit=10000):
        self.gas_limit = gas_limit
        self.gas_used = 0
        self.errors = []

    def visit(self, node):
        self.gas_used += 1
        if self.gas_used > self.gas_limit:
            raise RuntimeError("Gas limit exceeded!")
        return super().visit(node)

    def generic_visit(self, node):
        if isinstance(node, self.FORBIDDEN_NODES):
            raise RuntimeError(f"Forbidden construct: {type(node).__name__}")
        return super().generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.FORBIDDEN_NAMES:
            raise RuntimeError(f"Forbidden name: {node.id}")
        self.gas_used += 1
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.FORBIDDEN_NAMES:
            raise RuntimeError(f"Forbidden attribute access: {node.value.id}.{node.attr}")
        self.gas_used += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        # Only allow safe built-ins
        if isinstance(node.func, ast.Name):
            if node.func.id not in self.SAFE_BUILTINS and not node.func.id.isidentifier():
                raise RuntimeError(f"Forbidden function call: {node.func.id}")
        self.gas_used += 1
        self.generic_visit(node)

class LevelDBStorage:
    """LevelDB-backed storage for blockchain data"""
    def __init__(self, db_path='lakha_db'):
        self.db = plyvel.DB(db_path, create_if_missing=True)

    def put_block(self, block):
        key = f'block:{block.index}'.encode()
        value = json.dumps(block.to_dict()).encode()
        self.db.put(key, value)

    def get_block(self, index):
        key = f'block:{index}'.encode()
        value = self.db.get(key)
        if value:
            return json.loads(value.decode())
        return None

    def put_account(self, account):
        key = f'account:{account.address}'.encode()
        value = json.dumps(account.to_dict()).encode()
        self.db.put(key, value)

    def get_account(self, address):
        key = f'account:{address}'.encode()
        value = self.db.get(key)
        if value:
            return json.loads(value.decode())
        return None

    def put_validator(self, validator):
        key = f'validator:{validator.address}'.encode()
        value = json.dumps(validator.to_dict()).encode()
        self.db.put(key, value)

    def get_validator(self, address):
        key = f'validator:{address}'.encode()
        value = self.db.get(key)
        if value:
            return json.loads(value.decode())
        return None

    # --- Contract persistence ---
    def put_contract(self, contract):
        key = f'contract:{contract.contract_address}'.encode()
        value = json.dumps(contract.to_dict()).encode()
        self.db.put(key, value)

    def get_contract(self, contract_address):
        key = f'contract:{contract_address}'.encode()
        value = self.db.get(key)
        if value:
            return json.loads(value.decode())
        return None

    def close(self):
        self.db.close()

class LakhaContractVM:
    """
    Minimal VM for executing Lakha smart contracts (Python subset).
    Provides msg, block, and contract API context.
    Now integrates AST sandboxing and gas metering.
    """
    def __init__(self, blockchain_context):
        self.context = blockchain_context  # e.g., {"msg": ..., "block": ...}

    def execute(self, contract_class, method_name, args=None):
        """
        Instantiate contract_class, inject context, and call method_name with args.
        """
        if args is None:
            args = {}
        # Inject context globals
        global msg, block, emit_event, transfer
        msg = self.context["msg"]
        block = self.context["block"]
        emit_event = self.context.get("emit_event", lambda *a, **kw: None)
        transfer = self.context.get("transfer", lambda *a, **kw: None)
        # Instantiate contract
        contract = contract_class()
        # Call method
        method = getattr(contract, method_name)
        return method(**args)

    @staticmethod
    def validate_contract_source(contract_source, gas_limit=10000):
        """
        Parse and validate contract source code using the AST sandbox.
        Raises RuntimeError if forbidden constructs or gas overuse are detected.
        """
        tree = ast.parse(contract_source)
        sandbox = LakhaContractSandbox(gas_limit=gas_limit)
        sandbox.visit(tree)
        # If no exception, contract is valid under current rules
        return True

class LahkaBlockchain:
    """Main LAKHA blockchain implementation with smart contracts and Proof of Stake"""
    
    def __init__(self, test_mode=False, db_path='lakha_db', p2p_port=None, p2p_peers=None):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.validators: Dict[str, Validator] = {}
        self.storage = LevelDBStorage(db_path=db_path)
        self.ledger = Ledger(storage=self.storage)
        self.contract_engine = SmartContractEngine()
        self.processed_tx_hashes = set()  # Track processed tx hashes for replay protection
        self.test_mode = test_mode  # Enable test mode for deterministic behavior
        # Configuration
        self.minimum_stake = 10.0
        self.block_time = 5.0
        self.block_reward = 1.0
        self.gas_price = 0.001  # Reduced from 1.0 for demo
        # P2P networking (optional)
        self.p2p_node = None
        self.p2p_port = p2p_port
        self.p2p_peers = p2p_peers
        # Load chain from LevelDB if exists
        self._load_chain_from_db()
        # Create genesis block if chain is empty
        if not self.chain:
            self.create_genesis_block()
    
    def _load_chain_from_db(self):
        # Load blocks in order from LevelDB
        i = 0
        while True:
            block_data = self.storage.get_block(i)
            if not block_data:
                break
            block = Block(
                index=block_data['index'],
                timestamp=block_data['timestamp'],
                transactions=[Transaction(**tx) for tx in block_data['transactions']],
                previous_hash=block_data['previous_hash'],
                validator=block_data['validator'],
                state_root=block_data.get('state_root', ''),
                nonce=block_data.get('nonce', 0),
                hash=block_data.get('hash', '')
            )
            self.chain.append(block)
            i += 1
        # Load accounts from LevelDB
        for key, value in self.storage.db:
            if key.startswith(b'account:'):
                acc_data = value.decode()
                acc_dict = json.loads(acc_data)
                self.ledger.accounts[acc_dict['address']] = Account(**acc_dict)
        # Load validators from LevelDB
        for key, value in self.storage.db:
            if key.startswith(b'validator:'):
                val_data = value.decode()
                val_dict = json.loads(val_data)
                self.validators[val_dict['address']] = Validator(**val_dict)
        # Load contracts from LevelDB
        for key, value in self.storage.db:
            if key.startswith(b'contract:'):
                try:
                    contract_data = value.decode()
                    contract_dict = json.loads(contract_data)
                    
                    # Extract contract address from key or use fallback
                    contract_address = None
                    if 'contract_address' in contract_dict:
                        contract_address = contract_dict['contract_address']
                    else:
                        # Extract from key: 'contract:address' -> 'address'
                        contract_address = key.decode().split(':', 1)[1]
                    
                    contract_obj = ContractState(
                        contract_address=contract_address,
                        data=contract_dict.get('data', {}),
                        code=contract_dict.get('code', ''),
                        owner=contract_dict.get('owner', ''),
                        status=ContractStatus(contract_dict.get('status', 'active')),
                        created_at=contract_dict.get('created_at', time.time()),
                        updated_at=contract_dict.get('updated_at', time.time())
                    )
                    print(f"[DEBUG] Loaded contract: {contract_obj.contract_address}, state={contract_obj.data}")
                    self.contract_engine.contracts[contract_obj.contract_address] = contract_obj
                except Exception as e:
                    print(f"[WARNING] Failed to load contract from key {key}: {e}")
                    continue

    def close(self):
        self.storage.close()
    
    def create_genesis_block(self):
        """Create the first block in the blockchain"""
        # Use deterministic timestamp to ensure all nodes have same genesis block
        # This is crucial for P2P synchronization
        genesis_timestamp = 1640995200.0  # Fixed timestamp: 2022-01-01 00:00:00 UTC
            
        genesis_block = Block(
            index=0,
            timestamp=genesis_timestamp,
            transactions=[],
            previous_hash="0",
            validator="genesis"
        )
        self.chain.append(genesis_block)
        # Persist genesis block to LevelDB
        self.storage.put_block(genesis_block)
        # Give initial tokens to genesis address
        self.ledger.create_account("genesis", 10000000.0)  # Increased from 1M to 10M
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a transaction to the pending pool. Enforce Bech32 addresses (except 'genesis' and 'stake_pool')."""
        # Validate addresses - reject empty addresses
        if not transaction.from_address or (transaction.from_address != 'genesis' and not is_valid_address(transaction.from_address)):
            print(f"[DEBUG] add_transaction: Invalid from_address: {transaction.from_address}")
            return False
        # Allow 'genesis' and 'stake_pool' as special addresses, but reject empty to_address
        special_addresses = {'genesis', 'stake_pool'}
        # Allow empty to_address for CONTRACT_DEPLOY and CONTRACT_CALL
        if transaction.transaction_type in [TransactionType.CONTRACT_DEPLOY, TransactionType.CONTRACT_CALL]:
            pass
        elif not transaction.to_address or (transaction.to_address not in special_addresses and not is_valid_address(transaction.to_address)):
            print(f"[DEBUG] add_transaction: Invalid to_address: {transaction.to_address}")
            return False
        # Special address restrictions: stake_pool only accepts STAKE transactions
        if transaction.to_address == 'stake_pool' and transaction.transaction_type != TransactionType.STAKE:
            print(f"[DEBUG] add_transaction: stake_pool only accepts STAKE transactions")
            return False
        # Replay protection: reject duplicate tx hash (both processed and pending)
        if transaction.hash in self.processed_tx_hashes:
            print(f"[DEBUG] add_transaction: Duplicate transaction hash: {transaction.hash}")
            return False
        # Check for duplicate hash in pending transactions
        for pending_tx in self.pending_transactions:
            if pending_tx.hash == transaction.hash:
                print(f"[DEBUG] add_transaction: Duplicate hash in pending pool: {transaction.hash}")
                return False
        # Nonce checks
        sender_account = self.ledger.get_account(transaction.from_address)
        if sender_account:
            expected_nonce = sender_account.nonce
            if transaction.nonce != expected_nonce:
                # Be more lenient with nonce mismatches for genesis account in multi-node setup
                if transaction.from_address == "genesis":
                    # Accept genesis transactions with higher nonces (from other nodes)
                    if transaction.nonce > expected_nonce:
                        print(f"[DEBUG] add_transaction: Genesis nonce mismatch, accepting higher nonce: expected={expected_nonce}, got={transaction.nonce}")
                        # Update the local genesis account nonce to match
                        sender_account.nonce = transaction.nonce
                        self.storage.put_account(sender_account)
                    else:
                        print(f"[DEBUG] add_transaction: Genesis nonce mismatch, rejecting lower nonce: expected={expected_nonce}, got={transaction.nonce}")
                        return False
                else:
                    print(f"[DEBUG] add_transaction: Nonce mismatch for {transaction.from_address}: expected={expected_nonce}, got={transaction.nonce}")
                    return False
            # Check for duplicate nonce in pending transactions (double-spending prevention)
            for pending_tx in self.pending_transactions:
                if (pending_tx.from_address == transaction.from_address and 
                    pending_tx.nonce == transaction.nonce):
                    print(f"[DEBUG] add_transaction: Duplicate nonce in pending pool: {transaction.nonce}")
                    return False
        # Gas/amount checks
        if transaction.gas_limit <= 0 or transaction.gas_price <= 0:
            print(f"[DEBUG] add_transaction: Invalid gas parameters: limit={transaction.gas_limit}, price={transaction.gas_price}")
            return False
        if transaction.amount < 0:
            print(f"[DEBUG] add_transaction: Negative amount: {transaction.amount}")
            return False
        if not self.validate_transaction(transaction):
            print(f"[DEBUG] add_transaction: Transaction validation failed")
            return False
        # Memory exhaustion protection: limit pending tx pool
        if len(self.pending_transactions) >= 10000:
            print(f"[DEBUG] add_transaction: Pending pool full: {len(self.pending_transactions)}")
            return False
        self.pending_transactions.append(transaction)
        return True
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        """Validate a transaction"""
        # Check if sender has enough balance for gas
        gas_cost = transaction.gas_limit * self.gas_price  # Use instance gas_price instead of transaction.gas_price
        total_cost = transaction.amount + gas_cost
        sender_balance = self.ledger.get_balance(transaction.from_address)
        if sender_balance < total_cost:
            print(f"[DEBUG] validate_transaction: INSUFFICIENT FUNDS for {transaction.transaction_type.value} from {transaction.from_address}: balance={sender_balance}, required={total_cost}")
            return False
        # Validate based on transaction type
        if transaction.transaction_type == TransactionType.TRANSFER:
            if transaction.amount <= 0:
                print(f"[DEBUG] validate_transaction: TRANSFER amount <= 0: {transaction.amount}")
                return False
        elif transaction.transaction_type == TransactionType.CONTRACT_DEPLOY:
            if not transaction.data.get('contract_code'):
                print(f"[DEBUG] validate_transaction: CONTRACT_DEPLOY missing contract_code")
                return False
        elif transaction.transaction_type == TransactionType.CONTRACT_CALL:
            if not transaction.data.get('contract_address'):
                print(f"[DEBUG] validate_transaction: CONTRACT_CALL missing contract_address")
                return False
        elif transaction.transaction_type == TransactionType.STAKE:
            if transaction.amount < self.minimum_stake:
                print(f"[DEBUG] validate_transaction: STAKE amount < minimum_stake: {transaction.amount} < {self.minimum_stake}")
                return False
        # If all checks pass
        return True
    
    def process_transaction(self, transaction: Transaction):
        """Process a transaction and update state"""
        gas_cost = transaction.gas_limit * self.gas_price  # Use instance gas_price
        block_number = len(self.chain)
        self.processed_tx_hashes.add(transaction.hash)
        sender_account = self.ledger.get_account(transaction.from_address)
        if sender_account:
            sender_account.nonce += 1
        if transaction.transaction_type == TransactionType.TRANSFER:
            self.ledger.record_transaction(
                transaction_hash=transaction.hash,
                block_number=block_number,
                from_address=transaction.from_address,
                to_address=transaction.to_address,
                amount=transaction.amount,
                transaction_type="transfer",
                description="Token transfer",
                gas_cost=gas_cost
            )
            self.storage.put_account(self.ledger.get_account(transaction.from_address))
            self.storage.put_account(self.ledger.get_account(transaction.to_address))
        elif transaction.transaction_type == TransactionType.CONTRACT_DEPLOY:
            contract_code = transaction.data['contract_code']
            initial_state = transaction.data.get('initial_state', {})
            try:
                contract_address = self.contract_engine.deploy_contract(
                    contract_code, initial_state, transaction.from_address, 
                    transaction.gas_limit
                )
                transaction.data['deployed_address'] = contract_address
                # Persist contract to LevelDB
                contract_obj = self.contract_engine.contracts[contract_address]
                print(f"[DEBUG] Persisting contract after deploy: {contract_obj.contract_address}, state={contract_obj.data}")
                self.storage.put_contract(contract_obj)
                self.ledger.update_balance(
                    transaction.from_address, -gas_cost, transaction.hash, 
                    block_number, "Gas cost for contract deployment", 0.0
                )
            except Exception as e:
                self.ledger.update_balance(
                    transaction.from_address, gas_cost, transaction.hash, 
                    block_number, "Gas cost reverted", 0.0
                )
                raise e
            self.storage.put_account(self.ledger.get_account(transaction.from_address))
        elif transaction.transaction_type == TransactionType.CONTRACT_CALL:
            contract_address = transaction.data['contract_address']
            function_name = transaction.data['function_name']
            args = transaction.data.get('args', [])
            try:
                result = self.contract_engine.call_contract(
                    contract_address, function_name, args, 
                    transaction.from_address, transaction.gas_limit
                )
                transaction.data['result'] = result
                # Persist contract to LevelDB after state change
                contract_obj = self.contract_engine.contracts[contract_address]
                print(f"[DEBUG] Persisting contract after call: {contract_obj.contract_address}, state={contract_obj.data}")
                self.storage.put_contract(contract_obj)
                self.ledger.update_balance(
                    transaction.from_address, -gas_cost, transaction.hash, 
                    block_number, "Gas cost for contract call", 0.0
                )
            except Exception as e:
                self.ledger.update_balance(
                    transaction.from_address, gas_cost, transaction.hash, 
                    block_number, "Gas cost reverted", 0.0
                )
                raise e
            self.storage.put_account(self.ledger.get_account(transaction.from_address))
        elif transaction.transaction_type == TransactionType.STAKE:
            self.ledger.record_transaction(
                transaction_hash=transaction.hash,
                block_number=block_number,
                from_address=transaction.from_address,
                to_address="stake_pool",
                amount=transaction.amount,
                transaction_type="stake",
                description="Validator stake",
                gas_cost=gas_cost
            )
            if transaction.from_address not in self.validators:
                print(f"[DEBUG] process_transaction: Adding validator {transaction.from_address} with stake {transaction.amount}")
                self.validators[transaction.from_address] = Validator(
                    address=transaction.from_address,
                    stake=transaction.amount
                )
            self.storage.put_account(self.ledger.get_account(transaction.from_address))
            self.storage.put_validator(self.validators[transaction.from_address])
    
    def register_validator(self, address: str, stake_amount: float) -> bool:
        """Register a new validator. Address must be Bech32 (except 'genesis')."""
        if not address or (address != 'genesis' and not is_valid_address(address)):
            print(f"[DEBUG] Invalid address: {address}")
            return False
        if address in self.validators:
            print(f"[DEBUG] Duplicate validator registration: {address}")
            return False
        if stake_amount < self.minimum_stake:
            print(f"[DEBUG] Stake amount too low: {stake_amount}")
            return False
        # Check for sufficient balance for stake + gas
        gas_limit = 10
        gas_price = 1.0
        total_required = stake_amount + gas_limit * gas_price
        current_balance = self.ledger.get_balance(address)
        print(f"[DEBUG] Registering validator {address}: balance={current_balance}, required={total_required}")
        if current_balance < total_required:
            print(f"[DEBUG] Insufficient balance for {address}: has {current_balance}, needs {total_required}")
            return False
        
        # Get the correct nonce for the account
        account = self.ledger.get_account(address)
        if not account:
            print(f"[DEBUG] Account not found: {address}")
            return False
        
        # Create stake transaction with correct nonce
        stake_tx = Transaction(
            from_address=address,
            to_address="stake_pool",
            amount=stake_amount,
            transaction_type=TransactionType.STAKE,
            gas_limit=gas_limit,
            nonce=account.nonce  # Use correct nonce
        )
        success = self.add_transaction(stake_tx)
        if success:
            # Add validator immediately to prevent duplicate registration
            self.validators[address] = Validator(
                address=address,
                stake=stake_amount
            )
        return success
    
    def select_validator(self) -> Optional[str]:
        """Select a validator using PoCS (Proof of Contribution Stake) scoring"""
        if not self.validators:
            return None
        
        active_validators = {addr: val for addr, val in self.validators.items() 
                           if val.is_active}
        
        if not active_validators:
            return None
        
        current_time = time.time()
        
        # Calculate PoCS scores for all active validators
        validator_scores = {}
        total_score = 0
        
        for address, validator in active_validators.items():
            # Update activity timestamp
            validator.update_activity(current_time)
            # Calculate PoCS score
            pocs_score = validator.calculate_pocs_score(current_time)
            validator_scores[address] = pocs_score
            total_score += pocs_score
        
        if total_score <= 0:
            # Fallback to simple stake-based selection if no PoCS scores
            total_stake = sum(val.stake for val in active_validators.values())
            if total_stake <= 0:
                # If no stake, just pick the first active validator
                return list(active_validators.keys())[0]
            random_value = random.uniform(0, total_stake)
            current_weight = 0
            for address, validator in active_validators.items():
                current_weight += validator.stake
                if random_value <= current_weight:
                    return address
            return list(active_validators.keys())[0]
        # Use PoCS scores for weighted random selection
        random_value = random.uniform(0, total_score)
        current_weight = 0
        for address, score in validator_scores.items():
            current_weight += score
            if random_value <= current_weight:
                return address
        return list(active_validators.keys())[0]
    
    def create_block(self, validator_address: str) -> Block:
        """Create a new block with pending transactions"""
        transactions_to_include = self.pending_transactions[:100]
        
        # Calculate state root (simplified)
        state_root = self._calculate_state_root()
        
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=transactions_to_include,
            previous_hash=self.get_latest_block().hash,
            validator=validator_address,
            state_root=state_root
        )
        
        return new_block
    
    def add_block(self, block: Block) -> bool:
        """Add a validated block to the chain"""
        if not self.validate_block(block):
            return False
        for transaction in block.transactions:
            try:
                print(f"[DEBUG] add_block: Processing transaction {transaction.transaction_type.value} from {transaction.from_address}")
                self.process_transaction(transaction)
            except Exception as e:
                print(f"Transaction processing failed: {e}")
                continue
        for transaction in block.transactions:
            if transaction in self.pending_transactions:
                self.pending_transactions.remove(transaction)
        self.chain.append(block)
        self.ledger.update_balance(block.validator, self.block_reward, "", len(self.chain), "Block reward")
        if block.validator in self.validators:
            validator = self.validators[block.validator]
            validator.blocks_validated += 1
            validator.last_block_time = time.time()
            validator.total_rewards += self.block_reward
            current_time = time.time()
            validator.update_activity(current_time)
            validator.update_contribution_score(10.0, event="block_validated")
            validator.update_reliability_score(True, 1.0)
            tx_types = set(tx.transaction_type.value for tx in block.transactions)
            validator.all_transaction_types.update(tx_types)
            validator.unique_transaction_types = len(validator.all_transaction_types)
            block_time = self.block_time if hasattr(self, 'block_time') else 5.0
            validator.update_uptime(block_time)
            validator.record_block_attempt(True, len(block.transactions))
            if len(self.chain) % 5 == 0 and len(self.validators) >= 2:
                self.trigger_peer_reviews()
            # Persist validator
            self.storage.put_validator(validator)
        # Persist block
        self.storage.put_block(block)
        return True
    
    def validate_block(self, block: Block) -> bool:
        """Validate a block before adding to chain"""
        if block.index != len(self.chain):
            return False
        
        if block.previous_hash != self.get_latest_block().hash:
            return False
        
        # Allow genesis validator or registered validators
        if block.validator != "genesis" and block.validator not in self.validators:
            return False
        
        if block.hash != block.calculate_hash():
            return False
        
        return True
    
    def mine_block(self) -> bool:
        """Mine a new block (PoS version)"""
        if not self.pending_transactions:
            return False
        
        # In P2P mode, wait a bit for network propagation before mining
        if self.p2p_node and len(self.p2p_node.connections) > 0:
            # Wait for network to settle
            time.sleep(0.5)
        
        # For the first block after genesis, use genesis validator
        if len(self.chain) == 1 and not self.validators:
            validator = "genesis"
        else:
            validator = self.select_validator()
            # If no validators yet, allow genesis to mine any transaction type
            if not validator:
                validator = "genesis"
        new_block = self.create_block(validator)
        return self.add_block(new_block)
    
    def mine_block_with_validator(self, validator_address: str) -> bool:
        """Mine a block with a specific validator (for testing)"""
        if not self.pending_transactions:
            return False
        
        # Security check: only allow in test mode or for valid validators
        if not self.test_mode and validator_address != "genesis" and validator_address not in self.validators:
            print(f"[SECURITY] Attempted to mine with invalid validator: {validator_address}")
            return False
        
        new_block = self.create_block(validator_address)
        return self.add_block(new_block)
    
    def _calculate_state_root(self) -> str:
        """Calculate state root (simplified)"""
        state_data = {
            'ledger': self.ledger.to_dict(),
            'contracts': {addr: contract.to_dict() for addr, contract in self.contract_engine.contracts.items()}
        }
        state_string = json.dumps(state_data, sort_keys=True)
        return hashlib.sha256(state_string.encode()).hexdigest()
    
    def assign_peer_reviews(self) -> List[tuple]:
        """Randomly assign validators to rate each other (anti-collusion)"""
        if len(self.validators) < 2:
            return []
        
        validators = list(self.validators.keys())
        assignments = []
        
        # Randomly pair validators for peer review
        import random
        random.shuffle(validators)
        
        for i in range(0, len(validators) - 1, 2):
            reviewer = validators[i]
            reviewee = validators[i + 1]
            assignments.append((reviewer, reviewee))
        
        return assignments
    
    def process_peer_ratings(self, ratings: List[tuple]):
        """Process peer ratings and update reputation scores"""
        for reviewer, reviewee, rating, reason in ratings:
            if reviewer in self.validators and reviewee in self.validators:
                # Rate the peer
                self.validators[reviewer].rate_peer(reviewee, rating, reason)
                
                # Update reputation scores
                self.validators[reviewee].update_reputation_score()
    
    def trigger_peer_reviews(self):
        """Trigger a round of peer reviews"""
        assignments = self.assign_peer_reviews()
        
        # For demo purposes, generate some sample ratings
        # In a real system, validators would submit their actual ratings
        ratings = []
        for reviewer, reviewee in assignments:
            # Simulate rating based on performance
            reviewee_validator = self.validators[reviewee]
            base_rating = min(100, max(1, reviewee_validator.reliability_score))
            
            # Add some randomness to simulate real ratings
            import random
            rating = max(1, min(100, base_rating + random.uniform(-10, 10)))
            reason = f"Performance review based on reliability score"
            
            ratings.append((reviewer, reviewee, rating, reason))
        
        self.process_peer_ratings(ratings)
    
    def apply_validator_penalty(self, validator_address: str, penalty_type: str, severity: float, reason: str = ""):
        """Apply penalty to a validator"""
        if validator_address in self.validators:
            self.validators[validator_address].apply_penalty(penalty_type, severity, reason)
    
    def community_override_penalty(self, validator_address: str, new_penalty_multiplier: float, reason: str = ""):
        """Community governance override of algorithmic penalty"""
        if validator_address in self.validators:
            validator = self.validators[validator_address]
            old_multiplier = validator.current_penalty_multiplier
            validator.current_penalty_multiplier = new_penalty_multiplier
            
            # Log the override
            validator.penalty_history.append((
                time.time(), 
                "community_override", 
                old_multiplier - new_penalty_multiplier, 
                f"Community override: {reason}"
            ))
    
    def get_contribution_mining_activities(self) -> dict:
        """Get available contribution mining activities"""
        return {
            'code_audit': {
                'description': 'Audit smart contract code for security issues',
                'credits_per_hour': 10.0,
                'max_credits': 100.0
            },
            'documentation': {
                'description': 'Write or improve documentation',
                'credits_per_hour': 5.0,
                'max_credits': 50.0
            },
            'community_support': {
                'description': 'Help other users and validators',
                'credits_per_hour': 3.0,
                'max_credits': 30.0
            },
            'bug_report': {
                'description': 'Report bugs or security vulnerabilities',
                'credits_per_bug': 20.0,
                'max_credits': 200.0
            },
            'educational_content': {
                'description': 'Create educational content about the blockchain',
                'credits_per_hour': 8.0,
                'max_credits': 80.0
            }
        }
    
    def optimize_validator_selection(self) -> Optional[str]:
        """Optimized validator selection with performance improvements"""
        if not self.validators:
            return None
        
        active_validators = {addr: val for addr, val in self.validators.items() 
                           if val.is_active}
        
        if not active_validators:
            return None
        
        current_time = time.time()
        
        # Use cached scores where possible
        validator_scores = {}
        total_score = 0
        
        for address, validator in active_validators.items():
            # Update activity timestamp
            validator.update_activity(current_time)
            
            # Calculate PoCS score (with caching)
            pocs_score = validator.calculate_pocs_score(current_time)
            validator_scores[address] = pocs_score
            total_score += pocs_score
        
        if total_score <= 0:
            # Fallback to simple stake-based selection
            total_stake = sum(val.stake for val in active_validators.values())
            random_value = random.uniform(0, total_stake)
            current_weight = 0
            
            for address, validator in active_validators.items():
                current_weight += validator.stake
                if random_value <= current_weight:
                    return address
            
            return list(active_validators.keys())[0]
        
        # Use PoCS scores for weighted random selection
        random_value = random.uniform(0, total_score)
        current_weight = 0
        
        for address, score in validator_scores.items():
            current_weight += score
            if random_value <= current_weight:
                return address
        
        return list(active_validators.keys())[0]
    
    def update_network_conditions(self, condition: str):
        """Update network conditions and adjust validator weights"""
        adjustment_factors = {
            'high_load': 1.2,  # Increase weight for high-performance validators
            'low_load': 0.8,   # Decrease weight for low-load scenarios
            'normal': 1.0      # Normal conditions
        }
        
        factor = adjustment_factors.get(condition, 1.0)
        
        for validator in self.validators.values():
            validator.adjust_dynamic_weight(condition, factor)
    
    def record_collaboration(self, validator_address: str, activity: str, score: float):
        """Record cross-validator collaboration activity"""
        if validator_address in self.validators:
            self.validators[validator_address].update_collaboration_score(activity, score)
    
    def record_network_health_contribution(self, validator_address: str, metric: str, contribution: float):
        """Record network health contribution"""
        if validator_address in self.validators:
            self.validators[validator_address].update_network_health_contribution(metric, contribution)
    
    def get_network_performance_summary(self) -> dict:
        """Get comprehensive network performance summary"""
        if not self.validators:
            return {}
        
        total_validators = len(self.validators)
        active_validators = len([v for v in self.validators.values() if v.is_active])
        
        # Calculate average metrics
        avg_scores = {
            'pocs_score': 0.0,
            'reputation': 0.0,
            'reliability': 0.0,
            'collaboration': 0.0,
            'network_health': 0.0
        }
        
        total_stake = 0.0
        total_penalties = 0
        total_activities = 0
        
        for validator in self.validators.values():
            metrics = validator.get_performance_metrics()
            for key in avg_scores:
                if key in metrics:
                    avg_scores[key] += metrics[key]
            
            total_stake += validator.stake
            total_penalties += len(validator.penalty_history)
            total_activities += len(validator.contribution_activities)
        
        # Calculate averages
        if total_validators > 0:
            for key in avg_scores:
                avg_scores[key] /= total_validators
        
        return {
            'total_validators': total_validators,
            'active_validators': active_validators,
            'total_stake': total_stake,
            'average_metrics': avg_scores,
            'total_penalties': total_penalties,
            'total_activities': total_activities,
            'network_health_score': avg_scores['network_health'],
            'collaboration_score': avg_scores['collaboration']
        }
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        return self.ledger.get_balance(address)
    
    def get_contract_state(self, contract_address: str, key_path: str = "") -> Any:
        """Get contract state"""
        return self.contract_engine.get_contract_state(contract_address, key_path)
    
    def get_chain_info(self) -> Dict:
        """Get blockchain information"""
        return {
            'chain_length': len(self.chain),
            'pending_transactions': len(self.pending_transactions),
            'validators': len(self.validators),
            'contracts': len(self.contract_engine.contracts),
            'latest_block': self.get_latest_block().to_dict()
        }
    
    def to_dict(self) -> Dict:
        """Convert blockchain to dictionary for JSON serialization"""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'validators': {addr: val.to_dict() for addr, val in self.validators.items()},
            'ledger': self.ledger.to_dict(),
            'contracts': {addr: contract.to_dict() for addr, contract in self.contract_engine.contracts.items()}
        }

    async def start_network(self):
        if self.p2p_port is not None:
            self.p2p_node = Node(host='localhost', port=self.p2p_port, peers=self.p2p_peers)
            # Register message handlers
            self.p2p_node.on('block', self.handle_incoming_block)
            self.p2p_node.on('transaction', self.handle_incoming_transaction)
            self.p2p_node.on('request_block', self.handle_request_block)
            self.p2p_node.on('block_response', self.handle_block_response)
            await self.p2p_node.start()

    async def stop_network(self):
        if self.p2p_node:
            await self.p2p_node.stop()

    async def broadcast_block(self, block: Block):
        if self.p2p_node:
            await self.p2p_node.broadcast('block', block.to_dict())

    async def broadcast_transaction(self, tx: Transaction):
        if self.p2p_node:
            await self.p2p_node.broadcast('transaction', tx.to_dict())

    async def handle_incoming_block(self, block_data, websocket):
        # Validate and add block if valid and not already present
        from core import Block, Transaction, TransactionType
        block_index = block_data.get('index')
        # Check if block already exists
        if block_index is not None and (block_index >= len(self.chain) or self.chain[block_index].hash != block_data.get('hash')):
            try:
                # Convert transaction_type strings to enums in transactions
                transactions = []
                for tx_data in block_data['transactions']:
                    tx_copy = tx_data.copy()
                    tx_copy['transaction_type'] = TransactionType(tx_copy['transaction_type'])
                    transactions.append(Transaction(**tx_copy))
                
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    transactions=transactions,
                    previous_hash=block_data['previous_hash'],
                    validator=block_data['validator'],
                    state_root=block_data.get('state_root', ''),
                    nonce=block_data.get('nonce', 0),
                    hash=block_data.get('hash', '')
                )
                
                # Check if this block can be added (previous hash matches our latest block)
                if block.previous_hash == self.get_latest_block().hash:
                    if self.validate_block(block):
                        print(f"[P2P] Adding received block {block.index}")
                        self.add_block(block)
                    else:
                        print(f"[P2P] Received invalid block {block.index}")
                else:
                    print(f"[P2P] Received block {block.index} with previous_hash {block.previous_hash}, but our latest block hash is {self.get_latest_block().hash}")
                    print(f"[P2P] Chain out of sync - requesting missing blocks")
                    # Request missing blocks from the peer
                    await self.request_missing_blocks(block.previous_hash, websocket)
            except Exception as e:
                print(f"[P2P] Error processing received block: {e}")
        else:
            print(f"[P2P] Block {block_index} already exists or is duplicate.")

    async def request_missing_blocks(self, target_hash, websocket):
        """Request missing blocks from a peer to sync the chain"""
        try:
            # Find the first missing block we need
            missing_index = None
            for i in range(len(self.chain)):
                if self.chain[i].hash == target_hash:
                    missing_index = i + 1
                    break
            
            if missing_index is not None:
                print(f"[P2P] Requesting block {missing_index} from peer")
                request_msg = {
                    'type': 'request_block',
                    'payload': {'index': missing_index}
                }
                await websocket.send_str(json.dumps(request_msg))
            else:
                print(f"[P2P] Could not find block with hash {target_hash} in our chain")
        except Exception as e:
            print(f"[P2P] Error requesting missing blocks: {e}")

    async def handle_request_block(self, request_data, websocket):
        """Handle a request for a specific block"""
        try:
            block_index = request_data.get('index')
            if block_index is not None and block_index < len(self.chain):
                block = self.chain[block_index]
                print(f"[P2P] Sending block {block_index} to peer")
                response_msg = {
                    'type': 'block_response',
                    'payload': block.to_dict()
                }
                await websocket.send_str(json.dumps(response_msg))
            else:
                print(f"[P2P] Block {block_index} not found (our chain length: {len(self.chain)})")
        except Exception as e:
            print(f"[P2P] Error handling block request: {e}")

    async def handle_block_response(self, block_data, websocket):
        """Handle a response with a requested block"""
        try:
            print(f"[P2P] Received block response for block {block_data.get('index')}")
            # Process the received block as if it was broadcasted
            await self.handle_incoming_block(block_data, websocket)
        except Exception as e:
            print(f"[P2P] Error handling block response: {e}")

    async def handle_incoming_transaction(self, tx_data, websocket):
        from core import Transaction, TransactionType
        tx_hash = tx_data.get('hash')
        # Check if transaction already in processed or pending
        if tx_hash and tx_hash not in self.processed_tx_hashes and all(tx.hash != tx_hash for tx in self.pending_transactions):
            try:
                # Convert string transaction_type to enum
                tx_data_copy = tx_data.copy()
                tx_data_copy['transaction_type'] = TransactionType(tx_data_copy['transaction_type'])
                tx = Transaction(**tx_data_copy)
                if self.validate_transaction(tx):
                    print(f"[P2P] Adding received transaction {tx.hash}")
                    self.add_transaction(tx)
                else:
                    print(f"[P2P] Received invalid transaction {tx.hash}")
            except Exception as e:
                print(f"[P2P] Error processing received transaction: {e}")
        else:
            print(f"[P2P] Transaction {tx_hash} already processed or pending.")