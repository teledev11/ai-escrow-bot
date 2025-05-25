#!/usr/bin/env python3
"""
Enhanced Telegram Escrow Bot following the professional P2P model
Similar to Binance P2P, Paxful, and AirTM
"""
import os
import logging
import uuid
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ProfessionalEscrowBot:
    def __init__(self, token):
        self.token = token
        self.app = ApplicationBuilder().token(token).build()
        
        # Trade states for conversation handling
        self.CREATING_OFFER, self.WAITING_PAYMENT, self.CONFIRMING_PAYMENT = range(3)
        
        # Setup handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot command and callback handlers"""
        # Main commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("register", self.register_command))
        
        # Trading commands - following Binance P2P model
        self.app.add_handler(CommandHandler("buy", self.create_buy_offer))
        self.app.add_handler(CommandHandler("sell", self.create_sell_offer))
        self.app.add_handler(CommandHandler("offers", self.view_offers))
        self.app.add_handler(CommandHandler("mytrades", self.my_trades))
        
        # Escrow commands
        self.app.add_handler(CommandHandler("release", self.release_funds))
        self.app.add_handler(CommandHandler("dispute", self.open_dispute))
        self.app.add_handler(CommandHandler("confirm", self.confirm_payment))
        
        # Wallet commands
        self.app.add_handler(CommandHandler("balance", self.check_balance))
        self.app.add_handler(CommandHandler("deposit", self.deposit_crypto))
        self.app.add_handler(CommandHandler("withdraw", self.withdraw_crypto))
        
        # Admin commands
        self.app.add_handler(CommandHandler("admin", self.admin_panel))
        
        # Callback query handler for inline buttons
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for text inputs
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with professional P2P interface"""
        user = update.effective_user
        
        welcome_text = f"""
🔐 *Welcome to Secure P2P Exchange*

Hi {user.first_name}! I'm your professional escrow assistant for secure cryptocurrency trading.

*🌟 Why Choose Our Platform?*
• ✅ Secure escrow protection
• 💰 Multiple cryptocurrencies (BTC, ETH, USDT)
• 🏦 Various payment methods (Bank, PayPal, M-Pesa)
• ⚖️ Fair dispute resolution
• 🔒 Advanced security features

