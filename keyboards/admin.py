"""
Professional admin keyboards for Area 51 Bot
Clean, organized layouts with human-friendly button text
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.config import CallbackData, UIConstants

class AdminKeyboards:
    """Professional admin panel keyboards"""
    
    @staticmethod
    def main_dashboard() -> InlineKeyboardMarkup:
        """Main owner control panel with organized sections"""
        return InlineKeyboardMarkup(inline_keyboard=[
            # Financial Management Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.COMMISSION} Commission Settings", 
                    callback_data=CallbackData.ADMIN_COMMISSION
                ),
                InlineKeyboardButton(
                    text=f"{UIConstants.REPORTS} Financial Report", 
                    callback_data="admin_finance_report"
                )
            ],
            # User Management Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.USERS} User Management", 
                    callback_data=CallbackData.ADMIN_USERS
                ),
                InlineKeyboardButton(
                    text="🚫 Blocked Users", 
                    callback_data="admin_blocked_users"
                )
            ],
            # System Operations Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.SETTINGS} System Settings", 
                    callback_data=CallbackData.ADMIN_SETTINGS
                ),
                InlineKeyboardButton(
                    text="📋 Activity Logs", 
                    callback_data=CallbackData.ADMIN_LOGS
                )
            ],
            # Quick Actions Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.COMMISSION} Withdraw Commission", 
                    callback_data=CallbackData.ADMIN_WITHDRAW
                ),
                InlineKeyboardButton(
                    text="🔄 Refresh Data", 
                    callback_data=CallbackData.ADMIN_REFRESH
                )
            ]
        ])
    
    @staticmethod
    def commission_management() -> InlineKeyboardMarkup:
        """Commission settings management panel"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📈 Change Rate", 
                    callback_data=CallbackData.COMM_CHANGE_RATE
                ),
                InlineKeyboardButton(
                    text="📊 View History", 
                    callback_data=CallbackData.COMM_HISTORY
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.COMMISSION} Withdraw Balance", 
                    callback_data=CallbackData.COMM_WITHDRAW
                ),
                InlineKeyboardButton(
                    text="📄 Export Report", 
                    callback_data=CallbackData.COMM_EXPORT
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Dashboard", 
                    callback_data=CallbackData.ADMIN_DASHBOARD
                )
            ]
        ])
    
    @staticmethod
    def user_management() -> InlineKeyboardMarkup:
        """User management operations"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👀 View All Users", 
                    callback_data="admin_view_users"
                ),
                InlineKeyboardButton(
                    text="🔍 Search User", 
                    callback_data="admin_search_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Block User", 
                    callback_data="admin_block_user"
                ),
                InlineKeyboardButton(
                    text="✅ Unblock User", 
                    callback_data="admin_unblock_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 User Analytics", 
                    callback_data="admin_user_analytics"
                ),
                InlineKeyboardButton(
                    text="📥 Export Users", 
                    callback_data="admin_export_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Dashboard", 
                    callback_data=CallbackData.ADMIN_DASHBOARD
                )
            ]
        ])
    
    @staticmethod
    def system_settings() -> InlineKeyboardMarkup:
        """System configuration options"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💸 Commission Rate", 
                    callback_data="settings_commission_rate"
                ),
                InlineKeyboardButton(
                    text="💰 Payment Limits", 
                    callback_data="settings_payment_limits"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔐 Security Settings", 
                    callback_data="settings_security"
                ),
                InlineKeyboardButton(
                    text="📱 Bot Preferences", 
                    callback_data="settings_bot_prefs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗃️ Backup Data", 
                    callback_data="settings_backup"
                ),
                InlineKeyboardButton(
                    text="🔄 Reset System", 
                    callback_data="settings_reset"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Dashboard", 
                    callback_data=CallbackData.ADMIN_DASHBOARD
                )
            ]
        ])
    
    @staticmethod
    def confirmation_dialog(action: str, confirm_data: str, cancel_data: str = None) -> InlineKeyboardMarkup:
        """Generic confirmation dialog for dangerous actions"""
        cancel_callback = cancel_data or CallbackData.ADMIN_DASHBOARD
        
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, Continue", 
                    callback_data=confirm_data
                ),
                InlineKeyboardButton(
                    text="❌ Cancel", 
                    callback_data=cancel_callback
                )
            ]
        ])
    
    @staticmethod
    def withdrawal_confirmation(amount: int) -> InlineKeyboardMarkup:
        """Specific confirmation for commission withdrawal"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Withdraw {amount:,} coins", 
                    callback_data="confirm_withdraw_commission"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Cancel", 
                    callback_data=CallbackData.ADMIN_COMMISSION
                )
            ]
        ])
    
    @staticmethod
    def rate_change_options() -> InlineKeyboardMarkup:
        """Quick commission rate change options"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="5%", callback_data="set_rate_5"),
                InlineKeyboardButton(text="10%", callback_data="set_rate_10"),
                InlineKeyboardButton(text="15%", callback_data="set_rate_15")
            ],
            [
                InlineKeyboardButton(text="20%", callback_data="set_rate_20"),
                InlineKeyboardButton(text="25%", callback_data="set_rate_25"),
                InlineKeyboardButton(text="Custom", callback_data="set_rate_custom")
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back", 
                    callback_data=CallbackData.ADMIN_COMMISSION
                )
            ]
        ])
    
    @staticmethod
    def navigation_back(target: str) -> InlineKeyboardMarkup:
        """Simple back navigation button"""
        callback_map = {
            "dashboard": CallbackData.ADMIN_DASHBOARD,
            "commission": CallbackData.ADMIN_COMMISSION,
            "users": CallbackData.ADMIN_USERS,
            "settings": CallbackData.ADMIN_SETTINGS
        }
        
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Back", 
                    callback_data=callback_map.get(target, CallbackData.ADMIN_DASHBOARD)
                )
            ]
        ]) 