import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.database import (
    get_owner_data, add_commission, withdraw_commission, 
    get_analytics, get_all_users, update_user_balance,
    block_user, unblock_user, is_user_blocked,
    get_admin_spending_stats
)
from services.localization import get_text, format_number
from services.menu import update_menu

logger = logging.getLogger(__name__)
admin_router = Router()

class AdminStates(StatesGroup):
    """Admin panel FSM states"""
    change_commission_rate = State()
    block_user_id = State()
    unblock_user_id = State()

@admin_router.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    """Main admin dashboard with developer donations tracking"""
    # Get analytics data
    analytics = await get_analytics()
    owner_data = await get_owner_data()
    
    # Get donation statistics
    total_donations = owner_data.get("developer_donations", 0)
    donations_received = owner_data.get("total_donations_received", 0)
    withdrawn_donations = owner_data.get("withdrawn_donations", 0)
    available_donations = donations_received - withdrawn_donations
    
    base_text = await get_text(
        call.from_user.id, 
        "admin_panel",
        commission_balance=analytics["commission_balance"],
        total_users=analytics["total_users"],
        total_deposits=int(analytics["total_commissions"] / owner_data["commission_rate"]) if owner_data["commission_rate"] > 0 else 0,
        total_commissions=analytics["total_commissions"],
        commission_rate=owner_data["commission_rate"] * 100
    )
    
    # Get developer wallet balance (separate from user balance)
    developer_wallet = owner_data.get("developer_stars_wallet", 0)
    
    # Add donations section with separate wallet info
    donations_section = f"""

💝 <b>DEVELOPER DONATIONS</b>
├─ Total Donations: <code>{total_donations:,}</code> received
├─ Stars Received: <code>{donations_received:,}</code> stars
├─ Stars Withdrawn: <code>{withdrawn_donations:,}</code> stars
├─ Available to Withdraw: <code>{available_donations:,}</code> stars
├─ Developer Wallet: <code>{developer_wallet:,}</code> stars 🔒
└─ Community Support: {'🔥 Active' if total_donations > 0 else '💤 None yet'}

ℹ️ <b>Note:</b> Developer wallet is separate from user balance

"""
    
    text = base_text + donations_section
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_withdraw_commission"), 
                callback_data="withdraw_commission"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"💝 Withdraw Donations ({available_donations:,} ⭐)", 
                callback_data="withdraw_donations"
            )
        ],
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_detailed_report"), 
                callback_data="detailed_report"
            ),
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_change_commission"), 
                callback_data="change_commission_rate"
            )
        ],
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_manage_users"), 
                callback_data="manage_users"
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

@admin_router.callback_query(F.data == "withdraw_commission")
async def withdraw_commission_handler(call: CallbackQuery):
    """Withdraw all commission to owner balance"""
    owner_data = await get_owner_data()
    commission_balance = owner_data["commission_balance"]
    
    if commission_balance <= 0:
        await call.answer(await get_text(call.from_user.id, "no_commission"), show_alert=True)
        return
    
    # Transfer commission to owner's user balance
    await update_user_balance(call.from_user.id, commission_balance)
    
    # Reset commission balance
    await withdraw_commission(commission_balance)
    
    text = await get_text(
        call.from_user.id,
        "commission_withdrawn",
        amount=commission_balance
    )
    
    await call.message.answer(text)
    await call.answer()
    
    # Return to admin panel
    await admin_panel(call)

