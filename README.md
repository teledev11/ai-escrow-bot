# Telegram Escrow Bot

A secure, feature-rich Telegram bot that facilitates escrow transactions between buyers and sellers for digital goods and services. The bot supports both fiat and cryptocurrency payments, providing a safe environment for conducting online transactions.

## Features

- **Secure Escrow System**: Protect both buyers and sellers during transactions
- **Multiple Payment Methods**: Support for both fiat (Bank Transfer, PayPal, etc.) and cryptocurrencies (Bitcoin, Ethereum, etc.)
- **Dispute Resolution**: Built-in dispute handling and resolution process
- **Transaction Tracking**: Real-time transaction status updates and notifications
- **User Management**: Simple registration and profile management
- **Wallet Management**: Basic escrow wallet functionality

## Commands

### General Commands
- `/start` - Start the bot
- `/help` - Show help message with available commands
- `/register` - Register as a new user
- `/profile` - View your profile information

### Transaction Commands
- `/new` - Create a new transaction
- `/transactions` - List your transactions
- `/details [ID]` - View transaction details
- `/cancel [ID]` - Cancel a transaction
- `/complete [ID]` - Complete a transaction

### Payment Commands
- `/payment_methods` - View your payment methods
- `/add_payment` - Add a new payment method
- `/pay [ID]` - Send payment for a transaction
- `/confirm_payment [ID]` - Confirm receipt of payment

### Dispute Commands
- `/dispute [ID]` - Open a dispute for a transaction
- `/resolve [ID]` - Resolve a dispute (admin only)
- `/dispute_details [ID]` - View dispute details

## Transaction Flow

1. **Creation**: Seller creates a transaction with `/new` command
2. **Funding**: Buyer funds the transaction with `/pay`
3. **Confirmation**: Seller confirms payment receipt
4. **Delivery**: Seller delivers the goods/services
5. **Completion**: Buyer confirms receipt and completes the transaction
6. **Settlement**: Funds are released to the seller

## Setup Instructions

### Prerequisites

- Python 3.8+
- A Telegram Bot Token (obtained from [@BotFather](https://t.me/BotFather))

### Environment Variables

Set up the following environment variables:

