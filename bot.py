"""
Bot initialization and configuration module.
Sets up the bot with handlers and necessary configurations.
"""
import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Import handlers
from handlers.user_handlers import start, help_command, register, my_profile
from handlers.transaction_handlers import (
    create_transaction, list_transactions, transaction_details, 
    cancel_transaction, complete_transaction
)
from handlers.payment_handlers import (
    add_payment_method, send_payment, confirm_payment, payment_methods
)
from handlers.dispute_handlers import (
    open_dispute, resolve_dispute, dispute_details
)

logger = logging.getLogger(__name__)

def setup_bot():
    """
    Set up and configure the bot with all necessary handlers.
    Returns the configured Application instance.
    """
    # Get the bot token from environment variables
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")
    
    # Create the Application
    application = ApplicationBuilder().token(token).build()
    
    # Add handlers for user management
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("profile", my_profile))
    
    # Add handlers for transaction management
    application.add_handler(CommandHandler("new", create_transaction))
    application.add_handler(CommandHandler("transactions", list_transactions))
    application.add_handler(CommandHandler("details", transaction_details))
    application.add_handler(CommandHandler("cancel", cancel_transaction))
    application.add_handler(CommandHandler("complete", complete_transaction))
    
    # Add handlers for payment management
    application.add_handler(CommandHandler("payment_methods", payment_methods))
    application.add_handler(CommandHandler("add_payment", add_payment_method))
    application.add_handler(CommandHandler("pay", send_payment))
    application.add_handler(CommandHandler("confirm_payment", confirm_payment))
    
    # Add handlers for dispute management
    application.add_handler(CommandHandler("dispute", open_dispute))
    application.add_handler(CommandHandler("resolve", resolve_dispute))
    application.add_handler(CommandHandler("dispute_details", dispute_details))
    
    # Add callback query handler for button interactions
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Log setup completion
    logger.info("Bot handlers configured successfully")
    
    return application

async def button_callback(update, context):
    """
    Handle button callbacks from inline keyboards.
    Routes the callback to the appropriate handler based on the callback data prefix.
    """
    query = update.callback_query
    data = query.data
    
    # Acknowledge the callback
    await query.answer()
    
    try:
        # Route to appropriate handler based on callback data prefix
        if data.startswith("txn_"):
            from handlers.transaction_handlers import transaction_callback
            return await transaction_callback(update, context)
        elif data.startswith("pay_"):
            from handlers.payment_handlers import payment_callback
            return await payment_callback(update, context)
        elif data.startswith("dispute_"):
            from handlers.dispute_handlers import dispute_callback
            return await dispute_callback(update, context)
        elif data.startswith("user_"):
            from handlers.user_handlers import user_callback
            return await user_callback(update, context)
        else:
            await query.edit_message_text(text="❌ Unknown callback operation.")
            return
    except Exception as e:
        logger.error(f"Error in button callback: {e}")
        await query.edit_message_text(text="❌ An error occurred. Please try again.")
