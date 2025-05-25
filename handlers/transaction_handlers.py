"""
Transaction management handlers for the Telegram Escrow Bot.
Handles transaction creation, listing, details, cancellation, and completion.
"""
import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from models.transaction import Transaction
from models.user import User
from services.user_service import UserService
from services.escrow_service import EscrowService
from config import TransactionStatus, UserRole, TRANSACTION_FEE_PERCENTAGE

logger = logging.getLogger(__name__)
user_service = UserService()
escrow_service = EscrowService()

# Conversation states
TITLE, DESCRIPTION, AMOUNT, PAYMENT_METHOD, CONFIRM = range(5)

# Store conversation data temporarily
conv_data = {}

async def create_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /new command.
    Starts the transaction creation flow.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        # Create inline keyboard for registration
        keyboard = [
            [InlineKeyboardButton("✅ Register Now", callback_data="user_register")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ *Registration Required*\n\n"
            "You need to register before creating a transaction.\n\n"
            "Registration only takes a few seconds and ensures secure escrow transactions.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Check if user passed "help" argument
    if context.args and context.args[0].lower() == "help":
        # Show detailed help with examples and better formatting
        help_text = (
            "📝 *Creating a New Escrow Transaction*\n\n"
            "This guide will walk you through creating a secure escrow transaction:\n\n"
            "1️⃣ *Title* - Brief name for your transaction\n"
            "   _Example: \"Logo Design\" or \"Website Development\"_\n\n"
            "2️⃣ *Description* - Detailed information about goods/services\n"
            "   _Example: \"Professional logo design with 3 revisions\"_\n\n"
            "3️⃣ *Amount* - The price in USD\n"
            "   _Example: 150.00_\n\n"
            "4️⃣ *Payment Method* - How the buyer will pay\n"
            "   _Options: Bank Transfer, PayPal, Bitcoin, Ethereum_\n\n"
            "*What happens next?*\n"
            "• You'll receive a transaction ID and link to share with the buyer\n"
            "• Funds will be securely held in escrow until both parties are satisfied\n"
            "• The buyer confirms receipt to release payment to you\n\n"
            "*Security Tip:* Be clear and specific in your transaction details to avoid misunderstandings."
        )
        
        # Add buttons for quick actions
        keyboard = [
            [InlineKeyboardButton("🔄 Start Transaction", callback_data="transaction_start_new")],
            [InlineKeyboardButton("📋 View My Transactions", callback_data="user_transactions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Initialize conversation data
    conv_data[user_id] = {
        'role': UserRole.SELLER,  # Default to seller role
        'user_id': user_id,
        'username': username
    }
    
    # Send a welcome message for the transaction creation
    welcome_message = (
        f"🔒 *NEW SECURE TRANSACTION*\n\n"
        f"Hi {first_name}! Let's set up your escrow transaction.\n\n"
        f"You'll be the *SELLER* in this transaction, which means you'll:\n"
        f"• Specify what you're selling\n"
        f"• Set the price\n"
        f"• Choose payment methods\n"
        f"• Deliver goods/services when funded\n\n"
        f"*Step 1 of 4: Transaction Title*\n"
        f"Please provide a short, descriptive title for what you're selling:"
    )
    
    # Add cancel button
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return TITLE

async def transaction_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the transaction title input."""
    user_id = update.effective_user.id
    title = update.message.text.strip()
    
    # Check for cancel command
    if title.lower() == "/cancel":
        await update.message.reply_text(
            "💤 Transaction creation cancelled. Use /new to start again when you're ready."
        )
        # Clean up conversation data
        if user_id in conv_data:
            del conv_data[user_id]
        return ConversationHandler.END
    
    # Validate title
    if len(title) < 3 or len(title) > 50:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ *Title Length Issue*\n\n"
            "Your title should be between 3-50 characters for clarity.\n\n"
            "Please try again with a more appropriate length.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return TITLE
    
    # Save title
    conv_data[user_id]['title'] = title
    
    # Ask for description with progress indicator and formatting
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    progress_message = (
        f"✅ *Title saved:* \"{title}\"\n\n"
        f"*Step 2 of 4: Transaction Description*\n\n"
        f"Please provide a detailed description of what you're offering:\n"
        f"• What exactly is included?\n"
        f"• What are the deliverables?\n"
        f"• What is the timeline or delivery method?\n\n"
        f"_A clear description helps prevent misunderstandings later._"
    )
    
    await update.message.reply_text(
        progress_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return DESCRIPTION

async def transaction_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the transaction description input."""
    user_id = update.effective_user.id
    description = update.message.text.strip()
    
    # Check for cancel command
    if description.lower() == "/cancel":
        await update.message.reply_text(
            "💤 Transaction creation cancelled. Use /new to start again when you're ready."
        )
        # Clean up conversation data
        if user_id in conv_data:
            del conv_data[user_id]
        return ConversationHandler.END
    
    # Validate description
    if len(description) < 10 or len(description) > 500:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ *Description Length Issue*\n\n"
            "Your description should be between 10-500 characters.\n"
            "• Too short: Lacks necessary details\n"
            "• Too long: May be difficult to understand\n\n"
            "Please try again with a clearer, more concise description.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return DESCRIPTION
    
    # Save description
    conv_data[user_id]['description'] = description
    
    # Create a shortened preview of the description (first 50 chars)
    short_description = description[:50] + "..." if len(description) > 50 else description
    
    # Ask for amount with progress indicator and formatting
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    progress_message = (
        f"✅ *Description saved:* \"{short_description}\"\n\n"
        f"*Step 3 of 4: Transaction Amount*\n\n"
        f"Please enter the price in USD for this transaction.\n"
        f"• Use numbers only (e.g., 100 or 99.99)\n"
        f"• Do not include currency symbols\n"
        f"• The escrow fee ({TRANSACTION_FEE_PERCENTAGE}%) will be added automatically\n\n"
        f"_Example: For a $100 transaction, simply type '100'_"
    )
    
    await update.message.reply_text(
        progress_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return AMOUNT

async def transaction_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the transaction amount input."""
    user_id = update.effective_user.id
    amount_text = update.message.text.strip()
    
    # Check for cancel command
    if amount_text.lower() == "/cancel":
        await update.message.reply_text(
            "💤 Transaction creation cancelled. Use /new to start again when you're ready."
        )
        # Clean up conversation data
        if user_id in conv_data:
            del conv_data[user_id]
        return ConversationHandler.END
    
    # Validate amount
    try:
        # Remove any currency symbols if entered
        cleaned_text = amount_text.replace('$', '').replace('USD', '').strip()
        amount = float(cleaned_text)
        
        # Check for reasonable amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > 10000:  # Arbitrary high limit for safety
            keyboard = [
                [InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⚠️ *Large Amount Detected*\n\n"
                "For security reasons, please confirm if you intended to enter such a large amount.\n\n"
                "If this was an error, please enter a corrected amount.\n"
                "For high-value transactions, consider breaking them into smaller ones.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return AMOUNT
            
    except ValueError:
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ *Invalid Amount Format*\n\n"
            "Please enter a valid numeric amount.\n"
            "• Use only numbers and decimal point\n"
            "• Example: 100 or 99.99\n"
            "• Do not include letters or special characters\n\n"
            "Try again with a valid amount.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return AMOUNT
    
    # Save amount
    conv_data[user_id]['amount'] = amount
    
    # Calculate fee
    fee = amount * (TRANSACTION_FEE_PERCENTAGE / 100)
    conv_data[user_id]['fee'] = fee
    
    # Format total for display
    total = amount + fee
    
    # Ask for payment method with progress indicator and better UI
    progress_message = (
        f"✅ *Amount saved:* ${amount:.2f}\n\n"
        f"*Fee calculation:*\n"
        f"• Base amount: ${amount:.2f}\n"
        f"• Escrow fee ({TRANSACTION_FEE_PERCENTAGE}%): ${fee:.2f}\n"
        f"• Total for buyer: ${total:.2f}\n\n"
        f"*Step 4 of 4: Payment Method*\n\n"
        f"Please select the preferred payment method:"
    )
    
    # Enhanced payment method selection with icons
    keyboard = [
        [
            InlineKeyboardButton("🏦 Bank Transfer", callback_data="pay_method_bank"),
            InlineKeyboardButton("💳 PayPal", callback_data="pay_method_paypal")
        ],
        [
            InlineKeyboardButton("₿ Bitcoin", callback_data="pay_method_bitcoin"),
            InlineKeyboardButton("Ξ Ethereum", callback_data="pay_method_ethereum")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        progress_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return PAYMENT_METHOD

async def transaction_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the payment method selection."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Check if this is a cancellation request
    if query.data == "txn_cancel_creation":
        await query.edit_message_text(
            "💤 Transaction creation cancelled. Use /new to start again when you're ready."
        )
        # Clean up conversation data
        if user_id in conv_data:
            del conv_data[user_id]
        return ConversationHandler.END
    
    # Extract the payment method from callback data
    method = query.data.replace("pay_method_", "")
    
    # Format method name for display
    method_display_names = {
        "bank": "Bank Transfer",
        "paypal": "PayPal",
        "bitcoin": "Bitcoin",
        "ethereum": "Ethereum"
    }
    
    display_method = method_display_names.get(method, method.capitalize())
    
    # Save payment method
    conv_data[user_id]['payment_method'] = method
    
    # Show transaction summary with enhanced formatting
    data = conv_data[user_id]
    
    # Create a short preview of the description
    desc_preview = data['description']
    if len(desc_preview) > 100:
        desc_preview = desc_preview[:97] + "..."
    
    # Calculate the totals
    amount = data['amount']
    fee = data['fee']
    total = amount + fee
    
    # Build an attractive transaction summary
    summary = (
        f"🔐 *TRANSACTION SUMMARY*\n\n"
        f"📝 *Title:* {data['title']}\n\n"
        f"📋 *Description:*\n{desc_preview}\n\n"
        f"💰 *Financial Details:*\n"
        f"• Base Amount: ${amount:.2f}\n"
        f"• Escrow Fee ({TRANSACTION_FEE_PERCENTAGE}%): ${fee:.2f}\n"
        f"• Total: ${total:.2f}\n\n"
        f"💳 *Payment Method:* {display_method}\n\n"
        f"✅ Please review and confirm these details before creating the transaction. Once created, you'll receive a transaction ID to share with the buyer."
    )
    
    # Create confirmation buttons with better labeling
    keyboard = [
        [
            InlineKeyboardButton("✅ Create Transaction", callback_data="txn_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel")
        ],
        [
            InlineKeyboardButton("🔄 Change Payment Method", callback_data="txn_change_payment")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        summary,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return CONFIRM

async def transaction_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the transaction confirmation."""
    query = update.callback_query
    user_id = query.from_user.id
    action = query.data.replace("txn_", "")
    
    # Handle different action types
    if action == "cancel":
        # User cancelled the transaction
        await query.edit_message_text(
            "💤 Transaction creation cancelled. Use /new to start again when you're ready."
        )
        # Clean up conversation data
        if user_id in conv_data:
            del conv_data[user_id]
        return ConversationHandler.END
    
    elif action == "change_payment":
        # User wants to change payment method
        # Go back to payment method selection
        
        # Ask for payment method with progress indicator and better UI
        data = conv_data[user_id]
        progress_message = (
            f"*Change Payment Method*\n\n"
            f"Current transaction: *{data['title']}*\n"
            f"Amount: ${data['amount']:.2f}\n\n"
            f"Please select a different payment method:"
        )
        
        # Enhanced payment method selection with icons
        keyboard = [
            [
                InlineKeyboardButton("🏦 Bank Transfer", callback_data="pay_method_bank"),
                InlineKeyboardButton("💳 PayPal", callback_data="pay_method_paypal")
            ],
            [
                InlineKeyboardButton("₿ Bitcoin", callback_data="pay_method_bitcoin"),
                InlineKeyboardButton("Ξ Ethereum", callback_data="pay_method_ethereum")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="txn_cancel_creation")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            progress_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return PAYMENT_METHOD
    
    elif action == "confirm":
        # Create the transaction with a visual processing indicator
        await query.edit_message_text(
            "⏳ *Creating Your Transaction*\n\n"
            "Please wait while we set up your secure escrow...",
            parse_mode="Markdown"
        )
        
        # Get transaction data
        data = conv_data[user_id]
        
        # Generate a memorable transaction ID
        # Format: 2 letters + 6 numbers for better readability
        import random
        import string
        letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
        numbers = ''.join(random.choice(string.digits) for _ in range(6))
        transaction_id = f"{letters}{numbers}"
        
        # Create transaction object
        transaction = Transaction(
            id=transaction_id,
            title=data['title'],
            description=data['description'],
            amount=data['amount'],
            fee=data['fee'],
            payment_method=data['payment_method'],
            seller_id=user_id,
            seller_username=data['username'],
            status=TransactionStatus.CREATED
        )
        
        # Save the transaction
        success = escrow_service.create_transaction(transaction)
        
        if success:
            # Format method name for display
            method_display_names = {
                "bank": "Bank Transfer",
                "paypal": "PayPal",
                "bitcoin": "Bitcoin",
                "ethereum": "Ethereum"
            }
            display_method = method_display_names.get(data['payment_method'], data['payment_method'].capitalize())
            
            # Generate a deep link that the buyer can use
            invite_link = f"https://t.me/{context.bot.username}?start=txn_{transaction_id}"
            
            # Create a QR code command (this is just an example, actual QR code would need more implementation)
            qr_command = f"/qr_code {transaction_id}"
            
            # Format a beautiful success message
            confirmation = (
                f"🎉 *Transaction Created Successfully!*\n\n"
                f"📝 *Transaction ID:* `{transaction_id}`\n"
                f"💳 *Payment Method:* {display_method}\n"
                f"💰 *Amount:* ${data['amount']:.2f}\n\n"
                f"📱 *Share with buyer:*\n"
                f"• Copy this link: {invite_link}\n"
                f"• Or share transaction ID: `{transaction_id}`\n\n"
                f"🔔 *What happens next?*\n"
                f"1. Buyer joins the transaction\n"
                f"2. Buyer sends payment to escrow\n"
                f"3. You deliver goods/services\n"
                f"4. Buyer confirms receipt\n"
                f"5. Funds are released to you\n\n"
                f"You'll receive notifications at each step. Type /transactions to view all your active transactions."
            )
            
            # Create action buttons
            keyboard = [
                [
                    InlineKeyboardButton("📋 My Transactions", callback_data="user_transactions"),
                    InlineKeyboardButton("➕ New Transaction", callback_data="transaction_new")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                confirmation,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            # Show nicely formatted error
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="transaction_start_new")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ *Transaction Creation Failed*\n\n"
                "We encountered an issue while creating your transaction.\n\n"
                "This could be due to a temporary system issue. Please try again in a few moments.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        # Clean up conversation data
        if user_id in conv_data:
            del conv_data[user_id]
        
        return ConversationHandler.END
    
    else:
        # Unknown action, just end the conversation
        await query.edit_message_text(
            "⚠️ Unknown action. Transaction creation cancelled."
        )
        
        # Clean up conversation data
        if user_id in conv_data:
            del conv_data[user_id]
        
        return ConversationHandler.END

async def list_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /transactions command.
    Lists all transactions for the user.
    """
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return
    
    # Get user's transactions
    transactions = escrow_service.get_user_transactions(user_id)
    
    if not transactions:
        await update.message.reply_text(
            "You don't have any transactions yet.\n\n"
            "Use /new to create a new transaction."
        )
        return
    
    # Build transactions list
    header = "*Your Transactions*\n\n"
    transaction_list = []
    
    for txn in transactions:
        role = "Seller" if txn.seller_id == user_id else "Buyer"
        counterparty = txn.buyer_username if role == "Seller" else txn.seller_username
        counterparty = counterparty or "Not joined yet"
        
        txn_text = (
            f"ID: `{txn.id}`\n"
            f"Title: {txn.title}\n"
            f"Amount: ${txn.amount:.2f}\n"
            f"Status: {txn.status.capitalize()}\n"
            f"Role: {role}\n"
            f"Counterparty: @{counterparty}\n"
            f"Created: {txn.created_at.strftime('%Y-%m-%d')}\n"
        )
        transaction_list.append(txn_text)
    
    # Create paginated view if needed
    if len(transaction_list) > 5:
        # Only show first 5 transactions
        transactions_text = header + "\n\n".join(transaction_list[:5]) + "\n\n(Use /details [ID] to see more details)"
    else:
        transactions_text = header + "\n\n".join(transaction_list) + "\n\n(Use /details [ID] to see more details)"
    
    await update.message.reply_text(
        transactions_text,
        parse_mode="Markdown"
    )

async def transaction_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /details command.
    Shows detailed information about a specific transaction.
    """
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return
    
    # Check if transaction ID is provided
    if not context.args:
        await update.message.reply_text(
            "Please provide a transaction ID. Usage: /details [transaction_id]"
        )
        return
    
    transaction_id = context.args[0]
    transaction = escrow_service.get_transaction(transaction_id)
    
    if not transaction:
        await update.message.reply_text(
            f"Transaction with ID {transaction_id} not found."
        )
        return
    
    # Check if user is part of this transaction
    if user_id != transaction.seller_id and user_id != transaction.buyer_id:
        await update.message.reply_text(
            "You don't have access to this transaction."
        )
        return
    
    # Determine user's role in this transaction
    role = "Seller" if transaction.seller_id == user_id else "Buyer"
    
    # Build transaction details
    details = (
        f"*Transaction Details*\n\n"
        f"ID: `{transaction.id}`\n"
        f"Title: {transaction.title}\n"
        f"Description: {transaction.description}\n"
        f"Amount: ${transaction.amount:.2f}\n"
        f"Escrow Fee: ${transaction.fee:.2f}\n"
        f"Total: ${transaction.amount + transaction.fee:.2f}\n"
        f"Status: {transaction.status.capitalize()}\n"
        f"Payment Method: {transaction.payment_method.capitalize()}\n"
        f"Your Role: {role}\n"
    )
    
    # Add counterparty information
    if role == "Seller":
        if transaction.buyer_id:
            details += f"Buyer: @{transaction.buyer_username}\n"
        else:
            details += "Buyer: Not joined yet\n"
    else:
        details += f"Seller: @{transaction.seller_username}\n"
    
    # Add timestamps
    details += f"Created: {transaction.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    if transaction.updated_at:
        details += f"Last Updated: {transaction.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
    
    # Add action buttons based on transaction status and user role
    keyboard = []
    
    if transaction.status == TransactionStatus.CREATED:
        if role == "Buyer":
            keyboard.append([InlineKeyboardButton("Fund Transaction", callback_data=f"txn_fund_{transaction.id}")])
        elif role == "Seller":
            keyboard.append([InlineKeyboardButton("Cancel Transaction", callback_data=f"txn_cancel_{transaction.id}")])
    
    elif transaction.status == TransactionStatus.FUNDED:
        if role == "Seller":
            keyboard.append([InlineKeyboardButton("Confirm Receipt", callback_data=f"txn_confirm_{transaction.id}")])
        elif role == "Buyer":
            keyboard.append([InlineKeyboardButton("Open Dispute", callback_data=f"dispute_open_{transaction.id}")])
    
    elif transaction.status == TransactionStatus.CONFIRMED:
        if role == "Buyer":
            keyboard.append([InlineKeyboardButton("Complete Transaction", callback_data=f"txn_complete_{transaction.id}")])
            keyboard.append([InlineKeyboardButton("Open Dispute", callback_data=f"dispute_open_{transaction.id}")])
    
    elif transaction.status == TransactionStatus.DISPUTED:
        keyboard.append([InlineKeyboardButton("View Dispute", callback_data=f"dispute_view_{transaction.id}")])
    
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            details,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            details,
            parse_mode="Markdown"
        )

async def cancel_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /cancel command.
    Cancels a transaction if it's in the appropriate state.
    """
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return
    
    # Check if transaction ID is provided
    if not context.args:
        await update.message.reply_text(
            "Please provide a transaction ID. Usage: /cancel [transaction_id]"
        )
        return
    
    transaction_id = context.args[0]
    transaction = escrow_service.get_transaction(transaction_id)
    
    if not transaction:
        await update.message.reply_text(
            f"Transaction with ID {transaction_id} not found."
        )
        return
    
    # Check if user is authorized to cancel this transaction
    if user_id != transaction.seller_id and user_id != transaction.buyer_id:
        await update.message.reply_text(
            "You don't have permission to cancel this transaction."
        )
        return
    
    # Check if transaction can be cancelled
    if transaction.status not in [TransactionStatus.CREATED]:
        await update.message.reply_text(
            f"Cannot cancel transaction in '{transaction.status}' status.\n"
            f"Only transactions in 'created' status can be cancelled."
        )
        return
    
    # Create confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("Yes, Cancel", callback_data=f"txn_cancel_confirm_{transaction_id}"),
            InlineKeyboardButton("No, Keep", callback_data=f"txn_cancel_abort_{transaction_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Are you sure you want to cancel transaction `{transaction_id}`?\n\n"
        f"Title: {transaction.title}\n"
        f"Amount: ${transaction.amount:.2f}\n\n"
        f"This action cannot be undone.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def complete_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /complete command.
    Completes a transaction, releasing funds to the seller.
    """
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return
    
    # Check if transaction ID is provided
    if not context.args:
        await update.message.reply_text(
            "Please provide a transaction ID. Usage: /complete [transaction_id]"
        )
        return
    
    transaction_id = context.args[0]
    transaction = escrow_service.get_transaction(transaction_id)
    
    if not transaction:
        await update.message.reply_text(
            f"Transaction with ID {transaction_id} not found."
        )
        return
    
    # Check if user is the buyer
    if user_id != transaction.buyer_id:
        await update.message.reply_text(
            "Only the buyer can complete this transaction."
        )
        return
    
    # Check if transaction is in the correct state
    if transaction.status != TransactionStatus.CONFIRMED:
        await update.message.reply_text(
            f"Cannot complete transaction in '{transaction.status}' status.\n"
            f"Only transactions in 'confirmed' status can be completed."
        )
        return
    
    # Create confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("Yes, Complete", callback_data=f"txn_complete_confirm_{transaction_id}"),
            InlineKeyboardButton("No, Not Yet", callback_data=f"txn_complete_abort_{transaction_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Are you confirming that you've received the goods/services for transaction `{transaction_id}`?\n\n"
        f"Title: {transaction.title}\n"
        f"Amount: ${transaction.amount:.2f}\n\n"
        f"This will release the funds to the seller and cannot be undone.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for transaction actions.
    """
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("_")
    action = data[1]
    
    # Handle confirmation flow callbacks
    if action == "confirm" and len(data) == 2:
        return await transaction_confirm(update, context)
    
    if action == "cancel" and len(data) == 2:
        return await transaction_confirm(update, context)
    
    # Handle transaction action callbacks
    if len(data) >= 3:
        transaction_id = data[2]
        transaction = escrow_service.get_transaction(transaction_id)
        
        if not transaction:
            await query.edit_message_text(
                f"Transaction with ID {transaction_id} not found."
            )
            return
        
        # Fund transaction
        if action == "fund":
            # Create payment instructions
            payment_instructions = (
                f"*Payment Instructions*\n\n"
                f"Transaction: {transaction.title}\n"
                f"Amount: ${transaction.amount:.2f}\n"
                f"Fee: ${transaction.fee:.2f}\n"
                f"Total: ${transaction.amount + transaction.fee:.2f}\n"
                f"Payment Method: {transaction.payment_method.capitalize()}\n\n"
            )
            
            if transaction.payment_method in ["bank", "paypal"]:
                # Fiat payment
                payment_instructions += (
                    f"To proceed with payment:\n"
                    f"1. Use /pay {transaction_id} to get detailed payment instructions\n"
                    f"2. After sending payment, use /confirm_payment {transaction_id}\n"
                    f"3. The seller will verify your payment\n\n"
                    f"Your funds will be held in escrow until you confirm receipt of goods/services."
                )
            else:
                # Crypto payment
                payment_instructions += (
                    f"To proceed with crypto payment:\n"
                    f"1. Use /pay {transaction_id} to get the deposit address\n"
                    f"2. Send exactly the requested amount to the provided address\n"
                    f"3. After sending, use /confirm_payment {transaction_id}\n\n"
                    f"Your funds will be held in escrow until you confirm receipt of goods/services."
                )
            
            keyboard = [
                [InlineKeyboardButton("Make Payment", callback_data=f"pay_init_{transaction_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                payment_instructions,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        # Cancel transaction
        elif action == "cancel":
            keyboard = [
                [
                    InlineKeyboardButton("Yes, Cancel", callback_data=f"txn_cancel_confirm_{transaction_id}"),
                    InlineKeyboardButton("No, Keep", callback_data=f"txn_cancel_abort_{transaction_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Are you sure you want to cancel transaction `{transaction_id}`?\n\n"
                f"Title: {transaction.title}\n"
                f"Amount: ${transaction.amount:.2f}\n\n"
                f"This action cannot be undone.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        # Confirm cancellation
        elif action == "cancel" and len(data) >= 4 and data[3] == "confirm":
            success = escrow_service.cancel_transaction(transaction_id, user_id)
            
            if success:
                await query.edit_message_text(
                    f"✅ Transaction `{transaction_id}` has been cancelled."
                )
                
                # Notify the other party
                other_id = transaction.buyer_id if user_id == transaction.seller_id else transaction.seller_id
                if other_id:
                    try:
                        await context.bot.send_message(
                            chat_id=other_id,
                            text=f"ℹ️ Transaction `{transaction_id}` ({transaction.title}) has been cancelled.",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify user {other_id}: {e}")
            else:
                await query.edit_message_text(
                    f"❌ Failed to cancel transaction `{transaction_id}`."
                )
        
        # Abort cancellation
        elif action == "cancel" and len(data) >= 4 and data[3] == "abort":
            await query.edit_message_text(
                f"Transaction cancellation aborted. The transaction remains active."
            )
        
        # Confirm receipt (seller confirms payment was received)
        elif action == "confirm":
            success = escrow_service.confirm_transaction(transaction_id, user_id)
            
            if success:
                await query.edit_message_text(
                    f"✅ You've confirmed receipt of payment for transaction `{transaction_id}`.\n\n"
                    f"The buyer can now review the goods/services and complete the transaction "
                    f"to release the funds from escrow."
                )
                
                # Notify the buyer
                try:
                    await context.bot.send_message(
                        chat_id=transaction.buyer_id,
                        text=(
                            f"ℹ️ The seller has confirmed receipt of your payment for transaction `{transaction_id}` ({transaction.title}).\n\n"
                            f"Once you've received and are satisfied with the goods/services, "
                            f"please use /complete {transaction_id} to release the funds to the seller."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify buyer {transaction.buyer_id}: {e}")
            else:
                await query.edit_message_text(
                    f"❌ Failed to confirm transaction `{transaction_id}`."
                )
        
        # Complete transaction
        elif action == "complete":
            keyboard = [
                [
                    InlineKeyboardButton("Yes, Complete", callback_data=f"txn_complete_confirm_{transaction_id}"),
                    InlineKeyboardButton("No, Not Yet", callback_data=f"txn_complete_abort_{transaction_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"Are you confirming that you've received the goods/services for transaction `{transaction_id}`?\n\n"
                f"Title: {transaction.title}\n"
                f"Amount: ${transaction.amount:.2f}\n\n"
                f"This will release the funds to the seller and cannot be undone.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        # Confirm completion
        elif action == "complete" and len(data) >= 4 and data[3] == "confirm":
            success = escrow_service.complete_transaction(transaction_id, user_id)
            
            if success:
                await query.edit_message_text(
                    f"✅ Transaction `{transaction_id}` has been completed!\n\n"
                    f"The funds have been released to the seller. Thank you for using our escrow service."
                )
                
                # Notify the seller
                try:
                    await context.bot.send_message(
                        chat_id=transaction.seller_id,
                        text=(
                            f"🎉 Good news! Transaction `{transaction_id}` ({transaction.title}) has been completed.\n\n"
                            f"The buyer has confirmed receipt of goods/services and the funds "
                            f"(${transaction.amount:.2f}) have been released to you."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify seller {transaction.seller_id}: {e}")
            else:
                await query.edit_message_text(
                    f"❌ Failed to complete transaction `{transaction_id}`."
                )
        
        # Abort completion
        elif action == "complete" and len(data) >= 4 and data[3] == "abort":
            await query.edit_message_text(
                f"Transaction completion aborted. The transaction remains in progress."
            )
        
        else:
            await query.edit_message_text(
                "Unknown transaction operation."
            )

async def show_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show user transactions (called from callbacks).
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get user's transactions
    transactions = escrow_service.get_user_transactions(user_id)
    
    if not transactions:
        await query.edit_message_text(
            "You don't have any transactions yet.\n\n"
            "Use /new to create a new transaction."
        )
        return
    
    # Build transactions list
    header = "*Your Transactions*\n\n"
    transaction_list = []
    
    for txn in transactions:
        role = "Seller" if txn.seller_id == user_id else "Buyer"
        counterparty = txn.buyer_username if role == "Seller" else txn.seller_username
        counterparty = counterparty or "Not joined yet"
        
        txn_text = (
            f"ID: `{txn.id}`\n"
            f"Title: {txn.title}\n"
            f"Amount: ${txn.amount:.2f}\n"
            f"Status: {txn.status.capitalize()}\n"
            f"Role: {role}\n"
            f"Counterparty: @{counterparty}\n"
        )
        transaction_list.append(txn_text)
    
    # Create paginated view if needed
    if len(transaction_list) > 5:
        # Only show first 5 transactions
        transactions_text = header + "\n\n".join(transaction_list[:5]) + "\n\n(Use /details [ID] to see more details)"
    else:
        transactions_text = header + "\n\n".join(transaction_list) + "\n\n(Use /details [ID] to see more details)"
    
    # Add buttons
    keyboard = [
        [InlineKeyboardButton("Create New Transaction", callback_data="txn_new")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        transactions_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
