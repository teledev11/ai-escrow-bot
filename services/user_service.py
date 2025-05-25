"""
User service for the Telegram Escrow Bot.
Manages user data and provides user-related functionality.
Uses PostgreSQL database for persistent storage.
"""
import logging
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.user import User as UserModel
from db_models import User as DbUser, Wallet, get_db_session

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing users with database persistence."""
    
    def __init__(self):
        """Initialize the user service with database connection."""
        self.db = get_db_session()
    
    def get_user(self, user_id: int) -> Optional[UserModel]:
        """
        Get a user by their ID from the database.
        
        Args:
            user_id: User's Telegram ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            db_user = self.db.query(DbUser).filter(DbUser.id == user_id).first()
            if not db_user:
                return None
            
            # Convert DB user to model user (using attribute values, not column objects)
            return UserModel(
                id=int(db_user.id),
                username=str(db_user.username),
                first_name=str(db_user.first_name),
                last_name=str(db_user.last_name) if db_user.last_name else "",
                created_at=db_user.created_at.isoformat() if db_user.created_at else None,
                is_active=bool(db_user.is_active)
            )
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def register_user(self, user: UserModel) -> bool:
        """
        Register a new user in the database.
        
        Args:
            user: User object to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Check if user is missing a username
            if not user.username:
                logger.warning(f"Cannot register user {user.id} without a username.")
                return False

            # Create a new session for registration to avoid session conflicts
            self.db = get_db_session()
                
            # Check if user already exists
            existing_user = self.db.query(DbUser).filter(DbUser.id == user.id).first()
            if existing_user:
                logger.warning(f"User {user.id} already exists.")
                # If the user exists, treat it as a success since they're already registered
                return True
            
            # Create new user in database with error handling for each field
            try:
                # Ensure numeric user ID
                user_id = int(user.id)
                
                # Validate username is not blank
                if not user.username or len(user.username.strip()) == 0:
                    raise ValueError("Username cannot be blank")
                
                # Create user record
                db_user = DbUser(
                    id=user_id,
                    username=user.username,
                    first_name=user.first_name or "User",  # Default if missing
                    last_name=user.last_name or ""
                )
                self.db.add(db_user)
                
                # Create wallet for the user
                wallet = Wallet(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    balance=0.0
                )
                self.db.add(wallet)
                
                # Commit changes
                self.db.commit()
                
                logger.info(f"User {user_id} registered successfully.")
                return True
                
            except ValueError as ve:
                self.db.rollback()
                logger.error(f"Value error registering user: {ve}")
                return False
                
        except SQLAlchemyError as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Database error registering user: {e}")
            return False
        except Exception as e:
            if self.db:
                self.db.rollback()
            logger.error(f"Error registering user: {e}")
            return False
        finally:
            if self.db:
                self.db.close()
    
    def update_user(self, user: UserModel) -> bool:
        """
        Update an existing user in the database.
        
        Args:
            user: User object with updated information
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get existing user
            db_user = self.db.query(DbUser).filter(DbUser.id == user.id).first()
            if not db_user:
                logger.warning(f"User {user.id} does not exist.")
                return False
            
            # Update user fields
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.is_active = user.is_active
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"User {user.id} updated successfully.")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating user: {e}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            return False
    
    def add_transaction_to_user(self, user_id: int, transaction_id: str) -> bool:
        """
        Add a transaction ID to a user's transactions list.
        Note: This is handled by database relations now
        
        Args:
            user_id: User's Telegram ID
            transaction_id: Transaction ID to add
            
        Returns:
            True if user exists, False otherwise
        """
        # With proper database relations, we don't need to manually
        # add transaction IDs to a user's list. We just need to verify
        # the user exists.
        user = self.get_user(user_id)
        return user is not None
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a user from the database.
        
        Args:
            user_id: User's Telegram ID
            
        Returns:
            Dictionary containing user statistics
        """
        try:
            from db_models import Transaction, Wallet
            
            stats = {
                'total_transactions': 0,
                'as_buyer': 0,
                'as_seller': 0,
                'completed': 0,
                'active': 0,
                'disputed': 0,
                'escrow_balance': 0.0
            }
            
            # Check if user exists
            db_user = self.db.query(DbUser).filter(DbUser.id == user_id).first()
            if not db_user:
                return stats
            
            # Count transactions
            seller_txns = self.db.query(Transaction).filter(Transaction.seller_id == user_id).all()
            buyer_txns = self.db.query(Transaction).filter(Transaction.buyer_id == user_id).all()
            
            stats['as_seller'] = len(seller_txns)
            stats['as_buyer'] = len(buyer_txns)
            stats['total_transactions'] = stats['as_seller'] + stats['as_buyer']
            
            # Count by status
            all_txns = seller_txns + buyer_txns
            stats['completed'] = sum(1 for txn in all_txns if txn.status == 'completed')
            stats['disputed'] = sum(1 for txn in all_txns if txn.status == 'disputed')
            stats['active'] = sum(1 for txn in all_txns if txn.status in ['created', 'funded', 'confirmed'])
            
            # Get wallet balance
            wallet = self.db.query(Wallet).filter(Wallet.user_id == user_id).first()
            if wallet:
                stats['escrow_balance'] = wallet.balance
            
            return stats
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                'total_transactions': 0,
                'as_buyer': 0,
                'as_seller': 0,
                'completed': 0,
                'active': 0,
                'disputed': 0,
                'escrow_balance': 0.0
            }
