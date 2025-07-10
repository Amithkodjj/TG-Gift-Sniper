import logging
from typing import Dict, Any
from services.database import get_user_language

logger = logging.getLogger(__name__)

# Text translations
TEXTS = {
    "en": {
        # Main Menu  
        "main_menu_title": "🛸 <b>Area 51 Control Center</b>\n<code>v{version}</code>\n\n"
                          "📊 <b>SYSTEM STATUS</b>\n"
                          "├─ Status: {status}\n"
                          "├─ Active Users: <code>{active_users:,}</code>\n"
                          "├─ Commission Rate: <code>{commission_rate}%</code>\n\n"
                          "💰 <b>FINANCIAL OVERVIEW</b>\n"
                          "├─ Your Balance: <code>{balance:,}</code> coins\n"
                          "├─ Commission Earned: <code>{commission_balance:,}</code> coins\n\n",
        "main_menu_user": "🛸 <b>Area 51 Bot</b>\n<code>v{version}</code>\n\n"
                         "💰 <b>YOUR ACCOUNT</b>\n"
                         "├─ Balance: <code>{balance:,}</code> coins\n"
                         "├─ Profiles: <code>{profiles_count}</code> active\n"
                         "├─ Status: {status}\n\n",
        
        # Buttons
        "deposit_btn": "💎 Deposit Stars",
        "withdraw_btn": "💸 Withdraw Funds",
        "gift_catalog_btn": "🛍️ Gift Store",
        "settings_btn": "⚙️ Settings",
        "help_btn": "❓ Help & Info",
        "admin_panel_btn": "👑 Owner Panel",
        "profiles_btn": "📋 Manage Profiles",
        "toggle_btn_on": "🚀 Activate Bot",
        "toggle_btn_off": "⏸️ Pause Bot",
        "reset_btn": "🔄 Reset Statistics",
        "language_btn": "🌐 Language",
        
        # Status
        "status_active": "🟢 <code>ONLINE</code>",
        "status_inactive": "🔴 <code>OFFLINE</code>",
        
        # Help and other texts
        "help_text": "🤖 <b>Area 51 Bot Guide</b>\n<code>v{version}</code>\n\n"
                    "🎮 <b>MAIN CONTROLS</b>\n\n"
                    "🟢 <b>Activate</b> • 🔴 <b>Pause</b>\n"
                    "Start or stop automatic purchases\n\n"
                    "📋 <b>Manage Profiles</b>\n"
                    "Configure gift buying settings\n"
                    "Set price ranges & quantities\n"
                    "Choose recipients\n\n"
                    "🔄 <b>Reset Statistics</b>\n"
                    "Clear purchase counters\n\n"
                    "💎 <b>Deposit Stars</b>\n"
                    "Add funds (10% commission)\n\n"
                    "💸 <b>Withdraw Funds</b>\n"
                    "Get your stars back\n"
                    "Use transaction ID or <code>/withdraw_all</code>\n\n"
                    "🛍️ <b>Gift Store</b>\n"
                    "Browse and purchase gifts manually\n\n"
                    "💡 <b>IMPORTANT TIPS</b>\n\n"
                    "🎯 <b>Recipients must start bot</b>\n"
                    "Send them <code>@{bot_username}</code>\n\n"
                    "👤 <b>User ID recipients</b>\n"
                    "Get ID from @userinfobot\n\n"
                    "📢 <b>Channel recipients</b>\n"
                    "Use @channel_username format\n\n"
                    "🆔 <b>Transaction ID</b>\n"
                    "Click payment message to view\n\n"
                    "⚠️ <b>FREE WITHDRAWAL</b>\n"
                    "Withdraw ALL stars without fees\n"
                    "if you haven't bought gifts yet!\n"
                    "Perfect for testing safely.\n\n"
                    "🔗 <b>Community:</b> @Snipershot69\n"
                    "💻 <b>Developer:</b> @TheSniper051",
        
        "donate_to_dev_button": "💝 Donate to Dev (★100)",
        "contact_dev_button": "💬 Contact Developer",
        "back_to_menu": "☰ Back to Menu",
        "no_profiles": "❌ No profiles configured. Please add a profile first.",
        "donation_success": "✅ <b>DONATION SUCCESSFUL!</b>\n\n💝 Thank you for your support!\n🙏 Your donation helps improve the bot.",
        "donation_failed": "❌ <b>DONATION FAILED</b>\n\nPlease try again or contact support.",
        "counters_reset": "Purchase counter reset.",
        "status_updated": "Status updated",
        
        # Commission system
        "deposit_success": "✅ <b>DEPOSIT SUCCESSFUL!</b>\n\n"
                          "💰 <b>Deposited:</b> <code>{total_amount}</code> coins\n"
                          "💸 <b>Fee ({rate}%):</b> <code>{commission}</code> coins\n"
                          "🎯 <b>Your Balance:</b> <code>{user_amount}</code> coins\n\n"
                          "🙏 Thank you for using our service!",
        
        "commission_notification": "💰 <b>NEW COMMISSION!</b>\n\n"
                                  "👤 <b>From:</b> {user_name}\n"
                                  "💸 <b>Amount:</b> <code>{commission}</code> coins\n"
                                  "📊 <b>Total:</b> <code>{balance}</code> coins",
        
        # Language settings
        "language_selection": "🌐 <b>Language Selection</b>\n\nChoose your preferred language:",
        "language_changed": "✅ Language changed to English!",
        "language_en": "🇺🇸 English",
        
        # Gift Catalog
        "gift_selected": "🎯 <b>GIFT SELECTION</b>\n\n"
                        "🎁 <b>Selected:</b> {gift_display}\n"
                        "💰 <b>Price:</b> <code>{price:,}</code> coins each\n\n"
                        "📝 <b>Enter quantity</b> to purchase:\n\n"
                        "<code>/cancel</code> - to cancel",
        "enter_quantity_error": "❌ <b>ERROR:</b> Please enter a positive whole number!",
        "enter_recipient": "👤 <b>RECIPIENT DETAILS</b>\n\n"
                          "📋 <b>Instructions:</b>\n"
                          "• <b>User ID</b> (@userinfobot for yours)\n"
                          "• <b>Channel</b> username (@channel)\n\n"
                          "<code>/cancel</code> — cancel operation",
        "invalid_recipient": "❌ <b>INVALID FORMAT:</b>\n• For users: enter ID number\n• For channels: enter @username\nPlease try again.",
        "catalog_closed": "🚫 <b>Catalog session closed.</b>",
        "catalog_outdated": "⚠️ <b>Catalog expired.</b> Please reopen the gift store.",
        "purchase_processing": "⏳ <b>PROCESSING PURCHASE...</b>\n\n🎁 Please wait while we process your gift order...",
        "purchase_success": "✅ <b>PURCHASE COMPLETED!</b>\n\n"
                           "🎁 <b>Gift:</b> {gift_display}\n"
                           "📦 <b>Quantity:</b> <code>{bought}/{qty}</code> purchased\n"
                           "👤 <b>Recipient:</b> {recipient}",
        "purchase_partial": "⚠️ <b>PURCHASE INCOMPLETE</b>\n\n"
                           "🎁 <b>Gift:</b> {gift_display}\n"
                           "📦 <b>Purchased:</b> <code>{bought}/{qty}</code> gifts\n"
                           "👤 <b>Recipient:</b> {recipient}\n\n"
                           "💰 <b>Solution:</b> Top up your balance!\n"
                           "📦 <b>Note:</b> Check gift availability!\n"
                           "🔴 <b>Status:</b> Bot paused automatically.",
        "action_cancelled": "🚫 <b>Operation cancelled.</b>",
        "back_to_menu": "⬅️ Back to Menu",
        "confirm_btn": "✅ Confirm Purchase",
        "cancel_btn": "❌ Cancel",
        "catalog_header": "🎁 <b>GIFT STORE</b>\n\n"
                         "🧸 <b>Regular:</b> <code>{unlimited}</code> available\n"
                         "💎 <b>Limited:</b> <code>{limited}</code> exclusive",
        "purchase_summary": "📋 <b>PURCHASE CONFIRMATION</b>\n\n"
                           "🎁 <b>Gift:</b> {gift_display}\n"
                           "📊 <b>Quantity:</b> <code>{qty}</code> items\n"
                           "💵 <b>Unit Price:</b> <code>{price:,}</code> coins\n"
                           "💰 <b>Total Cost:</b> <code>{total:,}</code> coins\n"
                           "👤 <b>Recipient:</b> {recipient}\n\n"
                           "🔥 <b>Ready to proceed?</b>",
        "invalid_purchase": "❌ <b>SESSION EXPIRED:</b> Please restart your purchase.",
        
        # Admin Panel
        "admin_panel": "👑 <b>OWNER CONTROL CENTER</b>\n\n"
                      "💼 <b>ANALYTICS</b>\n"
                      "💎 Commission: <code>{commission_balance:,}</code> coins\n"
                      "👥 Users: <code>{total_users:,}</code> registered\n"
                      "💰 Deposits: <code>{total_deposits:,}</code> coins\n"
                      "📊 Earnings: <code>{total_commissions:,}</code> coins\n"
                      "📈 Rate: <code>{commission_rate:.1f}%</code> active",
        
        "btn_withdraw_commission": "💸 Withdraw Commission",
        "btn_detailed_report": "📊 Analytics Report", 
        "btn_change_commission": "⚙️ Change Rate",
        "btn_manage_users": "👥 User Management",
        "btn_back": "⬅️ Back",
        "btn_main_menu": "🏠 Main Menu",
        
        "commission_withdrawn": "✅ <b>COMMISSION WITHDRAWN</b>\n\n"
                               "💰 <b>Amount:</b> <code>{amount:,}</code> coins\n"
                               "💳 <b>Status:</b> Transferred to balance\n\n"
                               "💡 <b>Tip:</b> You can now withdraw from main menu",
        
        "no_commission": "❌ <b>No commission available!</b> Wait for user deposits.",
        
        "user_report": "📊 <b>DETAILED ANALYTICS</b>\n\n"
                      "📈 <b>OVERVIEW</b>\n"
                      "👥 Active: <code>{active_users:,}</code> users\n"
                      "💰 Balance: <code>{total_balance:,}</code> coins\n"
                      "💸 Spent: <code>{total_spent:,}</code> coins\n"
                      "📊 Average: <code>{avg_balance:,}</code> coins/user",
        
        # Wizard texts
        "wizard_min_price": "💰 <b>Enter minimum gift price</b>, example: `5000`\n\n`/cancel` — cancel",
        "wizard_max_price": "💰 <b>Enter maximum gift price</b>, example: `10000`\n\n`/cancel` — cancel",
        "wizard_min_supply": "📦 <b>Enter minimum gift supply</b>, example: `1000`\n\n`/cancel` — cancel",
        "wizard_max_supply": "📦 <b>Enter maximum gift supply</b>, example: `10000`\n\n`/cancel` — cancel",
        "wizard_gift_count": "🎁 <b>Enter maximum number of gifts</b>, example: `5`\n\n`/cancel` — cancel",
        "wizard_star_limit": "💸 <b>Enter coin limit for this profile</b> (example: `10000`)\n\n`/cancel` — cancel",
        "wizard_recipient": "👤 <b>Enter gift recipient:</b>\n\n"
                           "• <b>User ID</b> (you can find your ID here @userinfobot)\n"
                           "• Or <b>channel username</b> (example: `@channel`)\n\n"
                           "❗️ Find user ID here @userinfobot\n\n"
                           "`/cancel` — cancel",
        "wizard_deposit_amount": "💰 <b>Enter deposit amount</b>, example: `5000`\n\n`/cancel` — cancel",
        "wizard_refund_id": "🆔 <b>Enter transaction ID for refund:</b>\n\n`/withdraw_all` — withdraw entire balance\n`/cancel` — cancel",
        "wizard_guest_refund_id": "🆔 <b>Enter transaction ID for refund:</b>",
        "wizard_number_error": "🚫 Please enter a positive number. Try again.",
        "wizard_range_error_max_price": "🚫 Maximum price cannot be less than minimum. Try again.",
        "wizard_range_error_max_supply": "🚫 Maximum supply cannot be less than minimum. Try again.", 
        "wizard_recipient_error": "🚫 For account recipient — enter ID, for channel — username with @. Try again.",
        "wizard_deposit_range_error": "🚫 Enter number from 1 to 10000. Try again.",
        "refund_success": "✅ Refund completed successfully.",
        "refund_error": "🚫 Refund error:\n`{error}`",
        "no_stars_found": "⚠️ No stars found for refund.",
        "withdraw_all_confirm": "⚠️ Are you sure you want to withdraw all stars?",
        "withdraw_processing": "⏳ Processing star withdrawal...",
        "action_cancelled": "🚫 Action cancelled.",
        "profile_updated": "✅ <b>Profile {index}</b> updated.",
        "profile_deleted": "✅ <b>Profile {index}</b> deleted.",
        "profile_delete_cancelled": "🚫 Deletion of <b>Profile {index}</b> cancelled.",
        "confirm_delete_profile": "⚠️ Are you sure you want to delete <b>profile {index}</b>?\n\n{profile_info}",
        "yes_btn": "✅ Yes",
        "no_btn": "❌ No",
        "gift_bot_title": "Gift Bot",
        "deposit_description": "Balance top-up"
    }
}