@admin_router.callback_query(F.data == "withdraw_donations")
async def withdraw_donations_handler(call: CallbackQuery):
    """
    FIXED: Withdraw developer donations to SEPARATE developer wallet (NOT user balance)
    This prevents donations from mixing with regular user deposits/withdrawals
    """
    owner_data = await get_owner_data()
    donations_balance = owner_data.get("total_donations_received", 0)
    withdrawn_donations = owner_data.get("withdrawn_donations", 0)
    available_donations = donations_balance - withdrawn_donations
    
    if available_donations <= 0:
        await call.answer("❌ No donations available for withdrawal!", show_alert=True)
        return
    
    # CRITICAL FIX: Transfer donations to SEPARATE developer wallet
    # DO NOT mix with regular user balance that affects normal deposits/withdrawals
    from services.database import save_owner_data
    
    # Add to separate developer stars wallet (NOT user balance)
    owner_data["developer_stars_wallet"] = owner_data.get("developer_stars_wallet", 0) + available_donations
    owner_data["withdrawn_donations"] = donations_balance
    owner_data["last_donation_withdrawal"] = datetime.now().isoformat()
    
    await save_owner_data(owner_data)
    
    text = (
        f"✅ <b>DONATIONS WITHDRAWN!</b>\n\n"
        f"💝 <b>Amount:</b> <code>{available_donations:,}</code> stars\n"
        f"📊 <b>Total Donations:</b> <code>{donations_balance:,}</code> stars\n"
        f"💳 <b>Status:</b> Transferred to DEVELOPER WALLET\n"
        f"🔒 <b>Security:</b> Separate from user balance\n\n"
        f"⚠️ <b>IMPORTANT:</b> These stars are in a separate\n"
        f"developer wallet and will NOT affect your regular\n"
        f"user balance or withdrawal calculations.\n\n"
        f"🙏 <b>Thank you for developing Area 51!</b>"
    )
    
    await call.message.answer(text)
    await call.answer()
    
    # Return to admin panel
    await admin_panel(call)

# تم إزالة معالج سحب النجوم المخصصة لأن النظام الجديد يحول الأرباح تلقائياً لرصيد الأدمن

@admin_router.callback_query(F.data == "detailed_report")
async def detailed_report(call: CallbackQuery):
    """Show detailed analytics report"""
    analytics = await get_analytics()
    
    avg_balance = analytics["total_balance"] // analytics["total_users"] if analytics["total_users"] > 0 else 0
    
    text = await get_text(
        call.from_user.id,
        "user_report",
        active_users=analytics["active_users"],
        total_balance=analytics["total_balance"],
        total_spent=analytics["total_spent"],
        avg_balance=avg_balance
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_back"), 
                callback_data="admin_panel"
            )
        ]
    ])
    
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()

@admin_router.callback_query(F.data == "change_commission_rate")
async def change_commission_rate_prompt(call: CallbackQuery, state: FSMContext):
    """Prompt to change commission rate"""
    current_rate = (await get_owner_data())["commission_rate"] * 100
    
    text = f"⚙️ <b>Change Commission Rate</b>\n\n" \
           f"Current rate: {current_rate:.1f}%\n\n" \
           f"Enter new commission rate (1-20%):\n\n" \
           f"/cancel — cancel"
    
    await call.message.edit_text(text, reply_markup=None)
    await state.set_state(AdminStates.change_commission_rate)
    await call.answer()

@admin_router.message(AdminStates.change_commission_rate)
async def process_commission_rate_change(message: Message, state: FSMContext):
    """Process commission rate change"""
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer(await get_text(message.from_user.id, "action_cancelled"))
        return
    
    try:
        new_rate = float(message.text.strip().replace('%', ''))
        if not 1 <= new_rate <= 20:
            raise ValueError("Rate out of range")
        
        # Update commission rate
        owner_data = await get_owner_data()
        owner_data["commission_rate"] = new_rate / 100
        
        from services.database import save_owner_data
        await save_owner_data(owner_data)
        
        await message.answer(
            f"✅ Commission rate updated to {new_rate:.1f}%"
        )
        
        await state.clear()
        
        # Update menu
        await update_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            message_id=message.message_id
        )
        
    except (ValueError, TypeError):
        await message.answer("🚫 Enter a valid number between 1 and 20. Try again.")

