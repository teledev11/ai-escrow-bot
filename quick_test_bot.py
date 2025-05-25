#!/usr/bin/env python3
"""
Quick test to verify the bot registration is working properly.
"""
import asyncio
import os
import logging
from telegram import Bot

async def test_registration():
    """Test the bot's basic functionality."""
    try:
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ Bot token not found!")
            return False
            
        bot = Bot(token)
        me = await bot.get_me()
        
        print(f"✅ Bot is working!")
        print(f"Bot Name: {me.first_name}")
        print(f"Username: @{me.username}")
        print(f"Bot ID: {me.id}")
        
        # Test database connection
        from db_models import get_db_session
        session = get_db_session()
        
        # Check if we can query the users table
        from sqlalchemy import text
        result = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"✅ Database connected! Users count: {result}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_registration())