async def get_text(user_id: int, key: str, **kwargs) -> str:
    """Get localized text for user - ENGLISH ONLY"""
    try:
        # English only mode for professional experience
        text = TEXTS["en"].get(key, key)
        
        # Format text with provided arguments
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"Text formatting error for key '{key}': {e}")
                return text
        return text
    except Exception as e:
        logger.error(f"Localization error for user {user_id}, key '{key}': {e}")
        return TEXTS["en"].get(key, key)

def get_text_sync(language: str, key: str, **kwargs) -> str:
    """Get localized text synchronously - ENGLISH ONLY"""
    try:
        text = TEXTS["en"].get(key, key)
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"Text formatting error for key '{key}': {e}")
                return text
        return text
    except Exception as e:
        logger.error(f"Localization error for key '{key}': {e}")
        return TEXTS["en"].get(key, key)

def detect_language_from_user(user) -> str:
    """Detect language from Telegram user object - ENGLISH ONLY"""
    return 'en'

def format_number(number: int, language: str = "en") -> str:
    """Format number according to language locale - ENGLISH ONLY"""
    # English number formatting (comma as thousands separator)
    return f"{number:,}"

def get_target_display(profile: Dict, user_id: int, language: str) -> str:
    """Get formatted target display text - ENGLISH ONLY"""
    target_chat_id = profile.get("TARGET_CHAT_ID")
    target_user_id = profile.get("TARGET_USER_ID")
    
    if target_chat_id:
        return f"{target_chat_id} (Channel)"
    elif str(target_user_id) == str(user_id):
        return f"<code>{target_user_id}</code> (You)"
    else:
        return f"<code>{target_user_id}</code>" 