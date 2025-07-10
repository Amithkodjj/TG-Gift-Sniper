# --- Стандартные библиотеки ---
import asyncio
import logging
import random

# --- Сторонние библиотеки ---
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramRetryAfter

# --- Внутренние модули ---
from services.database import get_user_data, save_user_data, update_user_balance, get_owner_data, save_owner_data
from services.config import DEV_MODE
from datetime import datetime

logger = logging.getLogger(__name__)

async def transfer_admin_share_from_gift(gift_price: int, buyer_user_id: int):
    """
    تحويل 10% من سعر الهدية تلقائياً إلى رصيد الأدمن
    """
    try:
        owner_data = await get_owner_data()
        admin_user_id = owner_data.get("owner_id")
        
        if not admin_user_id:
            logger.error("Admin user ID not found in owner_data")
            return
        
        # حساب 10% من سعر الهدية
        admin_share_rate = 0.10  # 10%
        admin_share = int(gift_price * admin_share_rate)
        
        if admin_share <= 0:
            return
        
        # إضافة المبلغ مباشرة إلى رصيد الأدمن (كمستخدم عادي)
        await update_user_balance(admin_user_id, admin_share)
        
        # تحديث إحصائيات الهدايا
        owner_data["total_stars_spent_on_gifts"] = owner_data.get("total_stars_spent_on_gifts", 0) + gift_price
        owner_data["total_gifts_purchased"] = owner_data.get("total_gifts_purchased", 0) + 1
        owner_data["last_gift_purchase"] = datetime.now().isoformat()
        
        # تحديث إجمالي المبالغ المحولة للأدمن
        owner_data["total_admin_share_earned"] = owner_data.get("total_admin_share_earned", 0) + admin_share
        
        await save_owner_data(owner_data)
        
        # تسجيل العملية
        from services.database import log_transaction
        await log_transaction("admin_share_from_gift", {
            "gift_price": gift_price,
            "admin_share": admin_share,
            "admin_share_rate": admin_share_rate,
            "buyer_user_id": buyer_user_id,
            "admin_user_id": admin_user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Admin share transferred: {admin_share} stars (10% of {gift_price}) → Admin balance")
        
    except Exception as e:
        logger.error(f"Failed to transfer admin share from gift: {e}")

async def buy_gift(
    bot,
    env_user_id,
    gift_id,
    user_id,
    chat_id,
    gift_price,
    file_id,
    retries=3,
    add_test_purchases=False
):
    """
    Покупает подарок с заданными параметрами и количеством попыток.
    
    Аргументы:
        bot: Экземпляр бота.
        env_user_id: ID пользователя из окружения (конфиг).
        gift_id: ID подарка.
        user_id: ID пользователя-получателя (может быть None).
        chat_id: ID чата-получателя (может быть None).
        gift_price: Стоимость подарка.
        file_id: ID файла (не используется в этой версии бота).
        retries: Количество попыток при ошибках.

    Возвращает:
        True, если покупка успешна, иначе False.
    """
    # Тестовая логика
    if add_test_purchases or DEV_MODE:
        result = random.choice([True, True, True, False])
        logger.info(f"[ТЕСТ] ({result}) Покупка подарка {gift_id} за {gift_price} (имитация, баланс не трогаем)")
        return result
    
    # Normal logic for multi-user system
    user_data = await get_user_data(env_user_id)
    balance = user_data.get("balance", 0)
    
    if balance < gift_price:
        logger.error(f"Insufficient stars for gift {gift_id} (required: {gift_price}, available: {balance})")
        return False
    
    for attempt in range(1, retries + 1):
        try:
            if user_id is not None and chat_id is None:
                result = await bot.send_gift(gift_id=gift_id, user_id=user_id)
            elif user_id is None and chat_id is not None:
                result = await bot.send_gift(gift_id=gift_id, chat_id=chat_id)
            else:
                break

            if result:
                new_balance = await update_user_balance(env_user_id, -gift_price)
                
                # CRITICAL: تحويل 10% من سعر الهدية تلقائياً لرصيد الأدمن
                await transfer_admin_share_from_gift(gift_price, env_user_id)
                
                logger.info(f"Successful gift purchase {gift_id} for {gift_price} stars. Remaining: {new_balance}")
                return True
            
            logger.error(f"Попытка {attempt}/{retries}: Не удалось купить подарок {gift_id}. Повтор...")

        except TelegramRetryAfter as e:
            logger.error(f"Flood wait: ждём {e.retry_after} секунд")
            await asyncio.sleep(e.retry_after)

        except TelegramNetworkError as e:
            logger.error(f"Попытка {attempt}/{retries}: Сетевая ошибка: {e}. Повтор через {2**attempt} секунд...")
            await asyncio.sleep(2**attempt)

        except TelegramAPIError as e:
            logger.error(f"Ошибка Telegram API: {e}")
            break

    logger.error(f"Не удалось купить подарок {gift_id} после {retries} попыток.")
    return False