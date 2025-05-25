"""
Payment management handlers for the Telegram Escrow Bot.
Handles payment method management, sending and confirming payments.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from models.transaction import Transaction
from services.user_service import UserService
from services.escrow_service import EscrowService
from services.payment_service import PaymentService
from config import SUPPORTED_FIAT_METHODS, SUPPORTED_CRYPTO_METHODS, TransactionStatus

logger = logging.getLogger(__name__)
user_service = UserService()
escrow_service = EscrowService()
payment_service = PaymentService()

# Conversation states
METHOD_TYPE, METHOD_DETAILS, CONFIRM = range(3)

# Store payment method data temporarily
payment_data = {}

async def payment_methods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /payment_methods command.
    Shows the user's saved payment methods.
    """
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return
    
    # Get user's payment methods
    methods = payment_service.get_user_payment_methods(user_id)
    
    if not methods:
        keyboard = [
            [InlineKeyboardButton("Add Payment Method", callback_data="pay_add")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "You don't have any payment methods saved yet.\n\n"
            "Add a payment method to simplify future transactions.",
            reply_markup=reply_markup
        )
        return
    
    # Build payment methods list
    header = "*Your Payment Methods*\n\n"
    method_list = []
    
    for method in methods:
        if method['type'] == 'fiat':
            method_text = (
                f"*{method['name']}*\n"
                f"Type: Fiat\n"
                f"Details: {method['details']}"
            )
        else:
            method_text = (
                f"*{method['name']}*\n"
                f"Type: Cryptocurrency\n"
                f"Address: {method['address']}"
            )
        method_list.append(method_text)
    
    methods_text = header + "\n\n".join(method_list)
    
    # Add action buttons
    keyboard = [
        [InlineKeyboardButton("Add Payment Method", callback_data="pay_add")],
        [InlineKeyboardButton("Remove Payment Method", callback_data="pay_remove")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        methods_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def add_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /add_payment command.
    Starts the flow to add a new payment method.
    """
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return ConversationHandler.END
    
    # Initialize payment method data
    payment_data[user_id] = {'user_id': user_id}
    
    # Create method type selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("Fiat (Bank/PayPal)", callback_data="pay_type_fiat"),
            InlineKeyboardButton("Cryptocurrency", callback_data="pay_type_crypto")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Let's add a new payment method. First, select the type of payment method:",
        reply_markup=reply_markup
    )
    
    return METHOD_TYPE

async def payment_method_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method type selection."""
    query = update.callback_query
    user_id = query.from_user.id
    method_type = query.data.replace("pay_type_", "")
    
    # Save method type
    payment_data[user_id]['type'] = method_type
    
    if method_type == "fiat":
        # Create fiat method selection keyboard
        keyboard = []
        for method in SUPPORTED_FIAT_METHODS:
            keyboard.append([InlineKeyboardButton(method, callback_data=f"pay_method_{method.lower().replace(' ', '_')}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Select your fiat payment method:",
            reply_markup=reply_markup
        )
    else:
        # Create crypto method selection keyboard
        keyboard = []
        for method in SUPPORTED_CRYPTO_METHODS:
            keyboard.append([InlineKeyboardButton(method, callback_data=f"pay_method_{method.lower()}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Select your cryptocurrency:",
            reply_markup=reply_markup
        )
    
    return METHOD_DETAILS

async def payment_method_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle specific payment method selection."""
    query = update.callback_query
    user_id = query.from_user.id
    method = query.data.replace("pay_method_", "")
    
    # Save method name
    payment_data[user_id]['name'] = method.replace("_", " ").title()
    
    if payment_data[user_id]['type'] == "fiat":
        await query.edit_message_text(
            f"You selected {payment_data[user_id]['name']}.\n\n"
            f"Please provide the necessary details for this payment method.\n\n"
            f"For example:\n"
            f"- Bank Account: 'Bank Name, Account Number, Account Name'\n"
            f"- PayPal: 'your.email@example.com'\n\n"
            f"Reply to this message with the details:"
        )
    else:
        await query.edit_message_text(
            f"You selected {payment_data[user_id]['name']}.\n\n"
            f"Please provide your {payment_data[user_id]['name']} wallet address.\n\n"
            f"Reply to this message with the wallet address:"
        )
    
    return METHOD_DETAILS

async def payment_method_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method details input."""
    user_id = update.effective_user.id
    details = update.message.text.strip()
    
    # Validate details
    if len(details) < 5:
        await update.message.reply_text(
            "Please provide more detailed information."
        )
        return METHOD_DETAILS
    
    # Save details
    method_type = payment_data[user_id]['type']
    if method_type == "fiat":
        payment_data[user_id]['details'] = details
    else:
        payment_data[user_id]['address'] = details
    
    # Show confirmation
    method_info = (
        f"*Payment Method Summary*\n\n"
        f"Type: {method_type.capitalize()}\n"
        f"Method: {payment_data[user_id]['name']}\n"
    )
    
    if method_type == "fiat":
        method_info += f"Details: {payment_data[user_id]['details']}\n"
    else:
        method_info += f"Address: {payment_data[user_id]['address']}\n"
    
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="pay_confirm"),
            InlineKeyboardButton("Cancel", callback_data="pay_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        method_info + "\nIs this information correct?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return CONFIRM

async def payment_method_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method confirmation."""
    query = update.callback_query
    user_id = query.from_user.id
    action = query.data.replace("pay_", "")
    
    if action == "cancel":
        # User cancelled
        await query.edit_message_text(
            "Payment method addition cancelled."
        )
        # Clean up data
        if user_id in payment_data:
            del payment_data[user_id]
        return ConversationHandler.END
    
    # Save payment method
    data = payment_data[user_id]
    success = payment_service.add_payment_method(data)
    
    if success:
        await query.edit_message_text(
            f"✅ Payment method *{data['name']}* added successfully!",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ Failed to add payment method. Please try again later."
        )
    
    # Clean up data
    if user_id in payment_data:
        del payment_data[user_id]
    
    return ConversationHandler.END

async def send_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /pay command.
    Provides payment instructions for a transaction.
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
            "Please provide a transaction ID. Usage: /pay [transaction_id]"
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
    if transaction.buyer_id and transaction.buyer_id != user_id:
        await update.message.reply_text(
            "You are not the buyer for this transaction."
        )
        return
    
    # If user is not yet assigned as buyer, assign them
    if not transaction.buyer_id:
        # Update transaction with buyer details
        transaction.buyer_id = user_id
        transaction.buyer_username = update.effective_user.username
        escrow_service.update_transaction(transaction)
    
    # Check if transaction is in the right state
    if transaction.status != TransactionStatus.CREATED:
        await update.message.reply_text(
            f"This transaction is in '{transaction.status}' status and cannot be paid for.\n"
            f"Only transactions in 'created' status can be paid."
        )
        return
    
    # Get payment instructions
    if transaction.payment_method in ["bank", "bank_transfer", "paypal"]:
        # Get seller's payment details
        seller_method = payment_service.get_payment_method_by_name(
            transaction.seller_id, transaction.payment_method)
        
        if not seller_method:
            await update.message.reply_text(
                f"The seller hasn't provided payment details for {transaction.payment_method}.\n"
                f"Please contact the seller to provide payment details."
            )
            return
        
        payment_info = (
            f"*Payment Instructions*\n\n"
            f"Transaction: {transaction.title}\n"
            f"ID: `{transaction.id}`\n"
            f"Amount: ${transaction.amount:.2f}\n"
            f"Fee: ${transaction.fee:.2f}\n"
            f"Total to Pay: ${transaction.amount + transaction.fee:.2f}\n\n"
            f"Payment Method: {transaction.payment_method.capitalize()}\n"
            f"Recipient Details: {seller_method['details']}\n\n"
            f"Please send the payment to the recipient details provided above.\n"
            f"After sending payment, use /confirm_payment {transaction.id} to notify the system."
        )
    else:
        # Crypto payment
        # In a real implementation, this would generate a unique deposit address
        # For this demo, we'll use a placeholder
        payment_info = (
            f"*Cryptocurrency Payment Instructions*\n\n"
            f"Transaction: {transaction.title}\n"
            f"ID: `{transaction.id}`\n"
            f"Amount: ${transaction.amount:.2f} (in {transaction.payment_method.capitalize()})\n"
            f"Fee: ${transaction.fee:.2f} (in {transaction.payment_method.capitalize()})\n"
            f"Total to Pay: ${transaction.amount + transaction.fee:.2f}\n\n"
            f"Please send exactly the equivalent of ${transaction.amount + transaction.fee:.2f} "
            f"in {transaction.payment_method.capitalize()} to the following address:\n\n"
            f"`1Example{transaction.payment_method.capitalize()}AddressXYZ`\n\n"
            f"After sending payment, use /confirm_payment {transaction.id} to notify the system."
        )
    
    # Add confirmation button
    keyboard = [
        [InlineKeyboardButton("I've Sent Payment", callback_data=f"pay_sent_{transaction_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        payment_info,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /confirm_payment command.
    Buyer confirms they've sent payment for a transaction.
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
            "Please provide a transaction ID. Usage: /confirm_payment [transaction_id]"
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
            "Only the buyer can confirm payment for this transaction."
        )
        return
    
    # Check if transaction is in the right state
    if transaction.status != TransactionStatus.CREATED:
        await update.message.reply_text(
            f"This transaction is in '{transaction.status}' status.\n"
            f"Payment can only be confirmed for transactions in 'created' status."
        )
        return
    
    # Update transaction status
    success = payment_service.confirm_payment_sent(transaction_id, user_id)
    
    if success:
        # Update status
        transaction.status = TransactionStatus.FUNDED
        escrow_service.update_transaction(transaction)
        
        await update.message.reply_text(
            f"✅ Payment confirmation received for transaction `{transaction_id}`.\n\n"
            f"The seller has been notified and will verify the payment.\n"
            f"You'll receive a notification once the seller confirms receipt of payment.",
            parse_mode="Markdown"
        )
        
        # Notify seller
        try:
            await context.bot.send_message(
                chat_id=transaction.seller_id,
                text=(
                    f"💰 The buyer has confirmed sending payment for transaction `{transaction_id}` ({transaction.title}).\n\n"
                    f"Amount: ${transaction.amount:.2f}\n"
                    f"Payment Method: {transaction.payment_method.capitalize()}\n\n"
                    f"Please verify that you've received the payment and use /details {transaction_id} "
                    f"to view the transaction and confirm receipt."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify seller {transaction.seller_id}: {e}")
    else:
        await update.message.reply_text(
            "❌ Failed to confirm payment. Please try again later."
        )

async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for payment-related actions.
    """
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("_")
    action = data[1]
    
    # Handle payment method actions
    if action == "add":
        # Redirect to add payment method flow
        await query.edit_message_text(
            "Let's add a new payment method. First, select the type of payment method:"
        )
        
        # Create method type selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("Fiat (Bank/PayPal)", callback_data="pay_type_fiat"),
                InlineKeyboardButton("Cryptocurrency", callback_data="pay_type_crypto")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Let's add a new payment method. First, select the type of payment method:",
            reply_markup=reply_markup
        )
        
        # Initialize payment method data
        payment_data[user_id] = {'user_id': user_id}
        
        return METHOD_TYPE
    
    # Handle payment method type selection
    elif action == "type":
        return await payment_method_type(update, context)
    
    # Handle payment method selection
    elif action == "method":
        return await payment_method_selection(update, context)
    
    # Handle payment confirmation/cancellation
    elif action in ["confirm", "cancel"]:
        return await payment_method_confirm(update, context)
    
    # Handle payment sent confirmation
    elif action == "sent" and len(data) >= 3:
        transaction_id = data[2]
        transaction = escrow_service.get_transaction(transaction_id)
        
        if not transaction:
            await query.edit_message_text(
                f"Transaction with ID {transaction_id} not found."
            )
            return
        
        # Update transaction status
        success = payment_service.confirm_payment_sent(transaction_id, user_id)
        
        if success:
            # Update status
            transaction.status = TransactionStatus.FUNDED
            escrow_service.update_transaction(transaction)
            
            await query.edit_message_text(
                f"✅ Payment confirmation received for transaction `{transaction_id}`.\n\n"
                f"The seller has been notified and will verify the payment.\n"
                f"You'll receive a notification once the seller confirms receipt of payment.",
                parse_mode="Markdown"
            )
            
            # Notify seller
            try:
                await context.bot.send_message(
                    chat_id=transaction.seller_id,
                    text=(
                        f"💰 The buyer has confirmed sending payment for transaction `{transaction_id}` ({transaction.title}).\n\n"
                        f"Amount: ${transaction.amount:.2f}\n"
                        f"Payment Method: {transaction.payment_method.capitalize()}\n\n"
                        f"Please verify that you've received the payment and use /details {transaction_id} "
                        f"to view the transaction and confirm receipt."
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify seller {transaction.seller_id}: {e}")
        else:
            await query.edit_message_text(
                "❌ Failed to confirm payment. Please try again later."
            )
    
    # Handle payment method initialization for a transaction
    elif action == "init" and len(data) >= 3:
        transaction_id = data[2]
        transaction = escrow_service.get_transaction(transaction_id)
        
        if not transaction:
            await query.edit_message_text(
                f"Transaction with ID {transaction_id} not found."
            )
            return
        
        # Redirect to payment flow
        await query.edit_message_text(
            f"To proceed with payment for transaction `{transaction_id}`, please use:\n\n"
            f"/pay {transaction_id}"
        )
    
    else:
        await query.edit_message_text(
            "Unknown payment operation."
        )

async def show_payment_methods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show user payment methods (called from callbacks).
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get user's payment methods
    methods = payment_service.get_user_payment_methods(user_id)
    
    if not methods:
        keyboard = [
            [InlineKeyboardButton("Add Payment Method", callback_data="pay_add")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "You don't have any payment methods saved yet.\n\n"
            "Add a payment method to simplify future transactions.",
            reply_markup=reply_markup
        )
        return
    
    # Build payment methods list
    header = "*Your Payment Methods*\n\n"
    method_list = []
    
    for method in methods:
        if method['type'] == 'fiat':
            method_text = (
                f"*{method['name']}*\n"
                f"Type: Fiat\n"
                f"Details: {method['details']}"
            )
        else:
            method_text = (
                f"*{method['name']}*\n"
                f"Type: Cryptocurrency\n"
                f"Address: {method['address']}"
            )
        method_list.append(method_text)
    
    methods_text = header + "\n\n".join(method_list)
    
    # Add action buttons
    keyboard = [
        [InlineKeyboardButton("Add Payment Method", callback_data="pay_add")],
        [InlineKeyboardButton("Back to Profile", callback_data="user_profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        methods_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
