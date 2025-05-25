"""
Transaction model for the Telegram Escrow Bot.
Represents escrow transactions between buyers and sellers.
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from config import TransactionStatus

@dataclass
class Transaction:
    """
    Represents an escrow transaction between a buyer and a seller.
    
    Attributes:
        id: Unique transaction ID
        title: Short title describing the transaction
        description: Detailed description of goods/services
        amount: Transaction amount (excluding fees)
        fee: Escrow service fee
        payment_method: Method of payment (bank, paypal, bitcoin, etc.)
        seller_id: Telegram ID of the seller
        seller_username: Telegram username of the seller
        buyer_id: Telegram ID of the buyer (optional until joined)
        buyer_username: Telegram username of the buyer (optional until joined)
        status: Current status of the transaction
        created_at: Timestamp when the transaction was created
        updated_at: Timestamp when the transaction was last updated
        completed_at: Timestamp when the transaction was completed
        metadata: Additional metadata for the transaction
        dispute: Dispute information if a dispute is raised
    """
    id: str
    title: str
    description: str
    amount: float
    fee: float
    payment_method: str
    seller_id: int
    seller_username: str
    buyer_id: Optional[int] = None
    buyer_username: Optional[str] = None
    status: str = TransactionStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dispute: Optional[Dict[str, Any]] = None
    
    @property
    def total_amount(self) -> float:
        """Get the total amount including fees."""
        return self.amount + self.fee
    
    @property
    def is_active(self) -> bool:
        """Check if the transaction is in an active state."""
        return self.status in [
            TransactionStatus.CREATED,
            TransactionStatus.FUNDED,
            TransactionStatus.CONFIRMED
        ]
    
    @property
    def is_disputed(self) -> bool:
        """Check if the transaction is in disputed state."""
        return self.status == TransactionStatus.DISPUTED
    
    @property
    def is_complete(self) -> bool:
        """Check if the transaction is complete."""
        return self.status == TransactionStatus.COMPLETED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if the transaction is cancelled."""
        return self.status == TransactionStatus.CANCELLED
