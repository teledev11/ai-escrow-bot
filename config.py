"""
Configuration module for the Telegram Escrow Bot.
Contains application-wide settings and constants.
"""
import os

# Bot configuration
BOT_NAME = "EscrowAssistantBot"
BOT_DESCRIPTION = "A secure escrow service for digital goods and services transactions."

# Transaction settings
TRANSACTION_FEE_PERCENTAGE = 2.5  # 2.5% escrow fee
MIN_TRANSACTION_AMOUNT = 5  # Minimum amount for a transaction
MAX_TRANSACTION_AMOUNT = 5000  # Maximum amount for a transaction
TRANSACTION_TIMEOUT_DAYS = 14  # Number of days before a transaction times out

# Supported payment methods
SUPPORTED_FIAT_METHODS = ["Bank Transfer", "PayPal", "Credit Card", "Cash App"]
SUPPORTED_CRYPTO_METHODS = ["Bitcoin", "Ethereum", "Litecoin", "USDT"]

# Transaction statuses
class TransactionStatus:
    CREATED = "created"
    FUNDED = "funded"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

# Dispute statuses
class DisputeStatus:
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

# User roles
class UserRole:
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"

# Help messages and command descriptions
HELP_MESSAGE = """
🔐 *SECURE ESCROW ASSISTANT* 🔐

Welcome to your trusted escrow assistant for digital transactions. Here's how to use the bot:

🧩 *GENERAL COMMANDS*
• `/start` - Launch the bot & welcome screen
• `/help` - Display this help guide
• `/register` - Create your escrow account
• `/profile` - View your account dashboard

💰 *TRANSACTION COMMANDS*
• `/new` - Create a new escrow transaction
• `/transactions` - See all your transactions
• `/details [ID]` - View specific transaction
• `/cancel [ID]` - Cancel an active transaction
• `/complete [ID]` - Finalize and release funds

💳 *PAYMENT COMMANDS*
• `/payment_methods` - Manage saved payment methods
• `/add_payment` - Add new payment option
• `/pay [ID]` - Fund an escrow transaction
• `/confirm_payment [ID]` - Verify payment received

⚖️ *DISPUTE RESOLUTION*
• `/dispute [ID]` - Open dispute case
• `/dispute_details [ID]` - Check dispute status
• `/resolve [ID]` - Mark dispute as resolved

💡 *PRO TIP:* For detailed instructions on any command, type the command followed by "help" (example: `/new help`)
"""

# Category help messages
TRANSACTION_HELP = """
📝 *TRANSACTION GUIDE*

*Creating a Transaction (Seller):*
1. Use `/new` to start a new escrow
2. Enter title, description & amount
3. Choose your preferred payment method
4. Share the generated ID with your buyer

*Joining a Transaction (Buyer):*
1. Get transaction ID from seller
2. View details with `/details [ID]`
3. Fund transaction with `/pay [ID]`
4. Receive goods/services from seller
5. Complete with `/complete [ID]`

Your funds remain secure in escrow until both parties are satisfied with the transaction.
"""

PAYMENT_HELP = """
💸 *PAYMENT GUIDE*

*Supported Payment Methods:*
• *Fiat:* Bank Transfer, PayPal, Credit Card, Cash App
• *Crypto:* Bitcoin, Ethereum, Litecoin, USDT

*Adding Payment Methods:*
1. Use `/add_payment` command
2. Select payment type (fiat/crypto)
3. Choose specific method
4. Add required payment details
5. Confirm to save

Your payment information is securely stored for easy transaction management.
"""

DISPUTE_HELP = """
⚖️ *DISPUTE RESOLUTION GUIDE*

*Opening a Dispute:*
1. Use `/dispute [ID]` command
2. Provide reason for dispute
3. Submit evidence (screenshots, messages)
4. Wait for resolution process

*Resolution Process:*
• Both parties can communicate through the bot
• Provide additional information when requested
• Resolution based on evidence provided
• Funds released according to fair decision

Our goal is to provide fair and transparent resolution for all disputes.
"""

# API endpoints (for future use)
CRYPTO_PRICE_API = "https://api.coingecko.com/api/v3/simple/price"