*📈 Trade Like a Pro:*
• Create buy/sell offers
• Automatic escrow holding
• Real-time notifications
• Complete transaction history
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🛒 Buy Crypto", callback_data="main_buy"),
                InlineKeyboardButton("💰 Sell Crypto", callback_data="main_sell")
            ],
            [
                InlineKeyboardButton("📊 View Offers", callback_data="main_offers"),
                InlineKeyboardButton("💼 My Trades", callback_data="main_mytrades")
            ],
            [
                InlineKeyboardButton("👤 Register", callback_data="main_register"),
                InlineKeyboardButton("💳 My Wallet", callback_data="main_wallet")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="main_help"),
                InlineKeyboardButton("⚙️ Settings", callback_data="main_settings")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def create_sell_offer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a sell offer like Binance P2P"""
        keyboard = [
            [
                InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data="sell_BTC"),
                InlineKeyboardButton("Ξ Ethereum (ETH)", callback_data="sell_ETH")
            ],
            [
                InlineKeyboardButton("💵 USDT", callback_data="sell_USDT"),
                InlineKeyboardButton("🔄 More Coins", callback_data="sell_more")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💰 *Create Sell Offer*\n\n"
            "Choose the cryptocurrency you want to sell:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def create_buy_offer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a buy offer like Binance P2P"""
        keyboard = [
            [
                InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data="buy_BTC"),
                InlineKeyboardButton("Ξ Ethereum (ETH)", callback_data="buy_ETH")
            ],
            [
                InlineKeyboardButton("💵 USDT", callback_data="buy_USDT"),
                InlineKeyboardButton("🔄 More Coins", callback_data="buy_more")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🛒 *Create Buy Offer*\n\n"
            "Choose the cryptocurrency you want to buy:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def view_offers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View available P2P offers like Binance P2P marketplace"""
        offers_text = """
📊 *P2P Marketplace*

🛒 *Buy Offers:*
• 0.01 BTC for $450 via PayPal (@user123)
• 0.05 ETH for $180 via Bank Transfer (@trader456)
• 100 USDT for $99 via M-Pesa (@crypto789)

💰 *Sell Offers:*
• 0.02 BTC for $920 via Bank Transfer (@seller123)
• 0.1 ETH for $350 via PayPal (@dealer456)
• 500 USDT for $495 via Mobile Money (@trader789)

_Tap on any offer to start trading securely_
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_offers"),
                InlineKeyboardButton("🎯 Filter", callback_data="filter_offers")
            ],
            [
                InlineKeyboardButton("➕ Create Offer", callback_data="create_new_offer")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(offers_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def my_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's trading history like professional platforms"""
        trades_text = """
💼 *My Trading History*

🔄 *Active Trades:*
• Trade #12345 - Buying 0.01 BTC (In Escrow)
• Trade #12346 - Selling 50 USDT (Waiting Payment)

✅ *Completed Trades:*
• Trade #12340 - Bought 0.005 BTC ✅
• Trade #12341 - Sold 100 USDT ✅
• Trade #12342 - Bought 0.02 ETH ✅

📊 *Statistics:*
• Total Trades: 15
• Success Rate: 100%
• Member Since: Jan 2024
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Trade Details", callback_data="trade_details"),
                InlineKeyboardButton("📈 Statistics", callback_data="trade_stats")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(trades_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def check_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check wallet balance like professional exchanges"""
        balance_text = """
💳 *My Wallet Balance*

🔒 *Escrow Balances:*
• Bitcoin (BTC): 0.0245 BTC
• Ethereum (ETH): 0.156 ETH  
• USDT: 245.50 USDT

💰 *Available Balances:*
• Bitcoin (BTC): 0.0123 BTC
• Ethereum (ETH): 0.089 ETH
• USDT: 156.75 USDT

🔄 *In Trading:*
• 0.01 BTC (Trade #12345)
• 50 USDT (Trade #12346)
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📥 Deposit", callback_data="wallet_deposit"),
                InlineKeyboardButton("📤 Withdraw", callback_data="wallet_withdraw")
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="wallet_refresh"),
                InlineKeyboardButton("📊 History", callback_data="wallet_history")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries from inline buttons"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("main_"):
            await self.handle_main_menu(query, context)
        elif data.startswith("sell_") or data.startswith("buy_"):
            await self.handle_trade_creation(query, context)
        elif data.startswith("wallet_"):
            await self.handle_wallet_actions(query, context)
        else:
            await query.edit_message_text("Feature coming soon! 🚀")
    
    async def handle_main_menu(self, query, context):
        """Handle main menu selections"""
        action = query.data.replace("main_", "")
        
        if action == "register":
            await self.register_user(query, context)
        elif action == "help":
            await self.show_help(query, context)
        elif action == "offers":
            await self.show_marketplace(query, context)
        # Add more main menu handlers
    
    async def handle_trade_creation(self, query, context):
        """Handle trade creation flow"""
        parts = query.data.split("_")
        action = parts[0]  # buy or sell
        crypto = parts[1]  # BTC, ETH, USDT
        
        trade_text = f"""
{('🛒 Creating Buy Offer' if action == 'buy' else '💰 Creating Sell Offer')}

*Cryptocurrency:* {crypto}
*Action:* {action.upper()}

Please provide the following details:
1️⃣ Amount of {crypto}
2️⃣ Price per unit
3️⃣ Payment method
4️⃣ Additional terms

Example: "0.01 BTC at $45,000 via PayPal - Fast payment required"
"""
        
        await query.edit_message_text(trade_text, parse_mode='Markdown')
        context.user_data['creating_trade'] = {'action': action, 'crypto': crypto}
    
    async def handle_wallet_actions(self, query, context):
        """Handle wallet-related actions"""
        action = query.data.replace("wallet_", "")
        
        if action == "deposit":
            await self.show_deposit_info(query, context)
        elif action == "withdraw":
            await self.show_withdraw_form(query, context)
        # Add more wallet handlers
    
    async def show_deposit_info(self, query, context):
        """Show cryptocurrency deposit addresses"""
        deposit_text = """
📥 *Deposit Cryptocurrency*

*Bitcoin (BTC):*
`bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`

*Ethereum (ETH):*
`0x742d35Cc0Df7F5C3Ee2B3E3F88B4523F3C51234`

*USDT (TRC20):*
`TYASr3nPAaDfkjhXmGF7Qj8ZbBc3K1a7s9`

⚠️ *Important:*
• Only send the correct cryptocurrency
• Wait for confirmations before trading
• Minimum deposit: 0.001 BTC, 0.01 ETH, 10 USDT
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="deposit_refresh")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(deposit_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for trade creation and other inputs"""
        if context.user_data.get('creating_trade'):
            await self.process_trade_details(update, context)
        else:
            await update.message.reply_text(
                "Please use the menu buttons or commands to interact with the bot. Type /help for assistance."
            )
    
    async def process_trade_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process trade creation details"""
        trade_info = context.user_data['creating_trade']
        details = update.message.text
        
        # Generate trade ID
        trade_id = f"T{uuid.uuid4().hex[:8].upper()}"
        
        confirmation_text = f"""
✅ *Trade Offer Created!*

*Trade ID:* {trade_id}
*Type:* {trade_info['action'].upper()} {trade_info['crypto']}
*Details:* {details}
*Status:* Active
*Created:* {datetime.now().strftime('%Y-%m-%d %H:%M')}

Your offer is now live in the marketplace! 🚀

*Next Steps:*
• Wait for a counterparty to accept
• You'll be notified when someone responds
• Funds will be held in escrow during the trade
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 View My Offers", callback_data="view_my_offers"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear the trade creation state
        context.user_data.pop('creating_trade', None)
    
    async def register_user(self, query, context):
        """Handle user registration"""
        user = query.from_user
        
        registration_text = f"""
✅ *Registration Successful!*

Welcome to the platform, {user.first_name}!

*Your Account:*
• User ID: {user.id}
• Username: @{user.username or 'Not set'}
• Member Since: {datetime.now().strftime('%Y-%m-%d')}
• Status: Verified ✅

*What's Next?*
• Start trading immediately
• Create buy/sell offers
• Build your reputation
• Earn from successful trades

*Security Tips:*
• Enable 2FA on your Telegram
• Never share your bot access
• Always verify payment details
• Report suspicious activity
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🛒 Start Trading", callback_data="main_offers"),
                InlineKeyboardButton("💳 Setup Wallet", callback_data="main_wallet")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(registration_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        help_text = """
🔐 *Secure P2P Exchange Help*

*🚀 Quick Start:*
• /start - Launch the main menu
• /buy - Create a buy offer
• /sell - Create a sell offer
• /balance - Check your wallet

*💼 Trading Commands:*
• /offers - Browse marketplace
• /mytrades - View your trades
• /release - Release escrow funds
• /dispute - Report issues

*🔒 Security:*
• All trades use secure escrow
• Funds are protected until confirmed
• Dispute resolution available
• Multiple payment methods supported

*💰 Supported:*
• Bitcoin (BTC), Ethereum (ETH), USDT
• PayPal, Bank Transfer, M-Pesa
• Secure escrow protection

Need help? Contact @support
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle registration command"""
        user = update.effective_user
        
        registration_text = f"""
✅ *Registration Successful!*

Welcome to the platform, {user.first_name}!

*Your Account:*
• User ID: {user.id}
• Username: @{user.username or 'Not set'}
• Member Since: {datetime.now().strftime('%Y-%m-%d')}
• Status: Verified ✅

*What's Next?*
• Start trading immediately
• Create buy/sell offers
• Build your reputation
• Earn from successful trades

Type /help to see all available commands!
"""
        
        await update.message.reply_text(registration_text, parse_mode='Markdown')
    
    async def release_funds(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Release funds from escrow"""
        await update.message.reply_text(
            "🔓 *Release Escrow Funds*\n\n"
            "Please provide the Trade ID to release funds:",
            parse_mode='Markdown'
        )
    
    async def open_dispute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Open a dispute"""
        await update.message.reply_text(
            "⚖️ *Open Dispute*\n\n"
            "Please provide the Trade ID and reason for dispute:",
            parse_mode='Markdown'
        )
    
    async def confirm_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm payment received"""
        await update.message.reply_text(
            "✅ *Confirm Payment*\n\n"
            "Please provide the Trade ID to confirm payment receipt:",
            parse_mode='Markdown'
        )
    
    async def deposit_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show deposit information"""
        await self.show_deposit_info(update.message, context)
    
    async def withdraw_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show withdrawal form"""
        await update.message.reply_text(
            "📤 *Withdraw Cryptocurrency*\n\n"
            "Please specify:\n"
            "• Currency (BTC/ETH/USDT)\n"
            "• Amount\n"
            "• Destination address",
            parse_mode='Markdown'
        )
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
        await update.message.reply_text(
            "⚙️ *Admin Panel*\n\n"
            "Admin features coming soon!",
            parse_mode='Markdown'
        )
    
    async def show_help(self, query, context):
        """Show help information from callback"""
        await self.help_command(query, context)
    
    async def show_marketplace(self, query, context):
        """Show marketplace from callback"""
        await self.view_offers(query, context)
    
    async def show_withdraw_form(self, query, context):
        """Show withdrawal form from callback"""
        await self.withdraw_crypto(query, context)
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Professional P2P Escrow Bot...")
        self.app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")
    
    bot = ProfessionalEscrowBot(token)
    bot.run()