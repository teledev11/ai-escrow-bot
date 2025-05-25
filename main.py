"""
Main entry point for the Telegram Escrow Bot.
This file initializes the bot and starts polling.
"""
import logging
import os
from bot import setup_bot
from flask import Flask, render_template
from initialize_db import initialize_database
from db_models import create_tables

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Set secret key
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))

# Get bot username for the template
bot_username = os.environ.get("BOT_USERNAME", "Secure_P2P_bot")

@app.route('/')
def index():
    """Main page that displays information about the bot."""
    return render_template('index.html', bot_username=bot_username)

@app.route('/features')
def features():
    """Page with detailed features of the escrow bot."""
    return render_template('features.html', bot_username=bot_username)

# Initialize database before starting the bot
def ensure_database_setup():
    """Make sure the database is set up correctly."""
    try:
        logger.info("Initializing database...")
        success = initialize_database()
        if success:
            logger.info("Database initialized successfully.")
            return True
        else:
            logger.error("Failed to initialize database.")
            # Fallback to just creating tables
            try:
                create_tables()
                logger.info("Tables created successfully using fallback method.")
                return True
            except Exception as e:
                logger.error(f"Failed to create tables: {e}")
                return False
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        return False

# This is used when running under Gunicorn for the web interface
if __name__ == '__main__':
    # Run the bot in the main thread when started directly
    try:
        # Initialize database first
        db_ready = ensure_database_setup()
        if not db_ready:
            logger.warning("Database might not be fully initialized. Bot may encounter issues.")
        
        # Set up and start the goods & services escrow bot
        from goods_escrow_bot import main as run_bot
        
        logger.info("Starting AI ESCROW BOT...")
        run_bot()
    except Exception as e:
        logger.error(f"Error in main function: {e}")
