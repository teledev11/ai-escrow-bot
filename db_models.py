"""
Database models for the Telegram Escrow Bot.
These models will be stored in the PostgreSQL database.
"""
import os
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

# Create the database engine
DB_URL = os.environ.get('DATABASE_URL', '')
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Ensure the PostgreSQL URL is in the correct format for SQLAlchemy
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """
    Represents a registered user in the escrow system.
    """
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    # Relationships
    transactions_as_buyer = relationship("Transaction", foreign_keys="Transaction.buyer_id", back_populates="buyer")
    transactions_as_seller = relationship("Transaction", foreign_keys="Transaction.seller_id", back_populates="seller")
    payment_methods = relationship("PaymentMethod", back_populates="user")
    wallet = relationship("Wallet", uselist=False, back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class PaymentMethod(Base):
    """
    Represents a payment method saved by a user.
    """
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(64), nullable=False)
    type = Column(String(16), nullable=False)  # "fiat" or "crypto"
    details = Column(Text, nullable=True)      # For fiat methods
    address = Column(String(128), nullable=True)  # For crypto methods
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="payment_methods")

    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, name={self.name}, type={self.type})>"


class Transaction(Base):
    """
    Represents an escrow transaction between a buyer and a seller.
    """
    __tablename__ = "transactions"

    id = Column(String(16), primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    payment_method = Column(String(64), nullable=False)
    seller_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    buyer_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    status = Column(String(16), nullable=False, default="created")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    # Renamed from metadata to avoid conflicts with SQLAlchemy's internal attribute
    transaction_data = Column(JSONB, nullable=True)

    # Relationships
    seller = relationship("User", foreign_keys=[seller_id], back_populates="transactions_as_seller")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="transactions_as_buyer")
    dispute = relationship("Dispute", uselist=False, back_populates="transaction")
    wallet_transactions = relationship("WalletTransaction", back_populates="transaction")

    def __repr__(self):
        return f"<Transaction(id={self.id}, title={self.title}, status={self.status})>"


class Dispute(Base):
    """
    Represents a dispute opened for a transaction.
    """
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(16), ForeignKey("transactions.id"), nullable=False, unique=True)
    opened_by = Column(String(16), nullable=False)  # "buyer" or "seller"
    reason = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="open")
    resolution = Column(String(16), nullable=True)
    opened_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    transaction = relationship("Transaction", back_populates="dispute")

    def __repr__(self):
        return f"<Dispute(id={self.id}, transaction_id={self.transaction_id}, status={self.status})>"


class Wallet(Base):
    """
    Represents a user's escrow wallet.
    """
    __tablename__ = "wallets"

    id = Column(String(36), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)
    balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="wallet")

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, balance={self.balance})>"


class WalletTransaction(Base):
    """
    Represents a transaction in a wallet.
    """
    __tablename__ = "wallet_transactions"

    id = Column(String(36), primary_key=True)
    wallet_id = Column(String(36), ForeignKey("wallets.id"), nullable=False)
    transaction_id = Column(String(16), ForeignKey("transactions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    direction = Column(String(3), nullable=False)  # "in" or "out"
    type = Column(String(16), nullable=False)  # "deposit", "withdrawal", "fee", etc.
    created_at = Column(DateTime, default=datetime.now)
    # Renamed from metadata to avoid conflicts with SQLAlchemy's internal attribute
    transaction_details = Column(JSONB, nullable=True)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")
    transaction = relationship("Transaction", back_populates="wallet_transactions")

    def __repr__(self):
        return f"<WalletTransaction(id={self.id}, amount={self.amount}, direction={self.direction})>"


# Create all tables in the database
def create_tables():
    Base.metadata.create_all(bind=engine)


# Get a database session
def get_db_session():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()