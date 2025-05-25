"""
Dispute management handlers for the Telegram Escrow Bot.
Handles dispute creation, resolution, and details.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from models.transaction import Transaction
from services.user_service import UserService
from services.escrow_service import EscrowService
from config import TransactionStatus, DisputeStatus

logger = logging.getLogger(__name__)
user_service = UserService()
escrow_service = EscrowService()

# Conversation states
REASON, EVIDENCE = range(2)

# Store dispute data temporarily
dispute_data = {}

async def open_dispute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /dispute command.
    Opens a dispute for a transaction.
    """
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return ConversationHandler.END
    
    # Check if transaction ID is provided
    if not context.args:
        await update.message.reply_text(
            "Please provide a transaction ID. Usage: /dispute [transaction_id]"
        )
        return ConversationHandler.END
    
    transaction_id = context.args[0]
    transaction = escrow_service.get_transaction(transaction_id)
    
    if not transaction:
        await update.message.reply_text(
            f"Transaction with ID {transaction_id} not found."
        )
        return ConversationHandler.END
    
    # Check if user is part of this transaction
    if user_id != transaction.seller_id and user_id != transaction.buyer_id:
        await update.message.reply_text(
            "You don't have access to this transaction."
        )
        return ConversationHandler.END
    
    # Check if transaction is in a state that can be disputed
    if transaction.status not in [TransactionStatus.FUNDED, TransactionStatus.CONFIRMED]:
        await update.message.reply_text(
            f"Cannot open a dispute for a transaction in '{transaction.status}' status.\n"
            f"Disputes can only be opened for transactions in 'funded' or 'confirmed' status."
        )
        return ConversationHandler.END
    
    # Check if there's already a dispute
    if transaction.status == TransactionStatus.DISPUTED:
        await update.message.reply_text(
            f"A dispute is already open for this transaction.\n"
            f"Use /dispute_details {transaction_id} to view the dispute."
        )
        return ConversationHandler.END
    
    # Initialize dispute data
    dispute_data[user_id] = {
        'transaction_id': transaction_id,
        'user_id': user_id,
        'role': "seller" if user_id == transaction.seller_id else "buyer"
    }
    
    await update.message.reply_text(
        f"You're opening a dispute for transaction `{transaction_id}` ({transaction.title}).\n\n"
        f"Please provide a clear reason for the dispute:",
        parse_mode="Markdown"
    )
    
    return REASON

