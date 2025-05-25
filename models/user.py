"""
User model for the Telegram Escrow Bot.
Represents registered users with their details and preferences.
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class User:
    """
    Represents a registered user in the escrow system.
    
    Attributes:
        id: Telegram user ID (primary key)
        username: Telegram username
        first_name: User's first name
        last_name: User's last name
        created_at: Timestamp when the user was created
        payment_methods: Dictionary of user's payment methods
        transactions: List of transaction IDs associated with the user
        feedback: Dictionary of feedback received
        trusted_by: List of users who trust this user
        is_active: Flag to indicate if the user is active
    """
    id: int
    username: str
    first_name: str
    last_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    payment_methods: Dict = field(default_factory=dict)
    transactions: List[str] = field(default_factory=list)
    feedback: Dict = field(default_factory=dict)
    trusted_by: List[int] = field(default_factory=list)
    is_active: bool = True
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self) -> str:
        """Get the user's display name (username or full name)."""
        return f"@{self.username}" if self.username else self.full_name
    
    @property
    def transaction_count(self) -> int:
        """Get the number of transactions for this user."""
        return len(self.transactions)
