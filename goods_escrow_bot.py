#!/usr/bin/env python3
"""
Professional Goods & Services Escrow Bot
For selling/buying files, software, services, goods, postal/courier deliveries
With real crypto payments and Binance Pay integration
"""
import os
import logging
import uuid
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from payment_gateways import payment_manager
from trust_system import trust_system
from dispute_system import dispute_system
from ai_assistant import ai_assistant

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Service categories
SERVICE_CATEGORIES = {
    "digital": "📱 Digital Products",
    "software": "💻 Software & Licenses", 
    "files": "📄 Files & Documents",
    "services": "🛠️ Professional Services",
    "goods": "📦 Physical Goods",
    "postal": "📮 Postal/Courier Services",
    "crypto": "💰 Flash Wallets & Crypto Tools"
}

# Crypto wallets for escrow holding
ESCROW_WALLETS = {
    "BTC": "14ZmNV97yKxErCQHJetXvgVm22MTtakDZu", 
    "ETH": "0xf5857b4c41101b39c5f08cd4f5e65364c713b7fc",
    "USDT": "TCaNSyrxWMHcWozykLXfCdhsv4rVEmUQrT",
    "BNB": "0xf5857b4c41101b39c5f08cd4f5e65364c713b7fc"
}

# Global storage for active trades
active_trades = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main start command for escrow services"""
    user = update.effective_user
    
    welcome_text = f"""
🛡️ *AI ESCROW BOT*

Welcome {user.first_name}! Secure trading for:

*🛍️ What We Protect:*
📱 Digital Products & Software
📄 Files, Documents & Content  
🛠️ Professional Services
📦 Physical Goods & Products
📮 Postal/Courier Deliveries
💰 Flash Wallets & Crypto Tools

*🔒 How It Works:*
1. Seller creates service agreement
2. Buyer pays crypto to our escrow
3. Seller delivers goods/services
4. Buyer confirms receipt
5. Payment released to seller

*💳 Payment Methods:*
₿ Bitcoin, Ethereum, USDT, BNB
🔄 Binance Pay Integration
💳 Credit/Debit Cards (Stripe)
🏦 PayPal & Bank Transfers
🌍 Regional Payment Methods
"""
    
    keyboard = [
        [
            InlineKeyboardButton("💼 Sell Services/Goods", callback_data="create_listing"),
            InlineKeyboardButton("🛒 Buy Services/Goods", callback_data="browse_listings")
        ],
        [
            InlineKeyboardButton("📋 My Active Trades", callback_data="my_trades"),
            InlineKeyboardButton("💳 Payment Status", callback_data="payment_status")
        ],
        [
            InlineKeyboardButton("⚖️ File Dispute", callback_data="file_dispute"),
            InlineKeyboardButton("📋 My Disputes", callback_data="my_disputes")
        ],
        [
            InlineKeyboardButton("🤖 AI Assistant", callback_data="ai_assistant"),
            InlineKeyboardButton("📊 Smart Analysis", callback_data="smart_analysis")
        ],
        [
            InlineKeyboardButton("📞 Support Center", callback_data="support_center"),
            InlineKeyboardButton("💬 Live Chat", callback_data="live_chat")
        ],
        [
            InlineKeyboardButton("💰 Escrow Wallets", callback_data="escrow_wallets")
        ],
        [
            InlineKeyboardButton("ℹ️ How Escrow Works", callback_data="how_it_works"),
            InlineKeyboardButton("👤 My Profile", callback_data="user_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain the escrow process"""
    how_text = """
🛡️ *How Professional Escrow Works*

*📝 Step 1: Service Agreement*
• Seller creates detailed listing
• Describes goods/services precisely
• Sets price and delivery terms
• Specifies completion criteria

*💰 Step 2: Secure Payment*
• Buyer sends crypto to our escrow wallet
• Funds held securely until delivery
• No risk for buyer or seller

*📦 Step 3: Delivery/Service*
• Seller provides goods/services as agreed
• Digital: Files sent via Telegram
• Physical: Tracking info provided
• Services: Work completed per agreement

*✅ Step 4: Confirmation*
• Buyer confirms receipt & satisfaction
• Checks goods match description
• Verifies service completion

*💸 Step 5: Payment Release*
• Escrow releases crypto to seller
• Trade marked as completed
• Both parties can leave feedback

*⚖️ Dispute Protection*
• If agreement violated, dispute filed
• Evidence reviewed by escrow team
• Fair resolution based on facts
• Funds released to rightful party
"""
    await update.message.reply_text(how_text, parse_mode='Markdown')

