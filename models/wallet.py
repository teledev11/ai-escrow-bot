"""
Wallet model for the Telegram Escrow Bot.
Represents escrow wallet for handling funds.
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class WalletTransaction:
    """
    Represents a transaction in a wallet.
    
    Attributes:
        id: Unique transaction ID
        transaction_id: Associated escrow transaction ID
        amount: Amount of the transaction
        direction: 'in' or 'out'
        type: Type of transaction (deposit, withdrawal, fee, etc.)
        created_at: Timestamp when the wallet transaction occurred
        metadata: Additional metadata for the wallet transaction
    """
    id: str
    transaction_id: str
    amount: float
    direction: str  # 'in' or 'out'
    type: str  # 'deposit', 'withdrawal', 'fee', etc.
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

@dataclass
class Wallet:
    """
    Represents an escrow wallet.
    
    Attributes:
        id: Unique wallet ID
        user_id: Associated user ID
        balance: Current balance
        transactions: List of wallet transactions
        created_at: Timestamp when the wallet was created
        updated_at: Timestamp when the wallet was last updated
    """
    id: str
    user_id: int
    balance: float = 0.0
    transactions: List[WalletTransaction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def deposit(self, amount: float, transaction_id: str, transaction_type: str) -> WalletTransaction:
        """
        Deposit funds into the wallet.
        
        Args:
            amount: Amount to deposit
            transaction_id: Associated escrow transaction ID
            transaction_type: Type of transaction
            
        Returns:
            The created wallet transaction
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        self.balance += amount
        self.updated_at = datetime.now()
        
        wallet_tx = WalletTransaction(
            id=f"wtx_{len(self.transactions) + 1}",
            transaction_id=transaction_id,
            amount=amount,
            direction="in",
            type=transaction_type
        )
        
        self.transactions.append(wallet_tx)
        return wallet_tx
    
    def withdraw(self, amount: float, transaction_id: str, transaction_type: str) -> WalletTransaction:
        """
        Withdraw funds from the wallet.
        
        Args:
            amount: Amount to withdraw
            transaction_id: Associated escrow transaction ID
            transaction_type: Type of transaction
            
        Returns:
            The created wallet transaction
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        
        self.balance -= amount
        self.updated_at = datetime.now()
        
        wallet_tx = WalletTransaction(
            id=f"wtx_{len(self.transactions) + 1}",
            transaction_id=transaction_id,
            amount=amount,
            direction="out",
            type=transaction_type
        )
        
        self.transactions.append(wallet_tx)
        return wallet_tx
