#!/usr/bin/env python3
"""
Area 51 Bot v2.1.0 - Clean, Professional Implementation
Demonstrates the new modular structure and clean code organization
"""
import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Import our clean modules
from core.config import config
from handlers.admin_clean import register_admin_handlers
# from handlers.user import register_user_handlers      # Would be implemented similarly
# from handlers.payments import register_payment_handlers # Would be implemented similarly
# from middlewares.auth import AuthMiddleware             # Would be implemented
# from middlewares.logging import LoggingMiddleware       # Would be implemented

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Bot start time for uptime tracking
BOT_START_TIME = datetime.now()

class AreaBot:
    """Main bot class with clean initialization and management"""
    
    def __init__(self):
        """Initialize bot with clean configuration"""
        self.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self._setup_handlers()
        self._setup_middlewares()
    
    def _setup_handlers(self):
        """Register all handler groups"""
        logger.info("Setting up handlers...")
        
        # Register admin handlers
        register_admin_handlers(self.dp)
        
        # Register other handler groups
        # register_user_handlers(self.dp)
        # register_payment_handlers(self.dp)
        # register_gift_handlers(self.dp)
        
        logger.info("All handlers registered successfully")
    
    def _setup_middlewares(self):
        """Setup middleware for authentication, logging, etc."""
        logger.info("Setting up middlewares...")
        
        # Add custom middlewares here
        # self.dp.middleware.setup(AuthMiddleware())
        # self.dp.middleware.setup(LoggingMiddleware())
        
        logger.info("Middlewares configured")
    
    async def start(self):
        """Start the bot with clean startup process"""
        try:
            logger.info(f"🛸 {config.BOT_NAME} v{config.BOT_VERSION} starting...")
            
            # Validate configuration
            logger.info("Validating configuration...")
            if not config.BOT_TOKEN or not config.OWNER_ID:
                raise ValueError("Missing required configuration")
            
            # Setup database directories
            await self._ensure_directories()
            
            # Start polling
            logger.info(f"Bot @{(await self.bot.get_me()).username} starting polling...")
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    async def _ensure_directories(self):
        """Ensure required directories exist"""
        import os
        directories = [
            config.USER_DATA_DIR,
            config.LOGS_DIR,
            "data"
        ]
        
        for directory in directories:
            os.makedirs(directory, mode=0o755, exist_ok=True)
        
        logger.info("Data directories ensured")
    
    async def stop(self):
        """Clean shutdown process"""
        logger.info("Stopping bot...")
        await self.bot.session.close()
        logger.info("Bot stopped successfully")

async def main():
    """Main entry point"""
    bot = AreaBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Set bot start time for uptime tracking
    BOT_START_TIME = datetime.now()
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 