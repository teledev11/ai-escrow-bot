#!/usr/bin/env python3
"""
Database reset script to fix the Telegram user ID issue.
This will completely recreate all tables with correct BigInteger fields.
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database completely with correct schema."""
    try:
        # Get database URL
        DB_URL = os.environ.get('DATABASE_URL', '')
        if not DB_URL:
            raise ValueError("DATABASE_URL environment variable is not set!")
            
        # Ensure the PostgreSQL URL is in the correct format for SQLAlchemy
        if DB_URL.startswith("postgres://"):
            DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)
        
        with engine.connect() as connection:
            # Drop all existing tables
            logger.info("Dropping all existing tables...")
            connection.execute(text("DROP TABLE IF EXISTS wallet_transactions CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS wallets CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS disputes CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS transactions CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS payment_methods CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            connection.commit()
            
            # Create users table with BigInteger ID
            logger.info("Creating users table with BigInteger ID...")
            connection.execute(text("""
                CREATE TABLE users (
                    id BIGINT PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    first_name VARCHAR(64) NOT NULL,
                    last_name VARCHAR(64),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """))
            
            # Create payment_methods table
            logger.info("Creating payment_methods table...")
            connection.execute(text("""
                CREATE TABLE payment_methods (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id),
                    name VARCHAR(64) NOT NULL,
                    type VARCHAR(16) NOT NULL,
                    details TEXT,
                    address VARCHAR(128),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create transactions table
            logger.info("Creating transactions table...")
            connection.execute(text("""
                CREATE TABLE transactions (
                    id VARCHAR(16) PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    description TEXT NOT NULL,
                    amount FLOAT NOT NULL,
                    fee FLOAT NOT NULL,
                    payment_method VARCHAR(64) NOT NULL,
                    seller_id BIGINT NOT NULL REFERENCES users(id),
                    buyer_id BIGINT REFERENCES users(id),
                    status VARCHAR(16) NOT NULL DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    transaction_data JSONB
                );
            """))
            
            # Create wallets table
            logger.info("Creating wallets table...")
            connection.execute(text("""
                CREATE TABLE wallets (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id),
                    balance FLOAT NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                );
            """))
            
            # Create disputes table
            logger.info("Creating disputes table...")
            connection.execute(text("""
                CREATE TABLE disputes (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(16) UNIQUE NOT NULL REFERENCES transactions(id),
                    opened_by VARCHAR(16) NOT NULL,
                    reason TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    response TEXT,
                    status VARCHAR(16) NOT NULL DEFAULT 'open',
                    resolution VARCHAR(16),
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                );
            """))
            
            # Create wallet_transactions table
            logger.info("Creating wallet_transactions table...")
            connection.execute(text("""
                CREATE TABLE wallet_transactions (
                    id VARCHAR(36) PRIMARY KEY,
                    wallet_id VARCHAR(36) NOT NULL REFERENCES wallets(id),
                    transaction_id VARCHAR(16) NOT NULL REFERENCES transactions(id),
                    amount FLOAT NOT NULL,
                    direction VARCHAR(3) NOT NULL,
                    type VARCHAR(16) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transaction_details JSONB
                );
            """))
            
            connection.commit()
            logger.info("Database reset completed successfully!")
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    if success:
        print("✅ Database reset successful! Registration should now work.")
    else:
        print("❌ Database reset failed. Please check the logs.")