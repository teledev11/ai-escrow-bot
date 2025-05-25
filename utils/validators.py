"""
Validation utilities for the Telegram Escrow Bot.
Provides validation functions to ensure data integrity.
"""
import logging
import re
from typing import Optional, Dict, Any, Tuple, Union
from datetime import datetime

from config import (
    MIN_TRANSACTION_AMOUNT, 
    MAX_TRANSACTION_AMOUNT, 
    SUPPORTED_FIAT_METHODS,
    SUPPORTED_CRYPTO_METHODS,
    TransactionStatus,
    UserRole
)

logger = logging.getLogger(__name__)

def validate_transaction_amount(amount: Union[str, float]) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate a transaction amount.
    
    Args:
        amount: Amount to validate, can be string or float
        
    Returns:
        Tuple (is_valid, parsed_amount, error_message)
    """
    try:
        # Convert to float if string
        if isinstance(amount, str):
            amount = float(amount.strip())
        
        # Check if it's a positive number
        if amount <= 0:
            return False, None, "Amount must be a positive number"
        
        # Check min/max bounds
        if amount < MIN_TRANSACTION_AMOUNT:
            return False, None, f"Amount must be at least {MIN_TRANSACTION_AMOUNT}"
        
        if amount > MAX_TRANSACTION_AMOUNT:
            return False, None, f"Amount cannot exceed {MAX_TRANSACTION_AMOUNT}"
        
        return True, amount, None
    except ValueError:
        return False, None, "Invalid amount format. Please enter a numeric value."
    except Exception as e:
        logger.error(f"Error validating amount: {e}")
        return False, None, "An error occurred while validating the amount"

def validate_payment_method(method: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a payment method.
    
    Args:
        method: Payment method to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    # Convert to lowercase and normalize
    normalized_method = method.lower().replace(' ', '_')
    
    # Check against supported methods
    for fiat_method in SUPPORTED_FIAT_METHODS:
        if fiat_method.lower().replace(' ', '_') == normalized_method:
            return True, None
    
    for crypto_method in SUPPORTED_CRYPTO_METHODS:
        if crypto_method.lower() == normalized_method:
            return True, None
    
    return False, f"Unsupported payment method. Please choose from: {', '.join(SUPPORTED_FIAT_METHODS + SUPPORTED_CRYPTO_METHODS)}"

def validate_transaction_status_transition(current_status: str, new_status: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a transaction status transition.
    
    Args:
        current_status: Current transaction status
        new_status: New transaction status
        
    Returns:
        Tuple (is_valid, error_message)
    """
    # Define valid transitions
    valid_transitions = {
        TransactionStatus.CREATED: [TransactionStatus.FUNDED, TransactionStatus.CANCELLED],
        TransactionStatus.FUNDED: [TransactionStatus.CONFIRMED, TransactionStatus.DISPUTED, TransactionStatus.REFUNDED],
        TransactionStatus.CONFIRMED: [TransactionStatus.COMPLETED, TransactionStatus.DISPUTED],
        TransactionStatus.DISPUTED: [TransactionStatus.COMPLETED, TransactionStatus.REFUNDED, TransactionStatus.CANCELLED],
        TransactionStatus.COMPLETED: [],  # Terminal state
        TransactionStatus.REFUNDED: [],   # Terminal state
        TransactionStatus.CANCELLED: []   # Terminal state
    }
    
    if new_status in valid_transitions.get(current_status, []):
        return True, None
    
    return False, f"Invalid status transition from '{current_status}' to '{new_status}'"

def validate_crypto_address(crypto_type: str, address: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a cryptocurrency address format.
    
    Args:
        crypto_type: Type of cryptocurrency
        address: Address to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    # Basic validation patterns for common cryptocurrencies
    validation_patterns = {
        'bitcoin': r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$',
        'ethereum': r'^0x[a-fA-F0-9]{40}$',
        'litecoin': r'^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$',
        'usdt': r'^0x[a-fA-F0-9]{40}$|^T[a-zA-Z0-9]{33}$'  # ERC-20 or TRC-20
    }
    
    # Normalize crypto type
    crypto_type = crypto_type.lower()
    
    # Get the appropriate pattern
    pattern = validation_patterns.get(crypto_type)
    
    if not pattern:
        # For unsupported types, just check if it's not empty and has a reasonable length
        if len(address.strip()) < 10:
            return False, "Address is too short"
        return True, None
    
    # Check against the pattern
    if re.match(pattern, address):
        return True, None
    
    return False, f"Invalid {crypto_type} address format"

def validate_user_input(text: str, min_length: int = 1, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """
    Validate user input for general text fields.
    
    Args:
        text: Text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not text or len(text.strip()) < min_length:
        return False, f"Text must be at least {min_length} characters long"
    
    if len(text.strip()) > max_length:
        return False, f"Text cannot exceed {max_length} characters"
    
    return True, None

def validate_transaction_id(transaction_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a transaction ID format.
    
    Args:
        transaction_id: Transaction ID to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    # Check if it's alphanumeric and has the right length
    if not re.match(r'^[a-zA-Z0-9-]{4,36}$', transaction_id):
        return False, "Invalid transaction ID format"
    
    return True, None

def validate_dispute_resolution(resolution: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a dispute resolution.
    
    Args:
        resolution: Resolution to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    valid_resolutions = ['buyer', 'seller', 'refund']
    
    if resolution.lower() not in valid_resolutions:
        return False, f"Invalid resolution. Must be one of: {', '.join(valid_resolutions)}"
    
    return True, None

def validate_user_role(role: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a user role.
    
    Args:
        role: Role to validate
        
    Returns:
        Tuple (is_valid, error_message)
    """
    valid_roles = [UserRole.BUYER, UserRole.SELLER, UserRole.ADMIN]
    
    if role.lower() not in [r.lower() for r in valid_roles]:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    return True, None

def validate_date_format(date_str: str, format_str: str = '%Y-%m-%d') -> Tuple[bool, Optional[datetime], Optional[str]]:
    """
    Validate a date string format.
    
    Args:
        date_str: Date string to validate
        format_str: Expected date format
        
    Returns:
        Tuple (is_valid, parsed_date, error_message)
    """
    try:
        parsed_date = datetime.strptime(date_str, format_str)
        return True, parsed_date, None
    except ValueError:
        return False, None, f"Invalid date format. Expected format: {format_str}"
    except Exception as e:
        logger.error(f"Error validating date: {e}")
        return False, None, "An error occurred while validating the date"