@admin_router.callback_query(F.data == "manage_users")
async def manage_users_menu(call: CallbackQuery):
    """User management menu"""
    users = await get_all_users()
    total_users = len(users)
    blocked_users = len([u for u in users if u.get("is_blocked", False)])
    
    text = f"👥 <b>User Management</b>\n\n" \
           f"📊 Total Users: {total_users:,}\n" \
           f"🚫 Blocked Users: {blocked_users:,}\n" \
           f"✅ Active Users: {total_users - blocked_users:,}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Block User", callback_data="block_user_prompt"),
            InlineKeyboardButton(text="✅ Unblock User", callback_data="unblock_user_prompt")
        ],
        [
            InlineKeyboardButton(text="📋 User List", callback_data="user_list")
        ],
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_back"), 
                callback_data="admin_panel"
            )
        ]
    ])
    
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()

@admin_router.callback_query(F.data == "block_user_prompt")
async def block_user_prompt(call: CallbackQuery, state: FSMContext):
    """Prompt to block user"""
    text = "🚫 <b>Block User</b>\n\n" \
           "Enter user ID to block:\n\n" \
           "/cancel — cancel"
    
    await call.message.edit_text(text, reply_markup=None)
    await state.set_state(AdminStates.block_user_id)
    await call.answer()

@admin_router.message(AdminStates.block_user_id)
async def process_block_user(message: Message, state: FSMContext):
    """Process user blocking"""
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer(await get_text(message.from_user.id, "action_cancelled"))
        return
    
    try:
        user_id = int(message.text.strip())
        
        if user_id == message.from_user.id:
            await message.answer("🚫 You cannot block yourself!")
            return
        
        success = await block_user(user_id)
        if success:
            await message.answer(f"✅ User {user_id} has been blocked")
        else:
            await message.answer(f"🚫 Failed to block user {user_id}")
        
        await state.clear()
        
    except ValueError:
        await message.answer("🚫 Enter a valid user ID. Try again.")

@admin_router.callback_query(F.data == "unblock_user_prompt")
async def unblock_user_prompt(call: CallbackQuery, state: FSMContext):
    """Prompt to unblock user"""
    text = "✅ <b>Unblock User</b>\n\n" \
           "Enter user ID to unblock:\n\n" \
           "/cancel — cancel"
    
    await call.message.edit_text(text, reply_markup=None)
    await state.set_state(AdminStates.unblock_user_id)
    await call.answer()

@admin_router.message(AdminStates.unblock_user_id)
async def process_unblock_user(message: Message, state: FSMContext):
    """Process user unblocking"""
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer(await get_text(message.from_user.id, "action_cancelled"))
        return
    
    try:
        user_id = int(message.text.strip())
        
        success = await unblock_user(user_id)
        if success:
            await message.answer(f"✅ User {user_id} has been unblocked")
        else:
            await message.answer(f"🚫 Failed to unblock user {user_id}")
        
        await state.clear()
        
    except ValueError:
        await message.answer("🚫 Enter a valid user ID. Try again.")

@admin_router.callback_query(F.data == "user_list")
async def show_user_list(call: CallbackQuery):
    """Show list of users with basic info"""
    users = await get_all_users()
    
    if not users:
        text = "👥 No users found"
    else:
        text = "👥 <b>User List (Last 10):</b>\n\n"
        
        # Sort by last activity and take last 10
        sorted_users = sorted(users, key=lambda x: x.get("last_active", ""), reverse=True)[:10]
        
        for user in sorted_users:
            user_id = user["user_id"]
            balance = user.get("balance", 0)
            total_spent = user.get("total_spent", 0)
            is_blocked = user.get("is_blocked", False)
            
            status = "🚫" if is_blocked else "✅"
            text += f"{status} <code>{user_id}</code> | ★{balance:,} | Spent: ★{total_spent:,}\n"
        
        if len(users) > 10:
            text += f"\n... and {len(users) - 10} more users"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=await get_text(call.from_user.id, "btn_back"), 
                callback_data="manage_users"
            )
        ]
    ])
    
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()

def register_admin_handlers(dp):
    """Register admin handlers"""
    dp.include_router(admin_router) 