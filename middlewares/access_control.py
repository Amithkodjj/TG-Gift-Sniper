# --- Стандартные библиотеки ---
import logging

# --- Сторонние библиотеки ---
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

class AccessControlMiddleware(BaseMiddleware):
    """
    Multi-user access control middleware.
    Allows all users but provides special privileges to owner.
    """
    FREE_CALLBACKS = {"guest_deposit_menu", "guest_refund_menu"}
    FREE_STATES = {"ConfigWizard:guest_deposit_amount", "ConfigWizard:guest_refund_id"}
    ADMIN_CALLBACKS = {"admin_panel", "withdraw_commission", "detailed_report", 
                      "change_commission_rate", "manage_users", "block_user_prompt", 
                      "unblock_user_prompt", "user_list"}

    def __init__(self, owner_id: int):
        """
        :param owner_id: Owner user ID with admin privileges.
        """
        self.owner_id = owner_id
        super().__init__()

    async def __call__(self, handler, event: TelegramObject, data: dict):
        """
        Multi-user access control with owner privileges and user blocking support.
        """
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        
        # Check if user is blocked
        from services.database import is_user_blocked
        if await is_user_blocked(user.id):
            try:
                if isinstance(event, CallbackQuery):
                    await event.answer("🚫 You are blocked from using this bot.", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer("🚫 You are blocked from using this bot.")
            except Exception as e:
                logger.error(f"Failed to send block message to user {user.id}: {e}")
            return
        
        # Set user privileges
        data["is_owner"] = (user.id == self.owner_id)
        
        # Admin-only callbacks
        if isinstance(event, CallbackQuery) and getattr(event, "data", None) in self.ADMIN_CALLBACKS:
            if user.id != self.owner_id:
                await event.answer("⛔️ Admin access required", show_alert=True)
                return
        
        # Auto-detect and set user language if not set
        from services.localization import detect_language_from_user
        from services.database import get_user_data, set_user_language
        
        try:
            user_data = await get_user_data(user.id)
            if not user_data.get("language"):
                detected_lang = detect_language_from_user(user)
                await set_user_language(user.id, detected_lang)
        except Exception as e:
            logger.error(f"Failed to set language for user {user.id}: {e}")
        
        # Allow free callbacks for all users
        if isinstance(event, CallbackQuery) and getattr(event, "data", None) in self.FREE_CALLBACKS:
            return await handler(event, data)
        
        # Allow free states for all users  
        fsm_state = data.get("state")
        if fsm_state:
            state_name = await fsm_state.get_state()
            if state_name in self.FREE_STATES:
                return await handler(event, data)
        
        # Allow invoice messages for all users
        if isinstance(event, Message) and getattr(event, "invoice", None):
            return await handler(event, data)
        
        # Allow successful payment messages for all users
        if isinstance(event, Message) and getattr(event, "successful_payment", None):
            return await handler(event, data)
        
        return await handler(event, data)