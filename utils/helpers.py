"""
Helper utilities for the Telegram Escrow Bot.
Provides common helper functions used across the application.
"""
import logging
from typing import Dict, Any
import json
import os
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def format_currency(amount: float) -> str:
    """
    Format a currency amount with appropriate precision.
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string
    """
    return f"${amount:.2f}"

def calculate_fee(amount: float, percentage: float) -> float:
    """
    Calculate fee based on amount and percentage.
    
    Args:
        amount: Base amount
        percentage: Fee percentage
        
    Returns:
        Calculated fee amount
    """
    return (amount * percentage) / 100

def generate_short_id() -> str:
    """
    Generate a short unique identifier.
    
    Returns:
        Short unique ID string
    """
    import uuid
    return str(uuid.uuid4())[:8]

def is_expired(timestamp: datetime, days: int) -> bool:
    """
    Check if a timestamp is expired after a certain number of days.
    
    Args:
        timestamp: Datetime to check
        days: Number of days for expiration
        
    Returns:
        True if expired, False otherwise
    """
    expiration = timestamp + timedelta(days=days)
    return datetime.now() > expiration

def safe_json_dump(data: Dict[str, Any], filepath: str) -> bool:
    """
    Safely dump data to a JSON file.
    
    Args:
        data: Data to dump
        filepath: Path to the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w') as file:
            json.dump(data, file, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filepath}: {e}")
        return False

def safe_json_load(filepath: str) -> Dict[str, Any]:
    """
    Safely load data from a JSON file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Loaded data or empty dict if error
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                return json.load(file)
        return {}
    except Exception as e:
        logger.error(f"Error loading data from {filepath}: {e}")
        return {}

def retry_operation(func, max_retries=3, delay=1):
    """
    Retry an operation multiple times with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Initial delay in seconds
        
    Returns:
        Result of the function or None if all retries failed
    """
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            retries += 1
            if retries == max_retries:
                logger.error(f"Operation failed after {max_retries} retries: {e}")
                return None
            wait_time = delay * (2 ** (retries - 1))
            logger.warning(f"Retry {retries}/{max_retries} after {wait_time}s: {e}")
            time.sleep(wait_time)
