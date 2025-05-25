"""
Database initialization script for the Telegram Escrow Bot.
This script creates all the required tables in the PostgreSQL database.
"""
import os
import logging
import uuid
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from db_models import Base, User, Wallet, create_tables

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database with tables and sample data if needed."""
    try:
        # Create all the tables
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully!")
        
        # Optional: Create admin user for testing
        DB_URL = os.environ.get('DATABASE_URL', '')
        if not DB_URL:
            raise ValueError("DATABASE_URL environment variable is not set!")
            
        # Ensure the PostgreSQL URL is in the correct format for SQLAlchemy
        if DB_URL.startswith("postgres://"):
            DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if admin user exists
        admin_exists = session.query(User).filter(User.id == 0).first()
        if not admin_exists:
            logger.info("Creating admin user...")
            # Create admin user
            admin_user = User(
                id=0,
                username="admin",
                first_name="Admin",
                last_name="User"
            )
            session.add(admin_user)
            
            # Create admin wallet
            admin_wallet = Wallet(
                id=str(uuid.uuid4()),
                user_id=0,
                balance=0.0
            )
            session.add(admin_wallet)
            session.commit()
            logger.info("Admin user created successfully!")
            
        session.close()
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    initialize_database()