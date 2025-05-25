"""
User management handlers for the Telegram Escrow Bot.
Handles user commands like start, help, register, and profile management.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.user import User
from services.user_service import UserService
from config import HELP_MESSAGE

logger = logging.getLogger(__name__)
user_service = UserService()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    Introduces the bot and guides new users to register.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # Check if user is already registered
    if user_service.get_user(user_id):
        # Enhanced welcome back message with quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("💰 New Transaction", callback_data="txn_new"),
                InlineKeyboardButton("📋 My Transactions", callback_data="user_transactions")
            ],
            [
                InlineKeyboardButton("👤 My Profile", callback_data="user_profile"),
                InlineKeyboardButton("❓ Help", callback_data="user_help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔒 *Welcome back to the Escrow Assistant*, {first_name}!\n\n"
            f"What would you like to do today?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        # Enhanced registration button with better design
        keyboard = [
            [InlineKeyboardButton("✅ Register Now", callback_data="user_register")],
            [InlineKeyboardButton("❓ How It Works", callback_data="user_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send welcome message with improved formatting and visuals
        welcome_text = (
            f"🔐 *Welcome to the Secure Escrow Assistant!*\n\n"
            f"Hi {first_name}! I'm your personal escrow assistant for secure digital transactions.\n\n"
            f"*What I can do for you:*\n"
            f"• Create secure escrow transactions\n"
            f"• Protect buyers and sellers\n"
            f"• Support multiple payment methods\n"
            f"• Provide fair dispute resolution\n\n"
            f"To get started, please register with a simple click below!"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.
    Provides a list of available commands and their descriptions.
    """
    from config import HELP_MESSAGE, TRANSACTION_HELP, PAYMENT_HELP, DISPUTE_HELP
    
    # Check if a specific help topic is requested
    if context.args and len(context.args) > 0:
        topic = context.args[0].lower()
        
        if topic in ["transaction", "transactions", "tx"]:
            # Show transaction-specific help
            keyboard = [
                [InlineKeyboardButton("↩️ Back to Main Help", callback_data="help_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                TRANSACTION_HELP,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
            
        elif topic in ["payment", "payments", "pay"]:
            # Show payment-specific help
            keyboard = [
                [InlineKeyboardButton("↩️ Back to Main Help", callback_data="help_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                PAYMENT_HELP,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
            
        elif topic in ["dispute", "disputes", "resolution"]:
            # Show dispute-specific help
            keyboard = [
                [InlineKeyboardButton("↩️ Back to Main Help", callback_data="help_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                DISPUTE_HELP,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
    
    # Show main help with category selection buttons
    keyboard = [
        [
            InlineKeyboardButton("📝 Transaction Guide", callback_data="help_transaction"),
            InlineKeyboardButton("💸 Payment Guide", callback_data="help_payment")
        ],
        [
            InlineKeyboardButton("⚖️ Dispute Resolution", callback_data="help_dispute"),
            InlineKeyboardButton("👤 Account Help", callback_data="help_profile")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        HELP_MESSAGE,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /register command.
    Registers a new user in the system.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name or ""
    
    # Check if user is already registered
    if user_service.get_user(user_id):
        await update.message.reply_text(
            "You are already registered! Use /profile to see your profile information."
        )
        return
    
    # Create a new user
    new_user = User(
        id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    
    # Register the user
    success = user_service.register_user(new_user)
    
    if success:
        await update.effective_chat.send_message(
            f"✅ Registration successful! Welcome, {first_name}!\n\n"
            f"Your account is now ready to use. Type /help to see available commands."
        )
    else:
        await update.message.reply_text(
            "❌ Registration failed. Please try again later or contact support."
        )

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /profile command.
    Displays the user's profile information and statistics.
    """
    user_id = update.effective_user.id
    user = user_service.get_user(user_id)
    
    if not user:
        # Enhanced UI for registration prompt
        keyboard = [
            [InlineKeyboardButton("✅ Register Now", callback_data="user_register")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ You need to register first to access your profile!\n\n"
            "Registration takes just a few seconds and allows you to use all the features of our escrow service.",
            reply_markup=reply_markup
        )
        return
    
    # Get user transaction statistics
    stats = user_service.get_user_stats(user_id)
    
    # Format date properly, handling string or datetime object
    if isinstance(user.created_at, str):
        registered_date = user.created_at.split('T')[0] if 'T' in user.created_at else user.created_at
    else:
        try:
            registered_date = user.created_at.strftime('%Y-%m-%d')
        except:
            registered_date = "Unknown"
    
    # Enhanced profile view with better formatting and emoji
    profile_text = (
        f"👤 *Your Profile*\n\n"
        f"Username: @{user.username}\n"
        f"Name: {user.first_name} {user.last_name}\n"
        f"Registered: {registered_date}\n\n"
        f"📊 *Transaction Statistics*\n"
        f"💼 Total Transactions: {stats['total_transactions']}\n"
        f"🛒 As Buyer: {stats['as_buyer']}\n"
        f"💰 As Seller: {stats['as_seller']}\n"
        f"✅ Completed: {stats['completed']}\n"
        f"⏳ Active: {stats['active']}\n"
        f"⚠️ Disputed: {stats['disputed']}\n\n"
        f"💵 *Wallet Balance*\n"
        f"🔒 Escrow Balance: ${stats['escrow_balance']:.2f}"
    )
    
    # Enhanced action buttons with better UI
    keyboard = [
        [
            InlineKeyboardButton("💳 Payment Methods", callback_data="user_payment_methods"),
            InlineKeyboardButton("📋 My Transactions", callback_data="user_transactions")
        ],
        [
            InlineKeyboardButton("➕ Create New Transaction", callback_data="transaction_new")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        profile_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries related to user management.
    """
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data
    
    # Log callback data for debugging
    logger.debug(f"User callback received: {callback_data} from user {user_id}")
    
    # Extract action from callback data
    if "_" in callback_data:
        action = callback_data.split("_")[1]
    else:
        action = callback_data
    
    if action == "register":
        # First, acknowledge the callback to prevent Telegram timeout
        await query.answer()
        
        # Show a processing message
        await query.edit_message_text(
            "⏳ *Setting up your account...*\n\n"
            "Please wait while we create your secure escrow account.",
            parse_mode="Markdown"
        )
        
        try:
            # Trigger the registration flow with enhanced visuals
            # Check if username is provided
            if not query.from_user.username:
                await query.edit_message_text(
                    "⚠️ *Username Required*\n\n"
                    "To complete registration, you need to set a Telegram username first.\n\n"
                    "1. Go to your Telegram Settings\n"
                    "2. Tap on your profile\n"
                    "3. Add a username\n"
                    "4. Come back and try again!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Try Again", callback_data="user_register")]
                    ])
                )
                return
                
            # Create user object with proper error handling
            try:
                user = User(
                    id=user_id,
                    username=query.from_user.username or f"user{user_id}",  # Fallback username if needed
                    first_name=query.from_user.first_name or "User",  # Default if missing
                    last_name=query.from_user.last_name or ""
                )
                
                # Log registration attempt
                logger.info(f"Attempting to register user: {user_id}, username: {user.username}")
                
                # Try to register the user
                success = user_service.register_user(user)
                
                if success:
                    # Enhanced success message with quick action buttons
                    keyboard = [
                        [
                            InlineKeyboardButton("💰 Create Transaction", callback_data="transaction_new"),
                            InlineKeyboardButton("📋 View Commands", callback_data="help_command")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"✅ *Registration Successful!*\n\n"
                        f"Welcome to the Escrow Service, *{user.first_name}*!\n\n"
                        f"Your account is now active and ready to use.\n\n"
                        f"🔑 *Account ID:* `{user.id}`\n"
                        f"👤 *Username:* @{user.username}\n\n"
                        f"What would you like to do next?",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                else:
                    # Enhanced error message with retry option
                    keyboard = [
                        [InlineKeyboardButton("🔄 Try Again", callback_data="user_register")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    logger.error(f"Failed to register user {user_id}")
                    
                    await query.edit_message_text(
                        "❌ *Registration Issue*\n\n"
                        "We encountered a problem while setting up your account.\n\n"
                        "This could be due to a temporary system issue. Please try again or contact support if the problem persists.",
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error creating user object: {e}")
                # Show a user-friendly error
                await query.edit_message_text(
                    "❌ *Registration Error*\n\n"
                    "An unexpected error occurred while processing your registration.\n\n"
                    "Please try again in a few moments.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Try Again", callback_data="user_register")]
                    ]),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Unhandled exception in registration: {e}")
            # If we get here, something really went wrong
            try:
                await query.edit_message_text(
                    "❌ *System Error*\n\n"
                    "Something went wrong on our end.\n\n"
                    "Please try again later.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back to Start", callback_data="back_to_start")]
                    ]),
                    parse_mode="Markdown"
                )
            except:
                # Last resort if we can't even edit the message
                pass
    
    elif action == "profile":
        # Show user profile directly via callback
        user = user_service.get_user(user_id)
        if user:
            # Get user transaction statistics
            stats = user_service.get_user_stats(user_id)
            
            # Format date properly
            if isinstance(user.created_at, str):
                registered_date = user.created_at.split('T')[0] if 'T' in user.created_at else user.created_at
            else:
                try:
                    registered_date = user.created_at.strftime('%Y-%m-%d')
                except:
                    registered_date = "Unknown"
            
            # Enhanced profile view with better formatting and emoji
            profile_text = (
                f"👤 *Your Profile*\n\n"
                f"Username: @{user.username}\n"
                f"Name: {user.first_name} {user.last_name}\n"
                f"Registered: {registered_date}\n\n"
                f"📊 *Transaction Statistics*\n"
                f"💼 Total Transactions: {stats['total_transactions']}\n"
                f"🛒 As Buyer: {stats['as_buyer']}\n"
                f"💰 As Seller: {stats['as_seller']}\n"
                f"✅ Completed: {stats['completed']}\n"
                f"⏳ Active: {stats['active']}\n"
                f"⚠️ Disputed: {stats['disputed']}\n\n"
                f"💵 *Wallet Balance*\n"
                f"🔒 Escrow Balance: ${stats['escrow_balance']:.2f}"
            )
            
            # Enhanced action buttons with better UI
            keyboard = [
                [
                    InlineKeyboardButton("💳 Payment Methods", callback_data="user_payment_methods"),
                    InlineKeyboardButton("📋 My Transactions", callback_data="user_transactions")
                ],
                [
                    InlineKeyboardButton("➕ Create New Transaction", callback_data="transaction_new")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                profile_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            # User not found, prompt registration
            keyboard = [
                [InlineKeyboardButton("✅ Register Now", callback_data="user_register")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚠️ You need to register first to view your profile!",
                reply_markup=reply_markup
            )
    
    elif action == "payment_methods":
        # Redirect to payment methods view
        from handlers.payment_handlers import show_payment_methods
        await show_payment_methods(update, context)
    
    elif action == "transactions":
        # Redirect to transactions list
        from handlers.transaction_handlers import show_transactions
        await show_transactions(update, context)
        
    elif action == "how_it_works":
        # Show how the escrow system works
        how_it_works_text = (
            "🔄 *How Our Escrow System Works*\n\n"
            "*For Sellers:*\n"
            "1️⃣ Create a new transaction with `/new`\n"
            "2️⃣ Set details, price, and payment method\n"
            "3️⃣ Share the transaction ID with buyer\n"
            "4️⃣ Deliver goods/services when notified\n"
            "5️⃣ Receive funds after buyer confirmation\n\n"
            
            "*For Buyers:*\n"
            "1️⃣ Join transaction with provided ID\n"
            "2️⃣ Review details carefully\n"
            "3️⃣ Fund the escrow account\n"
            "4️⃣ Receive goods/services from seller\n"
            "5️⃣ Confirm receipt to release payment\n\n"
            
            "🔒 *Your Security Guarantee:*\n"
            "• Funds held in secure escrow\n"
            "• Fair dispute resolution\n"
            "• No payments released until both parties agree\n"
            "• Complete transparency throughout process"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Register Now", callback_data="user_register")],
            [InlineKeyboardButton("◀️ Back", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            how_it_works_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif action == "back_to_start":
        # Return to start message
        first_name = query.from_user.first_name
        keyboard = [
            [InlineKeyboardButton("✅ Register Now", callback_data="user_register")],
            [InlineKeyboardButton("❓ How It Works", callback_data="help_how_it_works")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"🔐 *Welcome to the Secure Escrow Assistant!*\n\n"
            f"Hi {first_name}! I'm your personal escrow assistant for secure digital transactions.\n\n"
            f"*What I can do for you:*\n"
            f"• Create secure escrow transactions\n"
            f"• Protect buyers and sellers\n"
            f"• Support multiple payment methods\n"
            f"• Provide fair dispute resolution\n\n"
            f"To get started, please register with a simple click below!"
        )
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Handle help-related callbacks
    elif action in ["main", "transaction", "payment", "dispute", "profile"]:
        from config import HELP_MESSAGE, TRANSACTION_HELP, PAYMENT_HELP, DISPUTE_HELP
        
        if action == "main":
            # Return to main help menu
            keyboard = [
                [
                    InlineKeyboardButton("📝 Transaction Guide", callback_data="help_transaction"),
                    InlineKeyboardButton("💸 Payment Guide", callback_data="help_payment")
                ],
                [
                    InlineKeyboardButton("⚖️ Dispute Resolution", callback_data="help_dispute"),
                    InlineKeyboardButton("👤 Account Help", callback_data="help_profile")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                HELP_MESSAGE,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        elif action == "transaction":
            # Show transaction help
            keyboard = [
                [InlineKeyboardButton("↩️ Back to Main Help", callback_data="help_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                TRANSACTION_HELP,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        elif action == "payment":
            # Show payment help
            keyboard = [
                [InlineKeyboardButton("↩️ Back to Main Help", callback_data="help_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                PAYMENT_HELP,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        elif action == "dispute":
            # Show dispute help
            keyboard = [
                [InlineKeyboardButton("↩️ Back to Main Help", callback_data="help_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                DISPUTE_HELP,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        elif action == "profile":
            # Show account help
            profile_help = """
🧩 *ACCOUNT MANAGEMENT GUIDE*

*Account Features:*
• View your transaction history
• Manage payment methods
• Check escrow wallet balance
• See dispute status

*Commands:*
• `/profile` - View your profile dashboard
• `/payment_methods` - Manage your payment details
• `/help` - Access this help system

Your profile is your control center for all escrow transactions and activities. Keep your payment methods up to date for smooth transactions.
            """
            
            keyboard = [
                [InlineKeyboardButton("↩️ Back to Main Help", callback_data="help_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                profile_help,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
    else:
        # For unknown actions
        await query.answer("Unknown operation", show_alert=True)
        
    # Answer the callback query to remove the loading state
    try:
        await query.answer()
    except:
        pass  # Already answered above