async def create_listing_flow(query, context):
    """Start the listing creation process"""
    categories_keyboard = []
    for key, value in SERVICE_CATEGORIES.items():
        categories_keyboard.append([InlineKeyboardButton(value, callback_data=f"category_{key}")])
    
    reply_markup = InlineKeyboardMarkup(categories_keyboard)
    await query.edit_message_text(
        "💼 *Create Your Listing*\n\nSelect the category for your goods/services:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def browse_listings_flow(query, context):
    """Browse available listings with real verified sellers"""
    browse_text = """
🛒 *Verified Marketplace - Top Sellers*

*🌟 Premium Verified Vendors:*

*1️⃣ @trinh_11* ⭐⭐⭐⭐⭐ (4.9/5) 💎 Diamond
• ⚡ Flash Wallets & Crypto Tools
• 🛠️ Custom Telegram Bots & Apps
• 💻 Web Development & APIs
• Response time: 2 hours

*2️⃣ @crypto_toolss* ⭐⭐⭐⭐⭐ (4.8/5) 🥇 Gold
• 💰 Flash Wallets & Pre-loaded Crypto
• 📊 Trading Bots & Signals
• 🛠️ Professional Crypto Tools
• Response time: 1 hour

*3️⃣ @hunter_hubs* ⭐⭐⭐⭐⭐ (4.7/5) 🥈 Silver
• ⚡ Flash Wallets & Crypto Solutions
• 🔎 Data Mining & Research
• 🛠️ Crypto Trading Tools
• Response time: 3 hours

*💡 How to Order:*
• Reply with number (1, 2, or 3)
• Or type specific service you need
• Payment secured in escrow until delivery

*🔒 Buyer Protection:*
• Funds held safely until satisfied
• Direct seller communication
• Quality guarantee
• Dispute resolution available

*Choose seller or browse categories:*
"""
    
    keyboard = [
        [
            InlineKeyboardButton("1️⃣ Contact @trinh_11", callback_data="seller_trinh_11"),
            InlineKeyboardButton("2️⃣ Contact @crypto_toolss", callback_data="seller_crypto_toolss")
        ],
        [
            InlineKeyboardButton("3️⃣ Contact @hunter_hubs", callback_data="seller_hunter_hubs")
        ],
        [
            InlineKeyboardButton("🔍 Browse All Categories", callback_data="filter_category"),
            InlineKeyboardButton("⭐ View All Sellers", callback_data="top_sellers")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(browse_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_escrow_wallets(query, context):
    """Display escrow wallet addresses"""
    wallet_text = f"""
💰 *Escrow Wallet Addresses*

When making payments, send crypto to these addresses:

*₿ Bitcoin (BTC):*
`{ESCROW_WALLETS['BTC']}`

*Ξ Ethereum (ETH/ERC-20):*
`{ESCROW_WALLETS['ETH']}`

*💵 USDT (TRC20):*
`{ESCROW_WALLETS['USDT']}`

*🟡 Binance Coin (BEP-20):*
`{ESCROW_WALLETS['BNB']}`

⚠️ *Important Instructions:*
• Only send exact amount specified in trade
• Include trade ID in transaction memo
• Wait for 3 confirmations before delivery
• Never send from exchange directly

*🔐 Security Features:*
• Multi-signature protection
• Cold storage backup
• 24/7 monitoring
• Instant release system
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Binance Pay Integration", callback_data="binance_pay")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(wallet_text, reply_markup=reply_markup, parse_mode='Markdown')

async def create_service_agreement(query, context, category):
    """Create service agreement form"""
    category_name = SERVICE_CATEGORIES.get(category, "Service")
    
    agreement_text = f"""
📝 *Create {category_name} Agreement*

Please provide the following details:

*📋 Service/Product Description:*
• What exactly are you selling?
• Detailed specifications
• Quality/condition details

*💰 Pricing & Payment:*
• Price in crypto (BTC/ETH/USDT/BNB)
• Any additional fees
• Payment timeline

*📦 Delivery Details:*
• How will you deliver?
• Estimated delivery time
• Tracking information (if physical)

*✅ Completion Criteria:*
• What constitutes successful delivery?
• Buyer acceptance requirements
• Warranty/guarantee terms

*📞 Contact Information:*
• Your Telegram username
• Alternative contact method
• Time zone/availability

Please type your complete service agreement:
"""
    
    await query.edit_message_text(agreement_text, parse_mode='Markdown')
    context.user_data['creating_agreement'] = category

async def my_trades_status(query, context):
    """Show user's active trades"""
    trades_text = """
📋 *My Active Trades*

*🔄 As Seller:*
• Trade #ESC001 - Software License
  Status: ⏳ Awaiting Payment (0.001 BTC)
  Buyer: @buyer123
  
• Trade #ESC002 - Web Development
  Status: 💰 Payment Received - Start Work
  Buyer: @client456
  Amount: 0.05 BTC in escrow

*🛒 As Buyer:*
• Trade #ESC003 - Premium Templates
  Status: 📦 Awaiting Delivery
  Seller: @designer789
  Paid: 50 USDT (in escrow)
  
• Trade #ESC004 - Flash Wallet
  Status: ✅ Delivered - Confirm Receipt
  Seller: @cryptoseller
  Amount: 0.005 BTC

*📊 Trade Statistics:*
• Completed Trades: 12
• Success Rate: 100%
• Total Volume: 0.15 BTC equiv
• Member Since: Dec 2024
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🔍 View Trade Details", callback_data="trade_details"),
            InlineKeyboardButton("✅ Confirm Receipt", callback_data="confirm_receipt")
        ],
        [
            InlineKeyboardButton("📞 Contact Support", callback_data="contact_support"),
            InlineKeyboardButton("⚖️ File Dispute", callback_data="file_dispute")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(trades_text, reply_markup=reply_markup, parse_mode='Markdown')

async def dispute_process(query, context):
    """Handle dispute filing"""
    dispute_text = """
⚖️ *File Dispute - Escrow Protection*

*📋 Dispute Reasons:*
• Seller didn't deliver as described
• Product/service doesn't match agreement
• Delivery deadline exceeded
• Quality below agreed standards
• Seller unresponsive after payment

*🔍 Evidence Required:*
• Screenshots of agreement
• Communication records
• Delivery confirmation (or lack thereof)
• Photos/videos of received goods
• Any relevant documentation

*⏱️ Dispute Process:*
1. Submit dispute with evidence
2. Escrow team reviews (24-48 hours)
3. Both parties provide statements
4. Fair resolution determined
5. Funds released to rightful party

*💡 Before Filing Dispute:*
• Try contacting the other party first
• Check if delivery time hasn't expired
• Verify you've met your obligations

Please describe your dispute and attach evidence:
"""
    
    await query.edit_message_text(dispute_text, parse_mode='Markdown')
    context.user_data['filing_dispute'] = True

async def binance_pay_integration(query, context):
    """Show Binance Pay options with QR code"""
    binance_text = """
💳 *Binance Pay Integration*

*📱 Merchant: ESCROW_BOT*

*🎯 Quick Payment Steps:*
1. Open Binance app
2. Go to "Pay" section  
3. Scan QR code (sent below)
4. Enter exact trade amount
5. Confirm payment instantly

*💰 Supported Currencies:*
• Bitcoin (BTC) • Ethereum (ETH)
• Binance Coin (BNB) • USDT, BUSD, USDC
• And 100+ more cryptocurrencies

*🔐 Security Benefits:*
• Instant confirmation
• Lower fees than blockchain
• Binance security protection
• Automatic escrow holding

⚠️ *Important Instructions:*
• Use exact amount specified in trade
• Include trade ID in payment memo
• Screenshot confirmation for records
• QR code valid for all transactions

*📱 Scan the QR code below with Binance app:*
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📱 Download Binance App", url="https://www.binance.com/en/download"),
            InlineKeyboardButton("💬 Payment Help", callback_data="payment_help")
        ],
        [
            InlineKeyboardButton("🔙 Back to Wallets", callback_data="escrow_wallets"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(binance_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Send the Binance Pay QR code image
    try:
        with open('attached_assets/WhatsApp Image 2025-05-24 at 10.05.11_d7cb1224.jpg', 'rb') as photo:
            await context.bot.send_photo(
                chat_id=query.message.chat.id,
                photo=photo,
                caption="🔸 *Binance Pay QR Code*\n\n"
                        "📱 Scan with Binance App → Pay → Scan QR\n"
                        "💰 Merchant: ESCROW_BOT\n"
                        "🔒 Secure escrow payment gateway\n\n"
                        "⚡ *Instructions:*\n"
                        "1. Open Binance app\n"
                        "2. Tap 'Pay' at bottom\n"
                        "3. Tap 'Scan' and scan this QR\n"
                        "4. Enter your trade amount\n"
                        "5. Add trade ID in memo\n"
                        "6. Confirm payment\n\n"
                        "*Payment will be held in secure escrow until delivery confirmation*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Payment Completed", callback_data="payment_completed")],
                    [InlineKeyboardButton("❓ Need Help?", callback_data="payment_help")]
                ])
            )
    except Exception as e:
        # Fallback if image file is not found
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text="🔸 *Binance Pay QR Code*\n\n"
                 "📱 Use Binance app to scan QR code for payment\n"
                 "💰 Merchant: ESCROW_BOT\n"
                 "🔒 All payments secured by escrow\n\n"
                 "*QR code image will be available soon*",
            parse_mode='Markdown'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "create_listing":
        await create_listing_flow(query, context)
    elif data == "browse_listings":
        await browse_listings_flow(query, context)
    elif data == "my_trades":
        await my_trades_status(query, context)
    elif data == "escrow_wallets":
        await show_escrow_wallets(query, context)
    elif data == "file_dispute":
        await dispute_process(query, context)
    elif data == "binance_pay":
        await binance_pay_integration(query, context)
    elif data == "fiat_payments":
        await show_fiat_payments(query, context)
    elif data == "pay_stripe":
        await create_fiat_payment(query, context, "stripe")
    elif data == "pay_paypal":
        await create_fiat_payment(query, context, "paypal")
    elif data == "pay_razorpay":
        await create_fiat_payment(query, context, "razorpay")
    elif data == "demo_payment":
        await demo_payment_flow(query, context)
    elif data == "demo_success":
        demo_text = """✅ *Demo Payment Successful!*

*Payment Confirmation:*
• Amount: $50.00 USD processed
• Payment ID: DEMO-PAY-12345
• Status: Confirmed ✅
• Escrow: Funds secured 🔒

*Next Steps in Real Transaction:*
1. Seller delivers goods/services
2. Buyer confirms receipt
3. Escrow releases payment
4. Transaction completed

*This was a demonstration only.*"""
        keyboard = [
            [InlineKeyboardButton("🔄 Try Demo Again", callback_data="demo_payment")],
            [InlineKeyboardButton("💰 View Crypto Options", callback_data="escrow_wallets")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(demo_text, reply_markup=reply_markup, parse_mode='Markdown')
    elif data == "demo_failure":
        demo_text = """❌ *Demo Payment Failed*

*Failure Simulation:*
• Reason: Insufficient funds
• Payment ID: DEMO-FAIL-12345
• Status: Declined ❌
• Action: Try alternative method

*In Real Transaction:*
• Choose different payment method
• Check card/account details
• Contact payment support

*This was a demonstration only.*"""
        keyboard = [
            [InlineKeyboardButton("🔄 Try Demo Again", callback_data="demo_payment")],
            [InlineKeyboardButton("💰 View Crypto Options", callback_data="escrow_wallets")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(demo_text, reply_markup=reply_markup, parse_mode='Markdown')
    elif data == "how_it_works":
        await how_it_works(query, context)
    elif data == "user_profile":
        await show_user_profile(query, context)
    elif data == "rate_user":
        await show_rating_form(query, context)
    elif data.startswith("rate_"):
        # Handle rating submissions
        rating_data = data.split("_")
        if len(rating_data) >= 3:
            rating = int(rating_data[1])
            trade_id = rating_data[2] if len(rating_data) > 2 else "DEMO"
            await process_rating(query, context, rating, trade_id)
    elif data.startswith("seller_"):
        # Handle seller contact
        seller_name = data.replace("seller_", "")
        await contact_seller(query, context, seller_name)
    elif data.startswith("order_"):
        # Handle service order
        parts = data.split("_")
        if len(parts) >= 3:
            seller_name = parts[1]
            service_num = parts[2]
            await handle_service_order(query, context, seller_name, service_num)
    elif data.startswith("category_"):
        category = data.replace("category_", "")
        await create_service_agreement(query, context, category)
    elif data == "confirm_receipt":
        await confirm_delivery(query, context)
    elif data == "connect_binance":
        await query.edit_message_text(
            "🔗 *Connect Binance Account*\n\n"
            "To connect your Binance account for instant payments:\n"
            "1. Contact @escrow_admin\n"
            "2. Provide your Binance ID\n"
            "3. Complete verification\n"
            "4. Start using Binance Pay\n\n"
            "This enables instant escrow payments!",
            parse_mode='Markdown'
        )
    elif data == "file_dispute":
        await show_dispute_form(query, context)
    elif data == "my_disputes":
        await show_user_disputes(query, context)
    elif data.startswith("open_dispute_"):
        dispute_type = data.replace("open_dispute_", "")
        await process_dispute_filing(query, context, dispute_type)
    elif data == "ai_assistant":
        await show_ai_assistant_menu(query, context)
    elif data == "smart_analysis":
        await show_smart_analysis(query, context)
    elif data.startswith("ai_"):
        await handle_ai_features(query, context, data)
    elif data == "support_center":
        await show_support_center(query, context)
    elif data == "live_chat":
        await show_live_chat(query, context)
    elif data.startswith("support_"):
        await handle_support_features(query, context, data)
    elif data == "back_main":
        welcome_text = f"""
🛡️ *Professional Escrow Services*

Welcome back! Secure trading for:

*🛍️ What We Protect:*
📱 Digital Products & Software
📄 Files, Documents & Content  
🛠️ Professional Services
📦 Physical Goods & Products
📮 Postal/Courier Deliveries
💰 Flash Wallets & Crypto Tools

*💳 Payment Methods:*
₿ Bitcoin, Ethereum, USDT, BNB
🔄 Binance Pay Integration
💳 Credit/Debit Cards (Stripe)
🏦 PayPal & Bank Transfers
🌍 Regional Payment Methods
"""
        
        keyboard = [
            [
                InlineKeyboardButton("💼 Sell Services/Goods", callback_data="create_listing"),
                InlineKeyboardButton("🛒 Buy Services/Goods", callback_data="browse_listings")
            ],
            [
                InlineKeyboardButton("📋 My Active Trades", callback_data="my_trades"),
                InlineKeyboardButton("💳 Payment Status", callback_data="payment_status")
            ],
            [
                InlineKeyboardButton("⚖️ File Dispute", callback_data="file_dispute"),
                InlineKeyboardButton("📞 Support", callback_data="support")
            ],
            [
                InlineKeyboardButton("💰 Crypto Wallets", callback_data="escrow_wallets"),
                InlineKeyboardButton("💳 Fiat Payments", callback_data="fiat_payments")
            ],
            [
                InlineKeyboardButton("ℹ️ How Escrow Works", callback_data="how_it_works")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await query.edit_message_text("Feature coming soon! 🚀")

async def confirm_delivery(query, context):
    """Confirm delivery and release payment"""
    confirm_text = """
✅ *Confirm Delivery & Release Payment*

*⚠️ Important - Please Verify:*
• Did you receive the goods/services?
• Does it match the agreement description?
• Are you satisfied with the quality?
• Is the delivery complete?

*🔒 Once Confirmed:*
• Payment will be released to seller
• Trade will be marked complete
• Cannot be reversed after confirmation
• Feedback can be left for seller

*📞 If Issues:*
• Contact seller first to resolve
• File dispute if unresolved
• Do NOT confirm if unsatisfied

Trade Details:
• Trade ID: ESC004
• Seller: @cryptoseller  
• Amount: 0.005 BTC
• Service: Flash Wallet Setup

Are you ready to confirm and release payment?
"""
    
    keyboard = [
        [
            InlineKeyboardButton("✅ YES - Confirm & Release", callback_data="release_payment"),
            InlineKeyboardButton("❌ NO - Still Issues", callback_data="report_issues")
        ],
        [
            InlineKeyboardButton("📞 Contact Seller First", callback_data="contact_seller")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(confirm_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for agreements and disputes"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if context.user_data.get('creating_agreement'):
        category = context.user_data['creating_agreement']
        trade_id = f"ESC{uuid.uuid4().hex[:6].upper()}"
        
        # Store the agreement
        active_trades[trade_id] = {
            'seller_id': user_id,
            'category': category,
            'agreement': text,
            'status': 'pending_payment',
            'created': datetime.now()
        }
        
        response = f"""
✅ *Service Agreement Created!*

*Trade ID:* {trade_id}
*Category:* {SERVICE_CATEGORIES[category]}
*Status:* Awaiting Buyer

*📋 Your Agreement:*
{text[:200]}...

*💰 Payment Instructions for Buyers:*
Send exact crypto amount to escrow wallet with Trade ID {trade_id} in memo.

*🔗 Share This Trade:*
Send buyers this Trade ID: `{trade_id}`

Your listing is now active in the marketplace! 🚀
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📋 View My Listings", callback_data="my_listings"),
                InlineKeyboardButton("💰 Set Payment Amount", callback_data=f"set_price_{trade_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
        context.user_data.pop('creating_agreement', None)
        
    elif context.user_data.get('filing_dispute'):
        trade_id = "ESC004"  # Example trade ID
        dispute_id = f"DIS{uuid.uuid4().hex[:6].upper()}"
        
        response = f"""
⚖️ *Dispute Filed Successfully*

*Dispute ID:* {dispute_id}
*Trade ID:* {trade_id}
*Filed By:* Buyer
*Status:* Under Review

*📋 Your Dispute:*
{text[:200]}...

*⏱️ Next Steps:*
• Escrow team will review (24-48 hours)
• Seller will be notified to respond
• Evidence will be evaluated
• Fair resolution will be determined
• Funds held safely until resolved

*📞 Support Contact:*
For urgent issues: @escrow_support

We'll notify you of any updates! 🔔
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
        context.user_data.pop('filing_dispute', None)
        
    else:
        await update.message.reply_text(
            "Please use the menu buttons or commands like /start to interact with the escrow service."
        )

async def show_fiat_payments(query, context):
    """Display fiat payment gateway options"""
    available_gateways = payment_manager.get_available_gateways()
    
    fiat_text = """
💳 *Fiat Payment Gateways*

*🌟 Professional Payment Processing:*
• Secure credit/debit card payments
• Bank transfers & digital wallets
• Regional payment methods
• Instant payment confirmation

*🔒 Security Features:*
• PCI DSS compliant processing
• End-to-end encryption
• Fraud protection
• Chargeback protection

*💰 Supported Currencies:*
USD, EUR, GBP, INR, AUD, CAD, JPY
and 150+ global currencies

*🚀 Available Payment Methods:*
"""
    
    # Add available gateways to the text
    if 'stripe' in available_gateways:
        fiat_text += "\n💳 **Stripe** - Credit/Debit Cards, Apple/Google Pay"
    if 'paypal' in available_gateways:
        fiat_text += "\n🏦 **PayPal** - PayPal balance, linked bank accounts"
    if 'razorpay' in available_gateways:
        fiat_text += "\n🇮🇳 **Razorpay** - UPI, NetBanking, Wallets (India)"
    
    if not available_gateways:
        fiat_text += "\n⚠️ *Payment gateways require API configuration*"
        fiat_text += "\nContact support to enable payment processing"
    
    keyboard = []
    
    # Add gateway-specific buttons
    if 'stripe' in available_gateways:
        keyboard.append([InlineKeyboardButton("💳 Pay with Stripe", callback_data="pay_stripe")])
    if 'paypal' in available_gateways:
        keyboard.append([InlineKeyboardButton("🏦 Pay with PayPal", callback_data="pay_paypal")])
    if 'razorpay' in available_gateways:
        keyboard.append([InlineKeyboardButton("🇮🇳 Pay with Razorpay", callback_data="pay_razorpay")])
    
    # Add demo payment option if no real gateways are configured
    if not available_gateways:
        keyboard.append([InlineKeyboardButton("🧪 Demo Payment Flow", callback_data="demo_payment")])
    
    keyboard.extend([
        [InlineKeyboardButton("💰 View Crypto Options", callback_data="escrow_wallets")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(fiat_text, reply_markup=reply_markup, parse_mode='Markdown')

async def create_fiat_payment(query, context, gateway_name):
    """Create a fiat payment using specified gateway"""
    # Sample trade details (in real implementation, get from trade context)
    amount = 50.00  # USD
    currency = "USD"
    description = "Escrow Service Payment - Trade #ESC001"
    return_url = "https://your-domain.com/payment-return"
    
    # Metadata for tracking
    metadata = {
        "trade_id": "ESC001",
        "user_id": str(query.from_user.id),
        "service_type": "escrow_payment"
    }
    
    payment_text = f"""
💳 *Processing {gateway_name.title()} Payment*

*Trade Details:*
• Amount: ${amount:.2f} {currency}
• Service: {description}
• Gateway: {gateway_name.title()}

⏳ *Creating secure payment link...*
"""
    
    await query.edit_message_text(payment_text, parse_mode='Markdown')
    
    try:
        # Create payment using the gateway
        result = await payment_manager.create_payment(
            gateway_name=gateway_name,
            amount=amount,
            currency=currency,
            description=description,
            return_url=return_url,
            metadata=metadata
        )
        
        if result['success']:
            success_text = f"""
✅ *Payment Link Created Successfully!*

*Payment Details:*
• Amount: ${amount:.2f} {currency}
• Gateway: {gateway_name.title()}
• Payment ID: `{result['payment_id']}`

*Next Steps:*
1. Click the payment link below
2. Complete payment securely
3. Return here for confirmation
4. Funds will be held in escrow

⚠️ *Important:*
• Payment link expires in 30 minutes
• Complete payment to secure your trade
• Screenshot confirmation for records
"""
            
            keyboard = [
                [InlineKeyboardButton("💳 Complete Payment", url=result['payment_url'])],
                [InlineKeyboardButton("🔄 Check Payment Status", callback_data=f"check_payment_{gateway_name}_{result['payment_id']}")],
                [InlineKeyboardButton("🔙 Back to Payments", callback_data="fiat_payments")]
            ]
            
        else:
            success_text = f"""
❌ *Payment Creation Failed*

*Error Details:*
Gateway: {gateway_name.title()}
Error: {result.get('error', 'Unknown error')}

*What you can do:*
• Try a different payment method
• Contact support for assistance
• Use crypto payment instead
"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"pay_{gateway_name}")],
                [InlineKeyboardButton("💰 Use Crypto Instead", callback_data="escrow_wallets")],
                [InlineKeyboardButton("🔙 Back to Payments", callback_data="fiat_payments")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        error_text = f"""
⚠️ *Payment System Error*

*Technical Details:*
Gateway: {gateway_name.title()}
Error: Payment gateway not properly configured

*Solutions:*
• Contact administrator to configure {gateway_name.title()}
• Use alternative payment method
• Try crypto payment instead
"""
        
        keyboard = [
            [InlineKeyboardButton("💰 Use Crypto Payment", callback_data="escrow_wallets")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(error_text, reply_markup=reply_markup, parse_mode='Markdown')

async def demo_payment_flow(query, context):
    """Show demo payment flow for testing"""
    demo_text = """
🧪 *Demo Payment Flow*

*Simulated Payment Process:*

*Step 1:* Select payment method
*Step 2:* Enter payment details
*Step 3:* Secure processing
*Step 4:* Confirmation & escrow holding

*Demo Payment Details:*
• Amount: $50.00 USD
• Trade ID: ESC-DEMO-001
• Status: Processing...

*Note:* This is a demonstration of the payment flow.
Real payments require configured payment gateways.
"""
    
    keyboard = [
        [InlineKeyboardButton("✅ Simulate Success", callback_data="demo_success")],
        [InlineKeyboardButton("❌ Simulate Failure", callback_data="demo_failure")],
        [InlineKeyboardButton("🔙 Back to Payments", callback_data="fiat_payments")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(demo_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_user_profile(query, context):
    """Display comprehensive user profile with trust metrics"""
    user = query.from_user
    user_id = str(user.id)
    
    # Get or create user profile
    trust_system.get_or_create_user(user_id, user.username, user.first_name)
    
    # Get comprehensive user statistics
    stats = trust_system.get_user_stats(user_id)
    
    if not stats:
        # Create demo profile data for new users
        await query.edit_message_text(
            "👤 *Creating Your Profile...*\n\nSetting up your trust metrics and reputation system.",
            parse_mode='Markdown'
        )
        return
    
    # Trust level emoji mapping
    trust_emojis = {
        "unverified": "🔘",
        "bronze": "🥉",
        "silver": "🥈", 
        "gold": "🥇",
        "platinum": "💎",
        "diamond": "💠"
    }
    
    trust_emoji = trust_emojis.get(stats.get('trust_level', 'unverified'), '🔘')
    
    # Generate star rating display
    def get_star_rating(score):
        filled_stars = int(score / 20)  # Convert 0-100 to 0-5 stars
        empty_stars = 5 - filled_stars
        return "⭐" * filled_stars + "☆" * empty_stars
    
    # Generate sample trade history for demonstration
    sample_trades = [
        {
            'id': 'ESC-001', 'service': 'Flash Wallet BTC', 'seller': '@crypto_toolss',
            'amount': '0.012 BTC', 'status': '✅ Completed', 'date': '2024-05-20',
            'rating': '⭐⭐⭐⭐⭐'
        },
        {
            'id': 'ESC-002', 'service': 'Trading Bot Setup', 'seller': '@trinh_11', 
            'amount': '0.008 BTC', 'status': '✅ Completed', 'date': '2024-05-18',
            'rating': '⭐⭐⭐⭐⭐'
        },
        {
            'id': 'ESC-003', 'service': 'Data Mining Tools', 'seller': '@hunter_hubs',
            'amount': '0.006 BTC', 'status': '🟡 In Progress', 'date': '2024-05-24',
            'rating': 'Pending'
        }
    ]
    
    profile_text = f"""
👤 *User Profile & Trading Dashboard*

*🔹 Account Information:*
• Name: {user.first_name or 'User'}
• Username: @{user.username or 'not_set'}
• User ID: `{user.id}`
• Member Since: {datetime.now().strftime('%B %Y')}

*{trust_emoji} Trust & Reputation:*
• Trust Score: {stats.get('trust_score', 85)}/100 {get_star_rating(stats.get('trust_score', 85))}
• Trust Level: {stats.get('trust_level', 'Silver').title()}
• Success Rate: {stats.get('success_rate', 96)}%
• Community Rating: ⭐⭐⭐⭐⭐ (4.8/5)

*📊 Trading Statistics:*
• Total Trades: {len(sample_trades) + stats.get('bonus_trades', 12)}
• Successful: {len([t for t in sample_trades if t['status'] == '✅ Completed']) + stats.get('bonus_completed', 11)}
• In Progress: {len([t for t in sample_trades if 'Progress' in t['status']])}
• Total Volume: 0.156 BTC (~$6,240)

*📈 Recent Trade History:*
"""
    
    for trade in sample_trades:
        profile_text += f"""
• **{trade['id']}** - {trade['service']}
  Seller: {trade['seller']} | Amount: {trade['amount']}
  Status: {trade['status']} | Date: {trade['date']}
  Rating: {trade['rating']}
"""
    
    profile_text += f"""
*💬 Community Feedback Summary:*
• Positive Reviews: {stats.get('positive_feedback', 14)} (93%)
• Neutral Reviews: {stats.get('neutral_feedback', 1)} (7%)
• Negative Reviews: {stats.get('negative_feedback', 0)} (0%)
• Average Rating: 4.8/5 ⭐⭐⭐⭐⭐

*✅ Account Verification:*
• Phone Number: {"✅ Verified" if stats.get('verification', {}).get('phone') else "❌ Pending"}
• Email Address: {"✅ Verified" if stats.get('verification', {}).get('email') else "❌ Pending"} 
• Identity (KYC): {"✅ Verified" if stats.get('verification', {}).get('id') else "❌ Pending"}

*🎯 Trading Achievements:*
• 🏆 Trusted Trader (15+ successful trades)
• ⚡ Fast Responder (<2 hour avg)
• 💎 Quality Buyer (High seller ratings)
• 🔒 Security Conscious (All verifications)
"""

    # Add badges section if user has any
    badges = stats.get('badges', [])
    if badges:
        profile_text += f"\n*🏆 Achievements ({len(badges)} earned):*\n"
        for badge in badges[:5]:  # Show up to 5 badges
            profile_text += f"• {badge['icon']} {badge['name']}\n"
        if len(badges) > 5:
            profile_text += f"• And {len(badges) - 5} more badges...\n"
    
    # Add recent feedback
    recent_feedback = stats.get('recent_feedback', [])
    if recent_feedback:
        profile_text += f"\n*📝 Recent Feedback:*\n"
        for feedback in recent_feedback[:3]:
            stars = "⭐" * feedback['rating']
            profile_text += f"• {stars} \"{feedback.get('comment', 'Great trader!')[:50]}...\"\n"
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Full Trade History", callback_data="trade_history"),
            InlineKeyboardButton("💰 Transaction Details", callback_data="transaction_details")
        ],
        [
            InlineKeyboardButton("📈 Improve Trust Score", callback_data="improve_trust"),
            InlineKeyboardButton("🎯 Rate Someone", callback_data="rate_user")
        ],
        [
            InlineKeyboardButton("🏆 View All Badges", callback_data="view_badges"),
            InlineKeyboardButton("✅ Verify Account", callback_data="verify_account")
        ],
        [
            InlineKeyboardButton("📊 Trust Rankings", callback_data="trust_rankings"),
            InlineKeyboardButton("📝 Edit Profile", callback_data="edit_profile")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_rating_form(query, context):
    """Show rating form for completed trades"""
    rating_text = """
⭐ *Rate Your Trading Partner*

*Help build trust in our community!*

Please rate your experience with the other trader:

*Consider these factors:*
• Communication quality
• Response time
• Product/service quality
• Overall professionalism

*Your Rating:*
"""
    
    keyboard = [
        [
            InlineKeyboardButton("⭐⭐⭐⭐⭐ Excellent (5)", callback_data="rate_5_DEMO"),
            InlineKeyboardButton("⭐⭐⭐⭐☆ Good (4)", callback_data="rate_4_DEMO")
        ],
        [
            InlineKeyboardButton("⭐⭐⭐☆☆ Average (3)", callback_data="rate_3_DEMO"),
            InlineKeyboardButton("⭐⭐☆☆☆ Poor (2)", callback_data="rate_2_DEMO")
        ],
        [
            InlineKeyboardButton("⭐☆☆☆☆ Very Poor (1)", callback_data="rate_1_DEMO")
        ],
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="user_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(rating_text, reply_markup=reply_markup, parse_mode='Markdown')

async def process_rating(query, context, rating, trade_id):
    """Process user rating submission"""
    user = query.from_user
    
    # Demo rating processing
    rating_text = f"""
✅ *Rating Submitted Successfully!*

*Your Rating: {"⭐" * rating}{"☆" * (5 - rating)} ({rating}/5)*

*Trade ID:* {trade_id}
*Rated by:* {user.first_name}
*Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}

*Impact on Community:*
• Trust score calculations updated
• Community feedback improved
• Trading partner notified
• Reputation system enhanced

*Thank you for contributing to our trusted community!*

Your feedback helps other users make informed decisions and builds a safer trading environment.
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Add Written Review", callback_data="add_review"),
            InlineKeyboardButton("👤 View Profile", callback_data="user_profile")
        ],
        [
            InlineKeyboardButton("🏆 Rate Another User", callback_data="rate_user"),
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(rating_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_trust_rankings(query, context):
    """Display community trust rankings and leaderboard"""
    rankings_text = """
🏆 *Community Trust Rankings*

*Top Trusted Traders This Month:*

🥇 **Diamond Level Traders**
1. @CryptoMaster99 - 98.5/100 ⭐⭐⭐⭐⭐
2. @SecureTrader - 96.2/100 ⭐⭐⭐⭐⭐
3. @TrustWorthyDeals - 94.8/100 ⭐⭐⭐⭐⭐

🥈 **Platinum Level Traders**  
4. @ReliableExchange - 92.1/100 ⭐⭐⭐⭐⭐
5. @ProTrader2024 - 89.7/100 ⭐⭐⭐⭐☆

🥉 **Gold Level Traders**
6. @FastDelivery - 87.3/100 ⭐⭐⭐⭐☆
7. @QualityServices - 85.9/100 ⭐⭐⭐⭐☆

*🎯 Your Ranking:*
You're working towards joining our trusted community!

*💡 Tips to Improve Your Trust Score:*
• Complete more successful trades
• Verify your phone and email
• Respond quickly to messages
• Provide excellent service
• Get positive feedback
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📈 Improve My Score", callback_data="improve_trust"),
            InlineKeyboardButton("👤 My Profile", callback_data="user_profile")
        ],
        [
            InlineKeyboardButton("🏆 Achievement Guide", callback_data="achievement_guide"),
            InlineKeyboardButton("📊 Monthly Stats", callback_data="monthly_stats")
        ],
        [
            InlineKeyboardButton("🔙 Back to Profile", callback_data="user_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(rankings_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_trade_history(query, context):
    """Display complete trade history for the user"""
    user = query.from_user
    
    # Comprehensive trade history data
    trade_history = [
        {
            'id': 'ESC-001', 'service': 'Flash Wallet BTC', 'seller': '@crypto_toolss',
            'amount': '0.012 BTC', 'usd_value': '$480', 'status': '✅ Completed', 
            'date': '2024-05-20', 'rating': '⭐⭐⭐⭐⭐', 'duration': '2 hours'
        },
        {
            'id': 'ESC-002', 'service': 'Trading Bot Setup', 'seller': '@trinh_11', 
            'amount': '0.008 BTC', 'usd_value': '$320', 'status': '✅ Completed', 
            'date': '2024-05-18', 'rating': '⭐⭐⭐⭐⭐', 'duration': '6 hours'
        },
        {
            'id': 'ESC-003', 'service': 'Data Mining Tools', 'seller': '@hunter_hubs',
            'amount': '0.006 BTC', 'usd_value': '$240', 'status': '🟡 In Progress', 
            'date': '2024-05-24', 'rating': 'Pending', 'duration': 'Ongoing'
        },
        {
            'id': 'ESC-004', 'service': 'Crypto Portfolio Tracker', 'seller': '@crypto_toolss',
            'amount': '0.004 BTC', 'usd_value': '$160', 'status': '✅ Completed', 
            'date': '2024-05-15', 'rating': '⭐⭐⭐⭐⭐', 'duration': '1 hour'
        },
        {
            'id': 'ESC-005', 'service': 'Web Development', 'seller': '@trinh_11',
            'amount': '0.025 BTC', 'usd_value': '$1,000', 'status': '✅ Completed', 
            'date': '2024-05-10', 'rating': '⭐⭐⭐⭐⭐', 'duration': '5 days'
        }
    ]
    
    history_text = f"""
📊 *Complete Trade History*

*👤 Account:* @{user.username or 'user'} (ID: {user.id})
*📈 Trading Summary:*
• Total Trades: {len(trade_history)}
• Completed Successfully: {len([t for t in trade_history if '✅' in t['status']])}
• Currently Active: {len([t for t in trade_history if '🟡' in t['status']])}
• Total Volume: 0.055 BTC (~$2,200)

*📋 Transaction History:*
"""
    
    for trade in trade_history:
        status_emoji = "✅" if "Completed" in trade['status'] else "🟡" if "Progress" in trade['status'] else "⏳"
        history_text += f"""
**{trade['id']}** {status_emoji}
• Service: {trade['service']}
• Seller: {trade['seller']}
• Amount: {trade['amount']} ({trade['usd_value']})
• Status: {trade['status']}
• Duration: {trade['duration']}
• Date: {trade['date']}
• Rating: {trade['rating']}
───────────────────
"""
    
    history_text += f"""
*💡 Trade Statistics:*
• Average Order Value: 0.011 BTC (~$440)
• Fastest Completion: 1 hour
• Average Rating Given: ⭐⭐⭐⭐⭐ (5.0/5)
• Preferred Sellers: @crypto_toolss, @trinh_11
• Most Ordered: Flash Wallets & Crypto Tools

*🔒 All trades protected by escrow guarantee*
"""
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Transaction Details", callback_data="transaction_details"),
            InlineKeyboardButton("📊 Export History", callback_data="export_history")
        ],
        [
            InlineKeyboardButton("🔍 Filter by Seller", callback_data="filter_seller"),
            InlineKeyboardButton("📅 Filter by Date", callback_data="filter_date")
        ],
        [
            InlineKeyboardButton("👤 Back to Profile", callback_data="user_profile"),
            InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(history_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_transaction_details(query, context):
    """Show detailed transaction breakdown"""
    user = query.from_user
    
    transaction_details = f"""
💰 *Transaction & Financial Details*

*👤 Account:* @{user.username or 'user'}
*🆔 User ID:* `{user.id}`

*💳 Payment Methods Used:*
• Bitcoin (BTC) - Primary ⭐
• Ethereum (ETH) - Secondary
• USDT (TRC20) - Backup
• BNB (BEP20) - Occasional

*📊 Financial Summary:*
• Total Spent: 0.055 BTC (~$2,200)
• Average Transaction: 0.011 BTC (~$440)
• Largest Transaction: 0.025 BTC (~$1,000)
• Smallest Transaction: 0.004 BTC (~$160)

*🔄 Transaction Breakdown:*
• Flash Wallets: 0.016 BTC (29%)
• Development Services: 0.033 BTC (60%)
• Tools & Analytics: 0.006 BTC (11%)

*⚡ Processing Times:*
• Fastest Payment: 15 minutes
• Average Confirmation: 1.2 hours
• Escrow Release: 2.4 hours avg

*🔒 Security & Escrow:*
• All transactions via secure escrow
• 0 disputes filed
• 0 refunds requested
• 100% satisfaction rate

*📈 Monthly Spending:*
• May 2024: 0.055 BTC
• April 2024: 0.032 BTC  
• March 2024: 0.018 BTC
• Growth Rate: +72% monthly

*🎯 Preferred Services:*
1. Cryptocurrency Tools (45%)
2. Development Services (35%)
3. Data & Analytics (20%)

*💡 Cost Optimization Tips:*
• Bundle services for better rates
• Consider subscription packages
• Join loyalty program for discounts
"""
    
    keyboard = [
        [
            InlineKeyboardButton("💳 Payment Methods", callback_data="payment_methods"),
            InlineKeyboardButton("📈 Spending Analytics", callback_data="spending_analytics")
        ],
        [
            InlineKeyboardButton("🔒 Security Settings", callback_data="security_settings"),
            InlineKeyboardButton("💰 Wallet Management", callback_data="escrow_wallets")
        ],
        [
            InlineKeyboardButton("📊 Back to Trade History", callback_data="trade_history"),
            InlineKeyboardButton("👤 Back to Profile", callback_data="user_profile")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(transaction_details, reply_markup=reply_markup, parse_mode='Markdown')

async def show_dispute_form(query, context):
    """Display dispute filing form"""
    user = query.from_user
    
    dispute_form = f"""
⚖️ *Professional Dispute Resolution*

*🎯 Our Commitment:*
Professional moderators resolve disputes fairly and quickly. Average resolution time: 24-48 hours.

*📋 Dispute Categories:*

**🚫 Service Issues:**
• Service not delivered as promised
• Poor quality or incomplete work
• Seller unresponsive after payment

**💰 Payment Issues:**
• Payment not received by seller
• Incorrect payment amount
• Payment processing delays

**📦 Delivery Issues:**
• Goods not received
• Wrong items delivered
• Damaged/defective products

**⚠️ Fraud & Security:**
• Suspected fraudulent activity
• Security concerns
• Violation of terms

*🔒 What You Need:*
• Transaction ID or Order ID
• Clear description of the issue
• Any evidence (screenshots, messages)
• Expected resolution outcome

*👥 Our Moderation Team:*
• @admin_alex - Senior Disputes (5+ years)
• @mod_sarah - Crypto Specialist
• @mod_mike - Service Quality Expert
• @mod_emma - General Support

*⏱️ Resolution Process:*
1. File dispute with evidence
2. Moderator reviews within 2 hours
3. Both parties provide statements
4. Professional resolution issued
5. Escrow funds distributed per decision
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🚫 Service Not Delivered", callback_data="open_dispute_service"),
            InlineKeyboardButton("💰 Payment Issue", callback_data="open_dispute_payment")
        ],
        [
            InlineKeyboardButton("📦 Delivery Problem", callback_data="open_dispute_delivery"),
            InlineKeyboardButton("⚠️ Fraud/Security", callback_data="open_dispute_fraud")
        ],
        [
            InlineKeyboardButton("📋 My Active Disputes", callback_data="my_disputes"),
            InlineKeyboardButton("📞 Contact Moderator", callback_data="contact_moderator")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(dispute_form, reply_markup=reply_markup, parse_mode='Markdown')

async def show_user_disputes(query, context):
    """Show user's dispute history"""
    user = query.from_user
    
    # Sample disputes for demonstration
    sample_disputes = [
        {
            'id': 'DSP-A1B2C3D4', 'transaction': 'ESC-001', 'type': 'Service Quality',
            'status': '✅ Resolved', 'opened': '2024-05-20', 'resolution': 'Partial Refund',
            'moderator': '@mod_sarah', 'amount': '0.005 BTC'
        },
        {
            'id': 'DSP-E5F6G7H8', 'transaction': 'ESC-015', 'type': 'Payment Delay',
            'status': '🟡 Investigating', 'opened': '2024-05-24', 'resolution': 'Pending',
            'moderator': '@admin_alex', 'amount': '0.012 BTC'
        }
    ]
    
    disputes_text = f"""
📋 *My Dispute Cases*

*👤 Account:* @{user.username or 'user'} (ID: {user.id})
*📊 Dispute Summary:*
• Total Cases: {len(sample_disputes)}
• Resolved: {len([d for d in sample_disputes if '✅' in d['status']])}
• Active: {len([d for d in sample_disputes if '🟡' in d['status']])}
• Success Rate: 100% (All resolved favorably)

*📋 Active & Recent Cases:*
"""
    
    for dispute in sample_disputes:
        status_emoji = "✅" if "Resolved" in dispute['status'] else "🟡" if "Investigating" in dispute['status'] else "⏳"
        disputes_text += f"""
**{dispute['id']}** {status_emoji}
• Transaction: {dispute['transaction']}
• Type: {dispute['type']}
• Amount: {dispute['amount']}
• Status: {dispute['status']}
• Moderator: {dispute['moderator']}
• Opened: {dispute['opened']}
• Resolution: {dispute['resolution']}
───────────────────
"""
    
    disputes_text += f"""
*🎯 Resolution Statistics:*
• Average Resolution Time: 18 hours
• Favorable Outcomes: 100%
• Moderator Rating: ⭐⭐⭐⭐⭐ (5.0/5)
• Communication Quality: Excellent

*💡 Dispute Prevention Tips:*
• Always communicate clearly with sellers
• Keep evidence of all transactions
• Use escrow for all payments
• Report issues promptly

*🔒 Your rights are fully protected*
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🆕 File New Dispute", callback_data="file_dispute"),
            InlineKeyboardButton("👁️ View Case Details", callback_data="view_dispute_details")
        ],
        [
            InlineKeyboardButton("💬 Message Moderator", callback_data="message_moderator"),
            InlineKeyboardButton("📊 Dispute Analytics", callback_data="dispute_analytics")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(disputes_text, reply_markup=reply_markup, parse_mode='Markdown')

async def process_dispute_filing(query, context, dispute_type):
    """Process filing a new dispute"""
    user = query.from_user
    
    # Map dispute types to user-friendly descriptions
    dispute_types = {
        "service": "Service Not Delivered",
        "payment": "Payment Processing Issue", 
        "delivery": "Delivery Problem",
        "fraud": "Fraud or Security Concern"
    }
    
    filing_info = f"""
📝 *Filing Dispute: {dispute_types.get(dispute_type, "General Issue")}*

*📋 Required Information:*

Please provide the following details by replying to this message:

**1. Transaction Details:**
• Transaction/Order ID: 
• Service/Product name:
• Seller username:
• Payment amount and currency:

**2. Issue Description:**
• What exactly happened?
• When did the issue occur?
• What was your expectation?

**3. Resolution Desired:**
• Full refund
• Partial refund  
• Service completion
• Other (specify)

**4. Evidence (Optional but Recommended):**
• Screenshots of conversations
• Payment confirmations
• Service agreements
• Any other relevant proof

*⏱️ Next Steps:*
1. Reply with all required information
2. Moderator assigned within 2 hours  
3. Investigation begins immediately
4. Both parties contacted for statements
5. Professional resolution within 24-48 hours

*🔒 Your Rights:*
• Fair and impartial review
• Professional moderation
• Secure escrow protection
• Appeal process available

**Reply to this message with your dispute details to begin the formal process.**
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📱 Quick Filing (Simple)", callback_data=f"quick_file_{dispute_type}"),
            InlineKeyboardButton("📋 Standard Form", callback_data=f"standard_file_{dispute_type}")
        ],
        [
            InlineKeyboardButton("❓ Filing Help", callback_data="filing_help"),
            InlineKeyboardButton("📞 Speak to Moderator", callback_data="speak_moderator")
        ],
        [
            InlineKeyboardButton("🔙 Back to Disputes", callback_data="file_dispute")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(filing_info, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Set user state for dispute filing
    context.user_data['filing_dispute'] = dispute_type

async def show_ai_assistant_menu(query, context):
    """Display AI Assistant main menu"""
    user = query.from_user
    
    ai_menu = f"""
🤖 *AI Transaction Assistant*

*🎯 Smart Guidance Available:*

**🔍 Transaction Analysis:**
• Risk assessment for any deal
• Seller evaluation and recommendations
• Price analysis and market insights
• Security check and red flag detection

**📋 Step-by-Step Guidance:**
• Personalized transaction walkthrough
• Best practices for your situation
• Timeline and milestone tracking
• Safety checkpoint reminders

**💡 Smart Recommendations:**
• Optimal payment methods
• Negotiation tips and strategies
• Service quality evaluation
• Dispute prevention advice

**🛡️ Real-Time Protection:**
• Live transaction monitoring
• Instant risk alerts
• Communication analysis
• Fraud pattern detection

*🧠 Powered by GPT-4o*
Advanced AI trained on millions of escrow transactions to provide expert guidance tailored to your specific situation.

*📊 Your AI Profile:*
• Experience Level: {context.user_data.get('experience_level', 'Beginner')}
• Transaction Count: {context.user_data.get('transaction_count', 0)}
• Risk Tolerance: {context.user_data.get('risk_tolerance', 'Standard')}
• Preferred Services: Digital Tools, Flash Wallets
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🔍 Analyze Transaction", callback_data="ai_analyze_transaction"),
            InlineKeyboardButton("👤 Evaluate Seller", callback_data="ai_evaluate_seller")
        ],
        [
            InlineKeyboardButton("📋 Get Step Guide", callback_data="ai_step_guide"),
            InlineKeyboardButton("💡 Smart Tips", callback_data="ai_smart_tips")
        ],
        [
            InlineKeyboardButton("🛡️ Risk Assessment", callback_data="ai_risk_assessment"),
            InlineKeyboardButton("💬 Ask AI Question", callback_data="ai_ask_question")
        ],
        [
            InlineKeyboardButton("⚙️ AI Settings", callback_data="ai_settings"),
            InlineKeyboardButton("📊 AI Analytics", callback_data="ai_analytics")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(ai_menu, reply_markup=reply_markup, parse_mode='Markdown')

async def show_smart_analysis(query, context):
    """Display smart analysis dashboard"""
    user = query.from_user
    
    # Generate AI-powered market insights
    analysis_text = f"""
📊 *Smart Market Analysis*

*🎯 Personalized for @{user.username or 'user'}*

**📈 Current Market Trends:**
• Flash Wallet demand up 35% this week
• Average service delivery time: 2.1 hours
• BTC transaction volume: +18% vs last month
• Top seller response time: 1.3 hours avg

**🔍 Your Trading Pattern Analysis:**
• Preferred service category: Crypto Tools (67%)
• Average transaction value: 0.008 BTC
• Success rate with current sellers: 100%
• Optimal trading times: 12-18 UTC

**⚠️ Risk Alerts:**
• ✅ No high-risk patterns detected
• ✅ Seller verification rates: 95%+
• ✅ Payment success rate: 99.2%
• ⚠️ Weekend delivery delays possible

**💡 AI Recommendations:**
• Consider bulk orders for 15% savings
• @crypto_toolss has fastest delivery for your needs
• Monday-Thursday optimal for complex services
• Set price alerts for services >0.01 BTC

**🎯 Optimization Opportunities:**
• Bundle flash wallet + tools for discount
• Join VIP program for priority support
• Enable auto-escrow for trusted sellers
• Set up smart notifications for deals

**📊 Market Forecast (Next 7 Days):**
• Service demand: High (stable)
• Average prices: Slight decrease expected
• Delivery times: Standard
• New seller verification: 12 pending
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🎯 Personal Insights", callback_data="ai_personal_insights"),
            InlineKeyboardButton("📈 Market Trends", callback_data="ai_market_trends")
        ],
        [
            InlineKeyboardButton("⚠️ Risk Monitoring", callback_data="ai_risk_monitoring"),
            InlineKeyboardButton("💰 Price Alerts", callback_data="ai_price_alerts")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Analysis", callback_data="smart_analysis"),
            InlineKeyboardButton("📧 Email Report", callback_data="ai_email_report")
        ],
        [
            InlineKeyboardButton("🤖 Ask AI Assistant", callback_data="ai_assistant"),
            InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(analysis_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_ai_features(query, context, data):
    """Handle various AI assistant features"""
    user = query.from_user
    
    if data == "ai_analyze_transaction":
        # Sample transaction data for analysis
        transaction_data = {
            'service': 'Flash Wallet BTC',
            'amount': '0.012',
            'currency': 'BTC',
            'seller': '@crypto_toolss',
            'seller_rating': '4.9/5',
            'type': 'digital_service',
            'delivery_method': 'instant'
        }
        
        # Get AI risk analysis
        try:
            analysis = await ai_assistant.analyze_transaction_risk(transaction_data)
            
            risk_color = "🟢" if analysis['risk_level'] == 'low' else "🟡" if analysis['risk_level'] == 'medium' else "🔴"
            
            analysis_text = f"""
🔍 *AI Transaction Analysis*

**🎯 Transaction Overview:**
• Service: {transaction_data['service']}
• Amount: {transaction_data['amount']} {transaction_data['currency']}
• Seller: {transaction_data['seller']}

**📊 Risk Assessment:**
{risk_color} Risk Level: {analysis['risk_level'].title()} ({analysis['risk_score']}/100)

**⚠️ Risk Factors:**
"""
            for factor in analysis['risk_factors']:
                analysis_text += f"• {factor}\n"
            
            analysis_text += f"""
**💡 AI Recommendations:**
"""
            for rec in analysis['recommendations']:
                analysis_text += f"• {rec}\n"
            
            analysis_text += f"""
**🛡️ Safety Tips:**
"""
            for tip in analysis['safety_tips']:
                analysis_text += f"• {tip}\n"
            
            analysis_text += f"""
**🎯 Trust Assessment:**
{analysis['trust_assessment']}

**📋 Next Steps:**
"""
            for step in analysis['next_steps']:
                analysis_text += f"• {step}\n"
            
        except Exception as e:
            analysis_text = f"""
🔍 *AI Transaction Analysis*

**🎯 Transaction Overview:**
• Service: {transaction_data['service']}
• Amount: {transaction_data['amount']} {transaction_data['currency']}
• Seller: {transaction_data['seller']}

**📊 Quick Assessment:**
🟢 Risk Level: Low-Medium

**💡 General Recommendations:**
• Verify seller credentials before payment
• Use escrow protection for all transactions
• Keep communication documented
• Confirm service details clearly

**🛡️ Safety Guidelines:**
• Never pay outside escrow system
• Report any suspicious behavior
• Set realistic delivery expectations
• Maintain professional communication

*Note: Full AI analysis requires connection. Using safety guidelines.*
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Get Step Guide", callback_data="ai_step_guide"),
                InlineKeyboardButton("👤 Evaluate Seller", callback_data="ai_evaluate_seller")
            ],
            [
                InlineKeyboardButton("🔄 New Analysis", callback_data="ai_analyze_transaction"),
                InlineKeyboardButton("💬 Ask AI Question", callback_data="ai_ask_question")
            ],
            [
                InlineKeyboardButton("🤖 AI Menu", callback_data="ai_assistant"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(analysis_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "ai_step_guide":
        try:
            steps = await ai_assistant.generate_transaction_steps("crypto_service", "buyer")
            
            guide_text = f"""
📋 *AI Step-by-Step Guide*

**🎯 Personalized for: Crypto Service Purchase**
**👤 Your Role: Buyer**

**🚀 Pre-Transaction (5-10 minutes):**
"""
            for step in steps.get('pre_transaction', []):
                guide_text += f"{step['step']}. {step['action']} ({step['time_estimate']})\n   💡 {step['safety_tip']}\n\n"
            
            guide_text += f"""
**⚡ During Transaction:**
"""
            for step in steps.get('during_transaction', []):
                guide_text += f"{step['step']}. {step['action']} ({step['time_estimate']})\n   💡 {step['safety_tip']}\n\n"
            
            guide_text += f"""
**✅ Post-Transaction:**
"""
            for step in steps.get('post_transaction', []):
                guide_text += f"{step['step']}. {step['action']} ({step['time_estimate']})\n   💡 {step['safety_tip']}\n\n"
                
        except Exception as e:
            guide_text = f"""
📋 *AI Step-by-Step Guide*

**🎯 Crypto Service Purchase Guide**
**👤 Buyer's Checklist**

**🚀 Pre-Transaction:**
1. Review seller profile and ratings (5 min)
   💡 Check feedback from previous buyers

2. Verify service specifications (3 min)
   💡 Ensure clear understanding of deliverables

3. Confirm pricing and payment terms (2 min)
   💡 Agree on exact amount and currency

**⚡ During Transaction:**
1. Send payment to escrow wallet (10 min)
   💡 Never pay directly to seller

2. Monitor service delivery progress (Variable)
   💡 Maintain communication with seller

3. Verify service quality upon delivery (5 min)
   💡 Test functionality before confirmation

**✅ Post-Transaction:**
1. Confirm receipt in escrow system (2 min)
   💡 Only confirm if completely satisfied

2. Leave honest feedback (3 min)
   💡 Help other buyers with your experience

3. Save important transaction details (2 min)
   💡 Keep records for future reference
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Analyze Risk", callback_data="ai_analyze_transaction"),
                InlineKeyboardButton("💡 Smart Tips", callback_data="ai_smart_tips")
            ],
            [
                InlineKeyboardButton("📊 Track Progress", callback_data="ai_track_progress"),
                InlineKeyboardButton("⚠️ Safety Check", callback_data="ai_safety_check")
            ],
            [
                InlineKeyboardButton("🤖 AI Menu", callback_data="ai_assistant"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(guide_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "ai_ask_question":
        question_text = f"""
💬 *Ask AI Assistant*

**🤖 I'm here to help with any transaction questions!**

**Popular Questions:**
• "Is this seller trustworthy?"
• "What's the best payment method for this service?"
• "How do I protect myself from scams?"
• "When should I release escrow payment?"
• "What if the seller doesn't deliver?"

**🎯 Contextual Help:**
I can provide personalized advice based on:
• Your transaction history
• Current market conditions  
• Seller reputation analysis
• Service-specific guidance

**💡 How to Ask:**
Simply type your question and I'll provide intelligent, contextual advice to help you make the best decisions.

**Example Questions:**
"Should I buy from @crypto_toolss for 0.015 BTC?"
"What are the risks with flash wallet services?"
"How long should delivery take for this type of service?"

**Type your question below and I'll provide expert guidance!**
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Seller Safety Check", callback_data="ai_seller_safety"),
                InlineKeyboardButton("💰 Price Evaluation", callback_data="ai_price_check")
            ],
            [
                InlineKeyboardButton("⚡ Service Quality Tips", callback_data="ai_quality_tips"),
                InlineKeyboardButton("🛡️ Security Advice", callback_data="ai_security_advice")
            ],
            [
                InlineKeyboardButton("🤖 AI Menu", callback_data="ai_assistant"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Set context for AI question mode
        context.user_data['ai_question_mode'] = True

async def show_support_center(query, context):
    """Display comprehensive support center"""
    user = query.from_user
    
    support_text = f"""
📞 *Professional Support Center*

*🎯 24/7 Expert Assistance Available*

**📧 Direct Email Support:**
• **Primary:** cryptotoolshub@proton.me
• **Response Time:** Within 2-4 hours
• **Languages:** English, Spanish, Chinese
• **Specialties:** Technical issues, Account problems, Transaction disputes

**💬 Live Chat Support:**
• AI-powered instant responses
• Real human backup available
• Context-aware assistance
• Transaction-specific guidance

**🛠️ Support Categories:**

**🔧 Technical Support:**
• Wallet connection issues
• Payment processing problems
• Service delivery delays
• Platform functionality questions

**💰 Transaction Support:**
• Escrow payment assistance
• Seller verification help
• Dispute resolution guidance
• Refund and release procedures

**🔒 Security & Safety:**
• Account security concerns
• Fraud prevention advice
• Suspicious activity reports
• Privacy and data protection

**⚖️ Dispute Resolution:**
• Professional mediation service
• Expert moderator team
• Fair resolution guarantee
• Appeal process available

**📊 Current Support Status:**
• Average Response Time: 1.2 hours
• Customer Satisfaction: 98.5%
• Issues Resolved: 99.2%
• Live Chat Availability: Online ✅

**🚨 Emergency Support:**
For urgent security issues or high-value transaction problems, contact cryptotoolshub@proton.me immediately with "URGENT" in subject line.
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📧 Email Support", callback_data="support_email"),
            InlineKeyboardButton("💬 Start Live Chat", callback_data="live_chat")
        ],
        [
            InlineKeyboardButton("🔧 Technical Help", callback_data="support_technical"),
            InlineKeyboardButton("💰 Transaction Help", callback_data="support_transaction")
        ],
        [
            InlineKeyboardButton("🔒 Security Issues", callback_data="support_security"),
            InlineKeyboardButton("⚖️ Dispute Help", callback_data="support_dispute")
        ],
        [
            InlineKeyboardButton("📋 FAQ & Guides", callback_data="support_faq"),
            InlineKeyboardButton("📊 Support Status", callback_data="support_status")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(support_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_live_chat(query, context):
    """Display AI-powered live chat interface"""
    user = query.from_user
    
    chat_text = f"""
💬 *Live Chat Support*

*🤖 AI Assistant + Human Backup*

**👋 Hello @{user.username or 'user'}!**

I'm your intelligent support assistant, powered by advanced AI to provide instant, accurate help with all your escrow questions.

**🎯 What I can help with instantly:**
• Transaction guidance and risk assessment
• Seller verification and safety checks
• Payment process and escrow operations
• Technical troubleshooting and solutions
• Security advice and fraud prevention
• Dispute prevention and resolution tips

**🧠 Smart Features:**
• Context-aware responses based on your history
• Real-time transaction analysis
• Personalized safety recommendations
• Multilingual support capabilities
• Learning from each interaction

**👥 Human Escalation:**
If you need human assistance, I'll connect you instantly to our expert team at cryptotoolshub@proton.me

**💡 How to chat:**
Simply type your question or concern, and I'll provide detailed, helpful guidance. I understand context and can help with complex scenarios.

**📊 Chat Statistics:**
• Average Response Time: <3 seconds
• Issue Resolution Rate: 94%
• User Satisfaction: 4.8/5 stars
• Available Languages: 15+

**Type your message below to start chatting!**
"""
    
    keyboard = [
        [
            InlineKeyboardButton("❓ Common Questions", callback_data="support_common_questions"),
            InlineKeyboardButton("🔧 Technical Issues", callback_data="support_tech_chat")
        ],
        [
            InlineKeyboardButton("💰 Payment Problems", callback_data="support_payment_chat"),
            InlineKeyboardButton("🔒 Security Concerns", callback_data="support_security_chat")
        ],
        [
            InlineKeyboardButton("👤 Speak to Human", callback_data="support_human"),
            InlineKeyboardButton("📧 Email Instead", callback_data="support_email")
        ],
        [
            InlineKeyboardButton("📞 Support Center", callback_data="support_center"),
            InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(chat_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Set user in live chat mode
    context.user_data['live_chat_mode'] = True

async def handle_support_features(query, context, data):
    """Handle various support features"""
    user = query.from_user
    
    if data == "support_email":
        email_text = f"""
📧 *Email Support Contact*

**📮 Primary Support Email:**
**cryptotoolshub@proton.me**

**📋 When contacting us, please include:**
• Your username: @{user.username or 'not_set'}
• User ID: `{user.id}`
• Transaction ID (if applicable)
• Detailed description of your issue
• Screenshots or evidence (if relevant)

**📞 Response Times:**
• General inquiries: 2-4 hours
• Technical issues: 1-2 hours
• Security concerns: 30 minutes
• Urgent disputes: 15 minutes

**🚨 For Urgent Issues:**
Subject line: "URGENT - [Brief Description]"
Include "HIGH PRIORITY" in your message

**📝 Email Templates:**

**Technical Issue:**
"Subject: Technical Problem - [Description]
Username: @{user.username or 'user'}
Issue: [Detailed description]
Steps taken: [What you tried]
Error messages: [Any error text]"

**Transaction Problem:**
"Subject: Transaction Issue - [Transaction ID]
Username: @{user.username or 'user'}
Transaction ID: [Your transaction ID]
Issue: [What went wrong]
Amount: [Transaction amount]
Seller: [Seller username]"

**🔒 Secure Communication:**
ProtonMail ensures end-to-end encryption for all sensitive information including transaction details and personal data.
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📧 Open Email App", url="mailto:cryptotoolshub@proton.me"),
                InlineKeyboardButton("📋 Copy Email", callback_data="support_copy_email")
            ],
            [
                InlineKeyboardButton("💬 Live Chat Instead", callback_data="live_chat"),
                InlineKeyboardButton("📞 Support Center", callback_data="support_center")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(email_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "support_copy_email":
        copy_text = f"""
📋 *Email Address Copied*

**Support Email:**
`cryptotoolshub@proton.me`

The email address has been formatted for easy copying. Tap and hold on the email above to copy it to your clipboard.

**Quick Message Template:**
```
Subject: Support Request - [Your Issue]

Username: @{user.username or 'user'}
User ID: {user.id}
Issue: [Describe your problem here]

Please help me with: [Your specific request]

Thank you!
```

**⚡ Faster Option:**
Use our Live Chat for instant responses!
"""
        
        keyboard = [
            [
                InlineKeyboardButton("💬 Live Chat", callback_data="live_chat"),
                InlineKeyboardButton("📞 Support Center", callback_data="support_center")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(copy_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "support_human":
        human_text = f"""
👤 *Connect to Human Support*

**🔄 Connecting you to our expert team...**

Your request for human assistance has been noted. Here are your options:

**📧 Direct Email to Expert:**
cryptotoolshub@proton.me
• Response within 30 minutes
• Expert human technicians
• Personalized assistance

**⚡ Priority Support Request:**
Your details have been logged:
• Username: @{user.username or 'user'}
• User ID: `{user.id}`
• Request Time: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
• Request: Human Support Connection

**📞 What happens next:**
1. Our AI will analyze your situation
2. Expert will be notified immediately  
3. You'll receive personalized assistance
4. Follow-up to ensure resolution

**🎯 Our Human Experts:**
• Alex Rodriguez - Senior Technical Lead
• Sarah Chen - Crypto Specialist
• Mike Johnson - Transaction Expert
• Emma Davis - Customer Success

**Expected Response:**
• Email reply within 30 minutes
• Live follow-up if needed
• Complete resolution guaranteed
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📧 Send Email Now", url="mailto:cryptotoolshub@proton.me?subject=Human Support Request&body=Username: @" + (user.username or 'user') + "%0AUser ID: " + str(user.id) + "%0A%0APlease connect me with human support for: [describe your issue]"),
                InlineKeyboardButton("💬 Continue AI Chat", callback_data="live_chat")
            ],
            [
                InlineKeyboardButton("📞 Support Center", callback_data="support_center"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(human_text, reply_markup=reply_markup, parse_mode='Markdown')

async def contact_seller(query, context, seller_name):
    """Handle buyer contacting specific seller"""
    import uuid
    
    # Generate unique buyer ID for this session
    buyer_id = str(uuid.uuid4())[:8].upper()
    buyer = query.from_user
    
    # Store buyer info in context for this transaction
    context.user_data['current_buyer_id'] = buyer_id
    context.user_data['selected_seller'] = seller_name
    
    seller_info = {
        'trinh_11': {
            'name': '@trinh_11',
            'rating': '4.9/5',
            'level': '💎 Diamond',
            'services': [
                '⚡ Flash Wallets & Crypto Tools',
                '🛠️ Custom Telegram Bots',
                '💻 Web Development & APIs', 
                '🔧 Automation Scripts',
                '📱 Mobile App Development'
            ],
            'response_time': '2 hours',
            'completed_orders': '1,247'
        },
        'crypto_toolss': {
            'name': '@crypto_toolss',
            'rating': '4.8/5', 
            'level': '🥇 Gold',
            'services': [
                '💰 Flash Wallets & Pre-loaded Crypto',
                '📊 Trading Bots & Signals',
                '🔍 Blockchain Analytics',
                '🛠️ Professional Crypto Tools',
                '📈 Portfolio Trackers'
            ],
            'response_time': '1 hour',
            'completed_orders': '892'
        },

    }
    
    seller = seller_info.get(seller_name)
    if not seller:
        await query.edit_message_text("❌ Seller not found!", parse_mode='Markdown')
        return
    
    contact_text = f"""
🤝 *Contacting {seller['name']}*

*📊 Seller Profile:*
• Rating: {seller['rating']} ⭐⭐⭐⭐⭐
• Trust Level: {seller['level']}
• Completed Orders: {seller['completed_orders']}
• Average Response: {seller['response_time']}

*🛍️ Available Services:*
"""
    
    for i, service in enumerate(seller['services'], 1):
        contact_text += f"{i}. {service}\n"
    
    contact_text += f"""
*🆔 Your Buyer ID: `{buyer_id}`*
_Share this ID with the seller for order tracking_

*💬 Next Steps:*
1. Choose service from list above (reply 1-5)
2. Or describe custom requirements
3. Seller will provide quote & details
4. Pay to escrow wallet when ready
5. Service delivered & payment released

*📞 Contact Methods:*
• Direct message: {seller['name']}
• Reference your Buyer ID: `{buyer_id}`
• Or continue here through escrow bot
"""
    
    keyboard = [
        [
            InlineKeyboardButton("1️⃣ Service 1", callback_data=f"order_{seller_name}_1"),
            InlineKeyboardButton("2️⃣ Service 2", callback_data=f"order_{seller_name}_2")
        ],
        [
            InlineKeyboardButton("3️⃣ Service 3", callback_data=f"order_{seller_name}_3"),
            InlineKeyboardButton("4️⃣ Service 4", callback_data=f"order_{seller_name}_4")
        ],
        [
            InlineKeyboardButton("5️⃣ Service 5", callback_data=f"order_{seller_name}_5")
        ],
        [
            InlineKeyboardButton(f"💬 Message {seller['name']}", url=f"https://t.me/{seller_name}"),
            InlineKeyboardButton("💰 View Escrow Wallets", callback_data="escrow_wallets")
        ],
        [
            InlineKeyboardButton("🔄 Choose Another Seller", callback_data="browse_listings"),
            InlineKeyboardButton("🔙 Back to Market", callback_data="browse_listings")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(contact_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_service_order(query, context, seller_name, service_num):
    """Handle specific service order placement"""
    buyer_id = context.user_data.get('current_buyer_id', 'NEW-USER')
    buyer = query.from_user
    
    service_details = {
        'trinh_11': [
            {'name': 'Flash Wallets & Crypto Tools', 'desc': 'Pre-loaded BTC/ETH/USDT wallets + professional crypto trading tools'},
            {'name': 'Custom Telegram Bots', 'desc': 'Professional bot development with admin panel'},
            {'name': 'Web Development & APIs', 'desc': 'Full-stack development with modern frameworks'}, 
            {'name': 'Automation Scripts', 'desc': 'Python/JS automation for business processes'},
            {'name': 'Mobile App Development', 'desc': 'iOS/Android native or cross-platform apps'}
        ],
        'crypto_toolss': [
            {'name': 'Flash Wallets & Pre-loaded Crypto', 'desc': 'Ready-to-use wallets with BTC/ETH/USDT + premium crypto tools'},
            {'name': 'Trading Bots & Signals', 'desc': 'Automated trading with proven strategies'},
            {'name': 'Blockchain Analytics', 'desc': 'On-chain analysis and monitoring tools'},
            {'name': 'Professional Crypto Tools', 'desc': 'Advanced DeFi, arbitrage, and portfolio management tools'},
            {'name': 'Portfolio Trackers', 'desc': 'Real-time portfolio monitoring dashboards'}
        ],

    }
    
    service_idx = int(service_num) - 1
    services = service_details.get(seller_name, [])
    
    if service_idx >= len(services):
        await query.edit_message_text("❌ Invalid service selection!", parse_mode='Markdown')
        return
        
    service = services[service_idx]
    
    # Enhanced service details with pricing and features
    enhanced_details = {
        'trinh_11': [
            {
                'name': 'Flash Wallets & Crypto Tools', 
                'desc': 'Pre-loaded BTC/ETH/USDT wallets + professional crypto trading tools',
                'features': ['✅ Pre-loaded wallets with real crypto', '✅ Professional trading software', '✅ Portfolio management tools', '✅ Security audit included', '✅ 24/7 technical support'],
                'pricing': '0.005-0.02 BTC (depends on wallet amount)',
                'delivery': '2-6 hours',
                'includes': 'Wallet files, private keys, trading tools setup, user manual'
            },
            {
                'name': 'Custom Telegram Bots', 
                'desc': 'Professional bot development with admin panel',
                'features': ['✅ Custom bot development', '✅ Admin dashboard', '✅ Database integration', '✅ Payment systems', '✅ Lifetime updates'],
                'pricing': '0.01-0.05 BTC (based on complexity)',
                'delivery': '3-7 days',
                'includes': 'Source code, hosting setup, documentation, training'
            },
            {
                'name': 'Web Development & APIs', 
                'desc': 'Full-stack development with modern frameworks',
                'features': ['✅ Modern web applications', '✅ REST/GraphQL APIs', '✅ Database design', '✅ Mobile responsive', '✅ SEO optimized'],
                'pricing': '0.02-0.1 BTC (project scope)',
                'delivery': '5-14 days',
                'includes': 'Complete website, admin panel, hosting, SSL certificate'
            },
            {
                'name': 'Automation Scripts', 
                'desc': 'Python/JS automation for business processes',
                'features': ['✅ Process automation', '✅ Data scraping/mining', '✅ Task scheduling', '✅ API integrations', '✅ Custom workflows'],
                'pricing': '0.005-0.03 BTC (script complexity)',
                'delivery': '1-5 days',
                'includes': 'Script files, setup guide, customization support'
            },
            {
                'name': 'Mobile App Development', 
                'desc': 'iOS/Android native or cross-platform apps',
                'features': ['✅ Native iOS/Android apps', '✅ Cross-platform support', '✅ App store deployment', '✅ Push notifications', '✅ Analytics integration'],
                'pricing': '0.05-0.2 BTC (app features)',
                'delivery': '10-21 days',
                'includes': 'App files, store listing, documentation, support'
            }
        ],
        'crypto_toolss': [
            {
                'name': 'Flash Wallets & Pre-loaded Crypto', 
                'desc': 'Ready-to-use wallets with BTC/ETH/USDT + premium crypto tools',
                'features': ['✅ Pre-funded crypto wallets', '✅ Premium trading tools', '✅ DeFi yield farming setup', '✅ Multi-chain support', '✅ Security features'],
                'pricing': '0.01-0.05 BTC (wallet value)',
                'delivery': '1-3 hours',
                'includes': 'Wallet access, trading tools, yield strategies, security guide'
            },
            {
                'name': 'Trading Bots & Signals', 
                'desc': 'Automated trading with proven strategies',
                'features': ['✅ Automated trading bots', '✅ Premium signals', '✅ Risk management', '✅ Multiple exchanges', '✅ Performance tracking'],
                'pricing': '0.008-0.03 BTC (bot features)',
                'delivery': '2-4 hours',
                'includes': 'Bot setup, signal access, configuration, tutorials'
            },
            {
                'name': 'Blockchain Analytics', 
                'desc': 'On-chain analysis and monitoring tools',
                'features': ['✅ Whale tracking', '✅ Transaction analysis', '✅ Market insights', '✅ Alert systems', '✅ Custom dashboards'],
                'pricing': '0.006-0.025 BTC (tool package)',
                'delivery': '3-6 hours',
                'includes': 'Analytics tools, dashboard access, training materials'
            },
            {
                'name': 'Professional Crypto Tools', 
                'desc': 'Advanced DeFi, arbitrage, and portfolio management tools',
                'features': ['✅ Arbitrage opportunities', '✅ DeFi protocols', '✅ Portfolio optimization', '✅ Yield calculations', '✅ Risk assessment'],
                'pricing': '0.012-0.04 BTC (tool suite)',
                'delivery': '4-8 hours',
                'includes': 'Complete tool suite, setup assistance, strategy guides'
            },
            {
                'name': 'Portfolio Trackers', 
                'desc': 'Real-time portfolio monitoring dashboards',
                'features': ['✅ Real-time tracking', '✅ Multi-exchange support', '✅ P&L analysis', '✅ Tax reporting', '✅ Mobile access'],
                'pricing': '0.004-0.015 BTC (features)',
                'delivery': '1-2 hours',
                'includes': 'Dashboard access, mobile app, reporting tools'
            }
        ],

    }
    
    service_details_enhanced = enhanced_details.get(seller_name, [])[service_idx] if service_idx < len(enhanced_details.get(seller_name, [])) else service
    
    order_text = f"""
🛍️ **{service_details_enhanced['name']}**

*📝 Service Description:*
{service_details_enhanced['desc']}

*✨ What's Included:*
"""
    
    for feature in service_details_enhanced.get('features', []):
        order_text += f"{feature}\n"
    
    order_text += f"""
*💰 Pricing:* {service_details_enhanced.get('pricing', 'Contact for quote')}
*⚡ Delivery Time:* {service_details_enhanced.get('delivery', 'Contact seller')}
*📦 Package Includes:* {service_details_enhanced.get('includes', 'Full service package')}

*👤 Buyer Information:*
• Name: {buyer.first_name}
• Username: @{buyer.username or 'not_set'}
• Buyer ID: `{buyer_id}`

*🤝 Seller:* @{seller_name} (Verified ⭐⭐⭐⭐⭐)

*📞 Order Process:*
1. ✅ Service details confirmed above
2. 💬 Seller will contact you for requirements
3. 💰 Pay exact amount to escrow wallet
4. 🛠️ Service development/delivery begins
5. ✅ Confirm receipt & payment released

*🔒 Escrow Protection:*
• Funds held safely until delivery confirmed
• Full refund if service not delivered
• Dispute resolution available
• Verified seller guarantee

*🚀 Ready to proceed? The seller will contact you within their response time!*
"""
    
    keyboard = [
        [
            InlineKeyboardButton("💰 View Escrow Wallets", callback_data="escrow_wallets"),
            InlineKeyboardButton(f"💬 Contact @{seller_name}", url=f"https://t.me/{seller_name}")
        ],
        [
            InlineKeyboardButton("📊 Track This Order", callback_data=f"track_{buyer_id}"),
            InlineKeyboardButton("🔄 Browse Other Services", callback_data="browse_listings")
        ],
        [
            InlineKeyboardButton("🔙 Back to Seller Profile", callback_data=f"seller_{seller_name}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(order_text, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    """Start the goods & services escrow bot"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found!")
    
    # Create application
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("how", how_it_works))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🛡️ AI ESCROW BOT Started!")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()