async def dispute_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle dispute reason input."""
    user_id = update.effective_user.id
    reason = update.message.text.strip()
    
    # Validate reason
    if len(reason) < 10 or len(reason) > 500:
        await update.message.reply_text(
            "Please provide a reason between 10 and 500 characters long."
        )
        return REASON
    
    # Save reason
    dispute_data[user_id]['reason'] = reason
    
    await update.message.reply_text(
        "Thank you. Now, please provide any evidence to support your case.\n\n"
        "This could include:\n"
        "- Screenshots of conversations\n"
        "- References to payment receipts\n"
        "- Any other relevant information\n\n"
        "This will help us resolve the dispute fairly."
    )
    
    return EVIDENCE

async def dispute_evidence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle dispute evidence input."""
    user_id = update.effective_user.id
    evidence = update.message.text.strip()
    
    # Validate evidence
    if len(evidence) < 10:
        await update.message.reply_text(
            "Please provide more detailed evidence."
        )
        return EVIDENCE
    
    # Save evidence
    dispute_data[user_id]['evidence'] = evidence
    
    # Get transaction
    transaction_id = dispute_data[user_id]['transaction_id']
    transaction = escrow_service.get_transaction(transaction_id)
    
    # Open the dispute
    success = escrow_service.open_dispute(
        transaction_id=transaction_id,
        user_id=user_id,
        reason=dispute_data[user_id]['reason'],
        evidence=dispute_data[user_id]['evidence']
    )
    
    if success:
        await update.message.reply_text(
            f"✅ Dispute opened successfully for transaction `{transaction_id}`.\n\n"
            f"Our team will review the dispute and may contact both parties for additional information.\n"
            f"You'll be notified of any updates to the dispute status.",
            parse_mode="Markdown"
        )
        
        # Notify the other party
        other_id = transaction.buyer_id if user_id == transaction.seller_id else transaction.seller_id
        try:
            await context.bot.send_message(
                chat_id=other_id,
                text=(
                    f"⚠️ A dispute has been opened for transaction `{transaction_id}` ({transaction.title}).\n\n"
                    f"Reason: {dispute_data[user_id]['reason']}\n\n"
                    f"Please use /dispute_details {transaction_id} to view the dispute details "
                    f"and provide your response."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {other_id}: {e}")
    else:
        await update.message.reply_text(
            "❌ Failed to open dispute. Please try again later."
        )
    
    # Clean up dispute data
    if user_id in dispute_data:
        del dispute_data[user_id]
    
    return ConversationHandler.END

async def resolve_dispute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /resolve command.
    Resolves a dispute for a transaction (admin only in real implementation).
    """
    user_id = update.effective_user.id
    
    # For demo purposes, we'll allow both parties to resolve disputes
    # In a real implementation, this would be restricted to admins
    
    # Check if user is registered
    if not user_service.get_user(user_id):
        await update.message.reply_text(
            "You need to register first! Use /register to create an account."
        )
        return
    
    # Check if transaction ID is provided
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Please provide a transaction ID and resolution. Usage: /resolve [transaction_id] [buyer|seller|refund]"
        )
        return
    
    transaction_id = context.args[0]
    resolution = context.args[1].lower()
    
    if resolution not in ["buyer", "seller", "refund"]:
        await update.message.reply_text(
            "Invalid resolution. Please use 'buyer', 'seller', or 'refund'."
        )
        return
    
    transaction = escrow_service.get_transaction(transaction_id)
    
    if not transaction:
        await update.message.reply_text(
            f"Transaction with ID {transaction_id} not found."
        )
        return
    
    # Check if transaction is in disputed status
    if transaction.status != TransactionStatus.DISPUTED:
        await update.message.reply_text(
            f"Transaction is not in disputed status."
        )
        return
    
    # Check if user is part of this transaction
    # In a real implementation, this would check for admin privileges
    if user_id != transaction.seller_id and user_id != transaction.buyer_id:
        await update.message.reply_text(
            "You don't have access to this transaction."
        )
        return
    
    # Resolve the dispute
    success = escrow_service.resolve_dispute(
        transaction_id=transaction_id, 
        resolution=resolution
    )
    
    if success:
        if resolution == "buyer":
            outcome = "The funds will be returned to the buyer."
        elif resolution == "seller":
            outcome = "The funds will be released to the seller."
        else:
            outcome = "The funds will be partially refunded according to the agreement."
            
        await update.message.reply_text(
            f"✅ Dispute for transaction `{transaction_id}` has been resolved.\n\n"
            f"Resolution: {resolution.capitalize()}\n"
            f"{outcome}",
            parse_mode="Markdown"
        )
        
        # Notify both parties
        try:
            await context.bot.send_message(
                chat_id=transaction.seller_id,
                text=(
                    f"🔔 The dispute for transaction `{transaction_id}` ({transaction.title}) has been resolved.\n\n"
                    f"Resolution: {resolution.capitalize()}\n"
                    f"{outcome}"
                ),
                parse_mode="Markdown"
            )
            
            await context.bot.send_message(
                chat_id=transaction.buyer_id,
                text=(
                    f"🔔 The dispute for transaction `{transaction_id}` ({transaction.title}) has been resolved.\n\n"
                    f"Resolution: {resolution.capitalize()}\n"
                    f"{outcome}"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify users: {e}")
    else:
        await update.message.reply_text(
            "❌ Failed to resolve dispute. Please try again later."
        )

async def dispute_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /dispute_details command.
    Shows details about a dispute.
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
            "Please provide a transaction ID. Usage: /dispute_details [transaction_id]"
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
    
    # Check if transaction has a dispute
    if transaction.status != TransactionStatus.DISPUTED:
        await update.message.reply_text(
            f"There is no active dispute for transaction `{transaction_id}`.",
            parse_mode="Markdown"
        )
        return
    
    # Get dispute details
    dispute = escrow_service.get_dispute(transaction_id)
    
    if not dispute:
        await update.message.reply_text(
            "Dispute details not found."
        )
        return
    
    # Build dispute details
    user_role = "seller" if user_id == transaction.seller_id else "buyer"
    details = (
        f"*Dispute Details*\n\n"
        f"Transaction: {transaction.title} (`{transaction_id}`)\n"
        f"Status: {dispute['status'].capitalize()}\n"
        f"Opened by: {'Seller' if dispute['opened_by'] == 'seller' else 'Buyer'}\n"
        f"Date Opened: {dispute['opened_at']}\n\n"
        f"*Reason for Dispute:*\n{dispute['reason']}\n\n"
        f"*Evidence:*\n{dispute['evidence']}\n\n"
    )
    
    if dispute['response']:
        details += f"*Counterparty Response:*\n{dispute['response']}\n\n"
    
    if dispute['resolution']:
        details += (
            f"*Resolution:*\n"
            f"Outcome: {dispute['resolution'].capitalize()}\n"
            f"Date Resolved: {dispute['resolved_at']}\n\n"
        )
    
    # Add action buttons if dispute is open
    keyboard = []
    
    if dispute['status'] == DisputeStatus.OPEN:
        # Show different options based on who opened the dispute and the user's role
        if dispute['opened_by'] != user_role:
            # User is responding to the dispute
            keyboard.append([InlineKeyboardButton("Respond to Dispute", callback_data=f"dispute_respond_{transaction_id}")])
        
        # In a real implementation, resolution would be admin-only
        # For demo purposes, let both parties attempt to resolve
        keyboard.append([InlineKeyboardButton("Propose Resolution", callback_data=f"dispute_propose_{transaction_id}")])
    
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

async def dispute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for dispute-related actions.
    """
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("_")
    
    if len(data) < 3:
        await query.edit_message_text("Invalid dispute action.")
        return
    
    action = data[1]
    transaction_id = data[2]
    
    transaction = escrow_service.get_transaction(transaction_id)
    if not transaction:
        await query.edit_message_text(f"Transaction with ID {transaction_id} not found.")
        return
    
    # Check if user is part of this transaction
    if user_id != transaction.seller_id and user_id != transaction.buyer_id:
        await query.edit_message_text("You don't have access to this transaction.")
        return
    
    # View dispute
    if action == "view":
        # Redirect to dispute details
        dispute = escrow_service.get_dispute(transaction_id)
        
        if not dispute:
            await query.edit_message_text("Dispute details not found.")
            return
        
        # Build dispute details
        user_role = "seller" if user_id == transaction.seller_id else "buyer"
        details = (
            f"*Dispute Details*\n\n"
            f"Transaction: {transaction.title} (`{transaction_id}`)\n"
            f"Status: {dispute['status'].capitalize()}\n"
            f"Opened by: {'Seller' if dispute['opened_by'] == 'seller' else 'Buyer'}\n"
            f"Date Opened: {dispute['opened_at']}\n\n"
            f"*Reason for Dispute:*\n{dispute['reason']}\n\n"
            f"*Evidence:*\n{dispute['evidence']}\n\n"
        )
        
        if dispute['response']:
            details += f"*Counterparty Response:*\n{dispute['response']}\n\n"
        
        if dispute['resolution']:
            details += (
                f"*Resolution:*\n"
                f"Outcome: {dispute['resolution'].capitalize()}\n"
                f"Date Resolved: {dispute['resolved_at']}\n\n"
            )
        
        # Add action buttons if dispute is open
        keyboard = []
        
        if dispute['status'] == DisputeStatus.OPEN:
            # Show different options based on who opened the dispute and the user's role
            if dispute['opened_by'] != user_role:
                # User is responding to the dispute
                keyboard.append([InlineKeyboardButton("Respond to Dispute", callback_data=f"dispute_respond_{transaction_id}")])
            
            # In a real implementation, resolution would be admin-only
            # For demo purposes, let both parties attempt to resolve
            keyboard.append([InlineKeyboardButton("Propose Resolution", callback_data=f"dispute_propose_{transaction_id}")])
        
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                details,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                details,
                parse_mode="Markdown"
            )
    
    # Open dispute
    elif action == "open":
        # Redirect to open dispute flow
        await query.edit_message_text(
            f"To open a dispute for transaction `{transaction_id}`, please use:\n\n"
            f"/dispute {transaction_id}",
            parse_mode="Markdown"
        )
    
    # Respond to dispute
    elif action == "respond":
        # This would initiate a conversation to collect the response
        # For simplicity, we'll use a direct prompt
        await query.edit_message_text(
            f"Please send your response to the dispute for transaction `{transaction_id}`.\n\n"
            f"Include any relevant information or evidence that supports your case.",
            parse_mode="Markdown"
        )
        
        # In a real implementation, this would set up a conversation handler
        # For this demo, we'll just acknowledge the intention
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"To respond to the dispute, please use:\n\n"
                f"/respond {transaction_id} [your detailed response]"
            )
        )
    
    # Propose resolution
    elif action == "propose":
        # This would initiate a conversation to collect the proposed resolution
        # For simplicity, we'll use a direct explanation
        resolution_options = (
            f"*Propose a Resolution*\n\n"
            f"To propose a resolution for this dispute, use one of the following commands:\n\n"
            f"/resolve {transaction_id} buyer - Resolve in favor of the buyer\n"
            f"/resolve {transaction_id} seller - Resolve in favor of the seller\n"
            f"/resolve {transaction_id} refund - Partial refund/negotiated solution\n\n"
            f"Note: In a real implementation, this would be handled by a dispute resolution team."
        )
        
        await query.edit_message_text(
            resolution_options,
            parse_mode="Markdown"
        )
    
    else:
        await query.edit_message_text("Unknown dispute operation.")
