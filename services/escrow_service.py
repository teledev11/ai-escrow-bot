"""
Escrow service for the Telegram Escrow Bot.
Manages transactions, disputes, and escrow functionality.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.transaction import Transaction
from models.wallet import Wallet, WalletTransaction
from services.user_service import UserService
from config import TransactionStatus, DisputeStatus

logger = logging.getLogger(__name__)

class EscrowService:
    """Service for managing escrow transactions and wallets."""
    
    def __init__(self):
        """Initialize the escrow service with in-memory storage."""
        self.transactions: Dict[str, Transaction] = {}
        self.wallets: Dict[int, Wallet] = {}
        self.disputes: Dict[str, Dict[str, Any]] = {}
        self.user_service = UserService()
    
    def create_transaction(self, transaction: Transaction) -> bool:
        """
        Create a new transaction.
        
        Args:
            transaction: Transaction object to create
            
        Returns:
            True if creation was successful, False otherwise
        """
        try:
            if transaction.id in self.transactions:
                logger.warning(f"Transaction {transaction.id} already exists.")
                return False
            
            # Save the transaction
            self.transactions[transaction.id] = transaction
            
            # Add transaction to seller's list
            self.user_service.add_transaction_to_user(transaction.seller_id, transaction.id)
            
            logger.info(f"Transaction {transaction.id} created successfully.")
            return True
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return False
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Get a transaction by its ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction object if found, None otherwise
        """
        return self.transactions.get(transaction_id)
    
    def update_transaction(self, transaction: Transaction) -> bool:
        """
        Update an existing transaction.
        
        Args:
            transaction: Transaction object with updated information
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            if transaction.id not in self.transactions:
                logger.warning(f"Transaction {transaction.id} does not exist.")
                return False
            
            # Update timestamp
            transaction.updated_at = datetime.now()
            
            # Save the updated transaction
            self.transactions[transaction.id] = transaction
            
            # If there's a buyer and they're not already associated with the transaction
            if transaction.buyer_id and transaction.id not in self.user_service.get_user(transaction.buyer_id).transactions:
                self.user_service.add_transaction_to_user(transaction.buyer_id, transaction.id)
            
            logger.info(f"Transaction {transaction.id} updated successfully.")
            return True
        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            return False
    
    def get_user_transactions(self, user_id: int) -> List[Transaction]:
        """
        Get all transactions for a user.
        
        Args:
            user_id: User's Telegram ID
            
        Returns:
            List of transactions where the user is either buyer or seller
        """
        user_transactions = []
        
        for txn in self.transactions.values():
            if txn.seller_id == user_id or txn.buyer_id == user_id:
                user_transactions.append(txn)
        
        # Sort by created_at, newest first
        user_transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_transactions
    
    def cancel_transaction(self, transaction_id: str, user_id: int) -> bool:
        """
        Cancel a transaction.
        
        Args:
            transaction_id: Transaction ID
            user_id: User's Telegram ID initiating the cancellation
            
        Returns:
            True if cancellation was successful, False otherwise
        """
        transaction = self.get_transaction(transaction_id)
        
        if not transaction:
            logger.warning(f"Transaction {transaction_id} not found.")
            return False
        
        # Check if user is authorized to cancel
        if user_id != transaction.seller_id and user_id != transaction.buyer_id:
            logger.warning(f"User {user_id} not authorized to cancel transaction {transaction_id}.")
            return False
        
        # Check if transaction can be cancelled
        if transaction.status != TransactionStatus.CREATED:
            logger.warning(f"Transaction {transaction_id} cannot be cancelled in {transaction.status} status.")
            return False
        
        # Update transaction status
        transaction.status = TransactionStatus.CANCELLED
        transaction.updated_at = datetime.now()
        
        return self.update_transaction(transaction)
    
    def confirm_transaction(self, transaction_id: str, user_id: int) -> bool:
        """
        Seller confirms receipt of payment.
        
        Args:
            transaction_id: Transaction ID
            user_id: User's Telegram ID (should be the seller)
            
        Returns:
            True if confirmation was successful, False otherwise
        """
        transaction = self.get_transaction(transaction_id)
        
        if not transaction:
            logger.warning(f"Transaction {transaction_id} not found.")
            return False
        
        # Check if user is the seller
        if user_id != transaction.seller_id:
            logger.warning(f"User {user_id} is not the seller for transaction {transaction_id}.")
            return False
        
        # Check if transaction is in the right state
        if transaction.status != TransactionStatus.FUNDED:
            logger.warning(f"Transaction {transaction_id} cannot be confirmed in {transaction.status} status.")
            return False
        
        # Update transaction status
        transaction.status = TransactionStatus.CONFIRMED
        transaction.updated_at = datetime.now()
        
        return self.update_transaction(transaction)
    
    def complete_transaction(self, transaction_id: str, user_id: int) -> bool:
        """
        Complete a transaction, releasing funds to the seller.
        
        Args:
            transaction_id: Transaction ID
            user_id: User's Telegram ID (should be the buyer)
            
        Returns:
            True if completion was successful, False otherwise
        """
        transaction = self.get_transaction(transaction_id)
        
        if not transaction:
            logger.warning(f"Transaction {transaction_id} not found.")
            return False
        
        # Check if user is the buyer
        if user_id != transaction.buyer_id:
            logger.warning(f"User {user_id} is not the buyer for transaction {transaction_id}.")
            return False
        
        # Check if transaction is in the right state
        if transaction.status != TransactionStatus.CONFIRMED:
            logger.warning(f"Transaction {transaction_id} cannot be completed in {transaction.status} status.")
            return False
        
        # Update transaction status
        transaction.status = TransactionStatus.COMPLETED
        transaction.updated_at = datetime.now()
        transaction.completed_at = datetime.now()
        
        # In a real implementation, this would trigger the escrow release logic
        # For this demo, we'll just update the transaction status
        
        return self.update_transaction(transaction)
    
    def get_user_wallet(self, user_id: int) -> Optional[Wallet]:
        """
        Get a user's wallet, creating one if it doesn't exist.
        
        Args:
            user_id: User's Telegram ID
            
        Returns:
            Wallet object
        """
        if user_id not in self.wallets:
            # Create a new wallet for the user
            wallet_id = str(uuid.uuid4())
            self.wallets[user_id] = Wallet(id=wallet_id, user_id=user_id)
        
        return self.wallets.get(user_id)
    
    def open_dispute(self, transaction_id: str, user_id: int, reason: str, evidence: str) -> bool:
        """
        Open a dispute for a transaction.
        
        Args:
            transaction_id: Transaction ID
            user_id: User's Telegram ID opening the dispute
            reason: Reason for the dispute
            evidence: Evidence supporting the dispute
            
        Returns:
            True if dispute was opened successfully, False otherwise
        """
        transaction = self.get_transaction(transaction_id)
        
        if not transaction:
            logger.warning(f"Transaction {transaction_id} not found.")
            return False
        
        # Check if user is part of the transaction
        if user_id != transaction.seller_id and user_id != transaction.buyer_id:
            logger.warning(f"User {user_id} not authorized to open dispute for transaction {transaction_id}.")
            return False
        
        # Check if transaction is in a state that can be disputed
        if transaction.status not in [TransactionStatus.FUNDED, TransactionStatus.CONFIRMED]:
            logger.warning(f"Transaction {transaction_id} cannot be disputed in {transaction.status} status.")
            return False
        
        # Check if there's already a dispute
        if transaction_id in self.disputes:
            logger.warning(f"Dispute already exists for transaction {transaction_id}.")
            return False
        
        # Determine the opener's role
        opener_role = "seller" if user_id == transaction.seller_id else "buyer"
        
        # Create the dispute
        dispute = {
            'transaction_id': transaction_id,
            'opened_by': opener_role,
            'reason': reason,
            'evidence': evidence,
            'response': None,
            'status': DisputeStatus.OPEN,
            'resolution': None,
            'opened_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'resolved_at': None
        }
        
        self.disputes[transaction_id] = dispute
        
        # Update transaction status
        transaction.status = TransactionStatus.DISPUTED
        transaction.updated_at = datetime.now()
        transaction.dispute = {'status': DisputeStatus.OPEN}
        
        self.update_transaction(transaction)
        
        logger.info(f"Dispute opened for transaction {transaction_id}.")
        return True
    
    def get_dispute(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a dispute by transaction ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Dispute dictionary if found, None otherwise
        """
        return self.disputes.get(transaction_id)
    
    def resolve_dispute(self, transaction_id: str, resolution: str) -> bool:
        """
        Resolve a dispute for a transaction.
        
        Args:
            transaction_id: Transaction ID
            resolution: Resolution outcome ('buyer', 'seller', or 'refund')
            
        Returns:
            True if resolution was successful, False otherwise
        """
        transaction = self.get_transaction(transaction_id)
        dispute = self.get_dispute(transaction_id)
        
        if not transaction or not dispute:
            logger.warning(f"Transaction or dispute not found for ID {transaction_id}.")
            return False
        
        if dispute['status'] != DisputeStatus.OPEN:
            logger.warning(f"Dispute for transaction {transaction_id} is not open.")
            return False
        
        # Update dispute
        dispute['status'] = DisputeStatus.RESOLVED
        dispute['resolution'] = resolution
        dispute['resolved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update transaction status based on resolution
        if resolution == 'buyer':
            # Return funds to buyer
            transaction.status = TransactionStatus.REFUNDED
        elif resolution == 'seller':
            # Release funds to seller
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
        else:  # 'refund'
            # Partial refund/negotiated solution
            transaction.status = TransactionStatus.REFUNDED
        
        transaction.updated_at = datetime.now()
        transaction.dispute = {'status': DisputeStatus.RESOLVED, 'resolution': resolution}
        
        self.update_transaction(transaction)
        
        logger.info(f"Dispute resolved for transaction {transaction_id} with outcome: {resolution}.")
        return True
