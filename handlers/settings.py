import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.database import set_user_language
from services.localization import get_text
from services.menu import update_menu

logger = logging.getLogger(__name__)
settings_router = Router()

@settings_router.callback_query(F.data == "settings_menu")
async def settings_menu(call: CallbackQuery):
    """Show settings menu"""
    text = await get_text(call.from_user.id, "settings_menu", default="⚙️ <b>Settings</b>")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_language"), 
                callback_data="language_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_main_menu"), 
                callback_data="main_menu"
            )
        ]
    ])
    
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()

@settings_router.callback_query(F.data == "language_menu")
async def language_menu(call: CallbackQuery):
    """Show language selection menu"""
    text = await get_text(call.from_user.id, "language_select")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 English (Active)", callback_data="language_en_selected")
        ],
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_back"), 
                callback_data="settings_menu"
            )
        ]
    ])
    
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()

@settings_router.callback_query(F.data.startswith("set_language_"))
async def set_language_handler(call: CallbackQuery):
    """Handle language change"""
    language = call.data.split("_")[-1]  # Extract language code
    
    # Set user language
    await set_user_language(call.from_user.id, language)
    
    # Send confirmation message
    success_text = await get_text(call.from_user.id, "language_changed")
    await call.message.answer(success_text)
    
    # Update menu with new language - Remove is_owner parameter since call.data is string
    await update_menu(
        bot=call.bot,
        chat_id=call.message.chat.id,
        user_id=call.from_user.id,
        message_id=call.message.message_id
    )
    await call.answer()

def register_settings_handlers(dp):
    """Register settings handlers"""
    dp.include_router(settings_router) 