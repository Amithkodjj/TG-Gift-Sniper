#!/usr/bin/env python3
# --- Стандартные библиотеки ---
import asyncio
import logging
import os
import sys
# --- Сторонние библиотеки ---
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
# --- Внутренние модули ---
from services.database import (
    get_user_data, save_user_data, migrate_from_single_user,
    get_owner_data, ensure_directories
)
from services.localization import get_text, detect_language_from_user, get_target_display
from services.menu import update_menu
from services.balance import refresh_balance
from services.gifts import get_filtered_gifts
from services.buy import buy_gift
from handlers.handlers_wizard import register_wizard_handlers
from handlers.handlers_catalog import register_catalog_handlers
from handlers.handlers_main import register_main_handlers
from handlers.admin import register_admin_handlers
from handlers.settings import register_settings_handlers
from utils.logging import setup_logging
from middlewares.access_control import AccessControlMiddleware
from middlewares.rate_limit import RateLimitMiddleware

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("TELEGRAM_USER_ID"))
VERSION = "2.0.0"  # Updated version for multi-user

# Optional environment variables with defaults
PURCHASE_COOLDOWN = float(os.getenv("PURCHASE_COOLDOWN", "0.3"))
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
MAX_PROFILES = int(os.getenv("MAX_PROFILES", "3"))

setup_logging()
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Updated middleware for multi-user support
from middlewares.commission import CommissionMiddleware

dp.message.middleware(RateLimitMiddleware(commands_limits={"/start": 3, "/withdraw_all": 3}))
dp.message.middleware(AccessControlMiddleware(OWNER_ID))
dp.message.middleware(CommissionMiddleware(OWNER_ID))
dp.callback_query.middleware(AccessControlMiddleware(OWNER_ID))

register_wizard_handlers(dp)
register_catalog_handlers(dp)
register_main_handlers(dp=dp, bot=bot, version=VERSION)
register_admin_handlers(dp)
register_settings_handlers(dp)


async def gift_purchase_worker():
    """
    Multi-user background worker for gift purchases.
    Processes all active users and their profiles.
    """
    while True:
        try:
            from services.database import get_all_users, is_user_blocked
            
            # Get all users
            all_users = await get_all_users()
            
            for user_data in all_users:
                user_id = user_data["user_id"]
                
                # Skip blocked users
                if await is_user_blocked(user_id):
                    continue
                
                # Check if user has any active profiles
                has_active_profiles = False
                for profile in user_data.get("profiles", []):
                    if not profile.get("DONE", False):
                        has_active_profiles = True
                        break
                
                if not has_active_profiles:
                    continue
                
                # Process user's profiles
                await process_user_profiles(user_id, user_data)
                
        except Exception as e:
            logger.error(f"Error in gift_purchase_worker: {e}")

        await asyncio.sleep(1)  # Check every second for all users

async def process_user_profiles(user_id: int, user_data: dict):
    """Process gift purchases for a specific user's profiles"""
    try:
        # Refresh user balance
        user_balance = user_data.get("balance", 0)
        if user_balance <= 0:
            return
        
        profiles = user_data.get("profiles", [])
        progress_made = False
        report_lines = []
        
        for profile_index, profile in enumerate(profiles):
            # Skip completed profiles
            if profile.get("DONE", False):
                continue
            
            # Extract profile parameters
            MIN_PRICE = profile.get("MIN_PRICE", 5000)
            MAX_PRICE = profile.get("MAX_PRICE", 10000)
            MIN_SUPPLY = profile.get("MIN_SUPPLY", 1000)
            MAX_SUPPLY = profile.get("MAX_SUPPLY", 10000)
            COUNT = profile.get("COUNT", 5)
            LIMIT = profile.get("LIMIT", 1000000)
            TARGET_USER_ID = profile.get("TARGET_USER_ID")
            TARGET_CHAT_ID = profile.get("TARGET_CHAT_ID")
            
            # Get filtered gifts
            filtered_gifts = await get_filtered_gifts(
                bot, MIN_PRICE, MAX_PRICE, MIN_SUPPLY, MAX_SUPPLY
            )
            
            if not filtered_gifts:
                continue
            
            purchases = []
            before_bought = profile.get("BOUGHT", 0)
            before_spent = profile.get("SPENT", 0)
            
            # Try to buy gifts
            for gift in filtered_gifts:
                gift_id = gift["id"]
                gift_price = gift["price"]
                sticker_file_id = gift["sticker_file_id"]
                
                # Check limits before purchase
                while (profile.get("BOUGHT", 0) < COUNT and 
                       profile.get("SPENT", 0) + gift_price <= LIMIT and
                       user_data["balance"] >= gift_price):
                    
                    success = await buy_gift(
                        bot=bot,
                        env_user_id=user_id,
                        gift_id=gift_id,
                        user_id=TARGET_USER_ID,
                        chat_id=TARGET_CHAT_ID,
                        gift_price=gift_price,
                        file_id=sticker_file_id
                    )
                    
                    if not success:
                        break
                    
                    # Update profile and user data
                    profile["BOUGHT"] = profile.get("BOUGHT", 0) + 1
                    profile["SPENT"] = profile.get("SPENT", 0) + gift_price
                    user_data["balance"] -= gift_price
                    user_data["total_spent"] = user_data.get("total_spent", 0) + gift_price
                    
                    purchases.append({"id": gift_id, "price": gift_price})
                    
                    # Save updated data
                    await save_user_data(user_id, user_data)
                    await asyncio.sleep(PURCHASE_COOLDOWN)
                    
                    # Check if limits reached
                    if profile["SPENT"] >= LIMIT:
                        break
                
                if profile.get("BOUGHT", 0) >= COUNT or profile.get("SPENT", 0) >= LIMIT:
                    break
            
            # Check if profile is completed
            after_bought = profile.get("BOUGHT", 0)
            after_spent = profile.get("SPENT", 0)
            
            if (after_bought >= COUNT or after_spent >= LIMIT) and not profile.get("DONE", False):
                profile["DONE"] = True
                await save_user_data(user_id, user_data)
                
                # Get user language for notifications
                user_language = user_data.get("language", "en")
                target_display = get_target_display(profile, user_id, user_language)
                
                # Send completion notification
                completion_text = await get_text(user_id, "purchase_complete")
                
                try:
                    await bot.send_message(user_id, completion_text)
                except Exception as e:
                    logger.error(f"Failed to send completion notification to {user_id}: {e}")
                
                progress_made = True
                logger.info(f"Profile #{profile_index+1} completed for user {user_id}")
            
            elif after_bought > before_bought or after_spent > before_spent:
                progress_made = True
                logger.info(f"Progress made on profile #{profile_index+1} for user {user_id}")
        
        # Update user data if progress was made
        if progress_made:
            await save_user_data(user_id, user_data)
            
    except Exception as e:
        logger.error(f"Error processing profiles for user {user_id}: {e}")


async def main() -> None:
    """
    Entry point: initialization, migration, and start polling.
    Multi-user system with commission support.
    """
    logger.info("Multi-user TelegramGiftsBot v2.0.0 started!")
    
    # Ensure directories exist
    await ensure_directories()
    
    # Try to migrate from single-user config if exists
    migration_success = await migrate_from_single_user("config.json", OWNER_ID)
    if migration_success:
        logger.info("Successfully migrated from single-user to multi-user system")
    
    # Initialize owner data
    await get_owner_data()
    
    # Create owner user profile if not exists
    await get_user_data(OWNER_ID)
    
    # Start background worker
    asyncio.create_task(gift_purchase_worker())
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
