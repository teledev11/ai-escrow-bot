"""
Payment service for the Telegram Escrow Bot.
Manages payment methods and verification.
"""
import logging
from typing import Dict, List, Optional, Any

from services.user_service import UserService
from services.escrow_service import EscrowService

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for managing payments and payment methods."""
    
    def __init__(self):
        """Initialize the payment service."""
        self.user_service = UserService()
        self.escrow_service = EscrowService()
        self.payment_methods: Dict[int, List[Dict[str, Any]]] = {}
    
    def add_payment_method(self, method_data: Dict[str, Any]) -> bool:
        """
        Add a payment method for a user.
        
        Args:
            method_data: Dictionary containing payment method details
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            user_id = method_data['user_id']
            
            # Check if user exists
            if not self.user_service.get_user(user_id):
                logger.warning(f"User {user_id} does not exist.")
                return False
            
            # Initialize payment methods list for user if it doesn't exist
            if user_id not in self.payment_methods:
                self.payment_methods[user_id] = []
            
            # Format the payment method
            payment_method = {
                'name': method_data['name'],
                'type': method_data['type']
            }
            
            if method_data['type'] == 'fiat':
                payment_method['details'] = method_data['details']
            else:
                payment_method['address'] = method_data['address']
            
            # Add the payment method
            self.payment_methods[user_id].append(payment_method)
            logger.info(f"Payment method added for user {user_id}.")
            return True
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            return False
    
    def get_user_payment_methods(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all payment methods for a user.
        
        Args:
            user_id: User's Telegram ID
            
        Returns:
            List of payment method dictionaries
        """
        return self.payment_methods.get(user_id, [])
    
    def get_payment_method_by_name(self, user_id: int, method_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific payment method by name for a user.
        
        Args:
            user_id: User's Telegram ID
            method_name: Name of the payment method
            
        Returns:
            Payment method dictionary if found, None otherwise
        """
        methods = self.get_user_payment_methods(user_id)
        
        for method in methods:
            if method['name'].lower() == method_name.lower().replace('_', ' '):
                return method
        
        return None
    
    def confirm_payment_sent(self, transaction_id: str, user_id: int) -> bool:
        """
        Confirm that payment has been sent for a transaction.
        
        Args:
            transaction_id: Transaction ID
            user_id: User's Telegram ID (should be the buyer)
            
        Returns:
            True if confirmation was successful, False otherwise
        """
        transaction = self.escrow_service.get_transaction(transaction_id)
        
        if not transaction:
            logger.warning(f"Transaction {transaction_id} not found.")
            return False
        
        # Check if user is the buyer
        if user_id != transaction.buyer_id:
            logger.warning(f"User {user_id} is not the buyer for transaction {transaction_id}.")
            return False
        
        # In a real implementation, this would track the payment confirmation
        # For this demo, we'll just return True
        logger.info(f"Payment confirmation recorded for transaction {transaction_id}.")
        return True
    
    def verify_payment(self, transaction_id: str, payment_data: Dict[str, Any]) -> bool:
        """
        Verify a payment for a transaction.
        
        Args:
            transaction_id: Transaction ID
            payment_data: Payment verification data
            
        Returns:
            True if verification was successful, False otherwise
        """
        # In a real implementation, this would verify payment details
        # For this demo, we'll just return True
        logger.info(f"Payment verified for transaction {transaction_id}.")
        return True
