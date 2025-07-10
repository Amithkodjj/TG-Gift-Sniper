# External libraries
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Internal libraries
from services.database import get_user_data, save_user_data
from services.localization import get_text, get_target_display

async def update_last_menu_message_id(user_id: int, message_id: int):
    """
    Saves the last menu message ID for a user.
    """
    user_data = await get_user_data(user_id)
    user_data["last_menu_message_id"] = message_id
    await save_user_data(user_id, user_data)


async def get_last_menu_message_id(user_id: int):
    """
    Returns the last menu message ID for a user.
    """
    user_data = await get_user_data(user_id)
    return user_data.get("last_menu_message_id")


async def config_action_keyboard(user_id: int, is_owner: bool = False) -> InlineKeyboardMarkup:
    """
    Generates inline keyboard for menu actions with localization.
    """
    user_data = await get_user_data(user_id)
    is_active = user_data.get("active", False)
    
    toggle_text = await get_text(user_id, "toggle_btn_off" if is_active else "toggle_btn_on")
    
    keyboard = [
        # Main control buttons
        [
            InlineKeyboardButton(text=toggle_text, callback_data="toggle_active")
        ],
        # Management buttons
        [
            InlineKeyboardButton(text=await get_text(user_id, "profiles_btn"), callback_data="profiles_menu"),
            InlineKeyboardButton(text=await get_text(user_id, "reset_btn"), callback_data="reset_bought")
        ],
        # Financial buttons
        [
            InlineKeyboardButton(text=await get_text(user_id, "deposit_btn"), callback_data="deposit_menu"),
            InlineKeyboardButton(text=await get_text(user_id, "withdraw_btn"), callback_data="refund_menu")
        ],
        # Store and settings
        [
            InlineKeyboardButton(text=await get_text(user_id, "gift_catalog_btn"), callback_data="catalog")
        ],
        [
            InlineKeyboardButton(text=await get_text(user_id, "settings_btn"), callback_data="settings_menu"),
            InlineKeyboardButton(text=await get_text(user_id, "help_btn"), callback_data="show_help")
        ]
    ]
    
    # Add admin panel for owner
    if is_owner:
        keyboard.insert(1, [
            InlineKeyboardButton(text=await get_text(user_id, "admin_panel_btn"), callback_data="admin_panel")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def update_menu(bot, chat_id: int, user_id: int, message_id: int, is_owner: bool = False):
    """
    Updates menu in chat: deletes previous and sends new one.
    """
    await delete_menu(bot=bot, chat_id=chat_id, user_id=user_id, current_message_id=message_id)
    text = await format_user_summary(user_id)
    await send_menu(bot=bot, chat_id=chat_id, user_id=user_id, text=text, is_owner=is_owner)


async def delete_menu(bot, chat_id: int, user_id: int, current_message_id: int = None):
    """
    Deletes the last menu message if it differs from current.
    """
    last_menu_message_id = await get_last_menu_message_id(user_id)
    if last_menu_message_id and last_menu_message_id != current_message_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=last_menu_message_id)
        except TelegramBadRequest as e:
            error_text = str(e)
            if "message can't be deleted for everyone" in error_text:
                outdated_text = await get_text(
                    user_id, 
                    "menu_outdated", 
                    default="⚠️ Previous menu is outdated and cannot be deleted (more than 48 hours passed). Use the current menu."
                )
                await bot.send_message(chat_id, outdated_text)
            elif "message to delete not found" in error_text:
                pass
            else:
                raise


async def send_menu(bot, chat_id: int, user_id: int, text: str, is_owner: bool = False) -> int:
    """
    Sends new menu to chat and updates last message ID.
    """
    keyboard = await config_action_keyboard(user_id, is_owner)
    sent = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard
    )
    await update_last_menu_message_id(user_id, sent.message_id)
    return sent.message_id


async def format_user_summary(user_id: int) -> str:
    """
    Formats user summary for main menu with localization.
    """
    from services.database import get_owner_data
    
    user_data = await get_user_data(user_id)
    owner_data = await get_owner_data()
    profiles = user_data.get("profiles", [])
    balance = user_data.get("balance", 0)
    is_owner = user_id == owner_data.get("owner_id", user_id)
    
    # Determine status
    is_active = user_data.get("active", False)
    status = await get_text(user_id, "status_active" if is_active else "status_inactive")
    
    # Choose appropriate menu template
    if is_owner:
        # Owner sees commission data and system stats
        from services.database import get_analytics, get_admin_spending_stats
        analytics = await get_analytics()
        spending_stats = await get_admin_spending_stats()
        
        text = await get_text(user_id, "main_menu_title", 
                            version="2.0.0",
                            balance=balance,  # FIXED: Use actual user balance, not stars_balance
                            active_users=analytics["active_users"], 
                            commission_balance=owner_data.get("commission_balance", 0),
                            commission_rate=int(owner_data.get("commission_rate", 0.10) * 100),
                            status=status)
        
        # Gift purchasing and earnings statistics
        admin_share_earned = owner_data.get("total_admin_share_earned", 0)
        spending_text = f"""

🎁 <b>GIFT & EARNINGS ANALYTICS</b>
├─ Total Stars Spent: <code>{spending_stats['total_stars_spent_on_gifts']:,}</code> coins
├─ Total Gifts Purchased: <code>{spending_stats['total_gifts_purchased']:,}</code> items
├─ Auto-Transferred (10%): <code>{admin_share_earned:,}</code> coins
└─ Last Purchase: {spending_stats['last_gift_purchase'][:19] if spending_stats['last_gift_purchase'] else 'None'}

💡 <b>Note:</b> 10% from each gift purchase is automatically transferred to your balance"""
        
        text += spending_text
    else:
        # Regular user sees their data
        text = await get_text(user_id, "main_menu_user", 
                            version="2.0.0",
                            balance=balance,
                            profiles_count=len(profiles),
                            status=status)
    
    # Add profile summaries only for users with profiles
    if profiles:
        user_language = user_data.get("language", "en")
        
        for idx, profile in enumerate(profiles, 1):
            target_display = get_target_display(profile, user_id, user_language)
            
            # Status indicators - English only
            if profile.get('done', False):
                status_emoji = "✅ COMPLETE"
                state_color = "🟢"
            elif profile.get('spent', 0) > 0:
                status_emoji = "⚡ ACTIVE"
                state_color = "🟡"
            else:
                status_emoji = "⏳ PENDING"
                state_color = "🔵"
            
            # English profile display only
            profile_line = f"\n\n📊 <b>PROFILE {idx}</b>\n"
            profile_line += f"├─ Status: <code>{status_emoji}</code> {state_color}\n"
            profile_line += f"├─ Price Range: <code>{profile.get('MIN_PRICE'):,}</code> - <code>{profile.get('MAX_PRICE'):,}</code> coins\n"
            profile_line += f"├─ Supply Range: <code>{profile.get('MIN_SUPPLY'):,}</code> - <code>{profile.get('MAX_SUPPLY'):,}</code> left\n"
            profile_line += f"├─ Progress: <code>{profile.get('BOUGHT'):,}/{profile.get('COUNT'):,}</code> gifts\n"
            profile_line += f"├─ Spent: <code>{profile.get('SPENT'):,}/{profile.get('LIMIT'):,}</code> coins\n"
            profile_line += f"└─ Target: {target_display}\n"
            
            text += profile_line
    
    return text


def payment_keyboard(amount):
    """
    Generates inline keyboard with payment button for invoice.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Deposit ★{amount:,}", pay=True)
    return builder.as_markup()