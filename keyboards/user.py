"""
Professional user keyboards for Area 51 Bot
Clean, intuitive layouts for regular users
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Optional
from core.config import CallbackData, UIConstants

class UserKeyboards:
    """Professional user panel keyboards"""
    
    @staticmethod
    def main_panel() -> InlineKeyboardMarkup:
        """Main user panel with logical grouping"""
        return InlineKeyboardMarkup(inline_keyboard=[
            # Account Management Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.MONEY} Deposit Funds", 
                    callback_data=CallbackData.USER_DEPOSIT
                ),
                InlineKeyboardButton(
                    text=f"{UIConstants.COMMISSION} Withdraw", 
                    callback_data=CallbackData.USER_WITHDRAW
                )
            ],
            # Profile Management Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.PROFILE} My Profiles", 
                    callback_data=CallbackData.USER_PROFILES
                ),
                InlineKeyboardButton(
                    text="➕ Add Profile", 
                    callback_data=CallbackData.USER_ADD_PROFILE
                )
            ],
            # Shopping Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.STORE} Gift Store", 
                    callback_data=CallbackData.USER_STORE
                ),
                InlineKeyboardButton(
                    text=f"{UIConstants.ORDERS} My Orders", 
                    callback_data=CallbackData.USER_ORDERS
                )
            ],
            # Settings & Help Section
            [
                InlineKeyboardButton(
                    text=f"{UIConstants.SETTINGS} Settings", 
                    callback_data=CallbackData.USER_SETTINGS
                ),
                InlineKeyboardButton(
                    text="ℹ️ Help & Support", 
                    callback_data=CallbackData.USER_HELP
                )
            ]
        ])
    
    @staticmethod
    def profile_management(profiles: List[Dict]) -> InlineKeyboardMarkup:
        """Dynamic profile management keyboard"""
        keyboard = []
        
        # Add profile buttons (max 5 per row, then wrap)
        for i, profile in enumerate(profiles[:10]):  # Limit to 10 profiles
            status_emoji = "✅" if profile.get("DONE", False) else "🟡"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status_emoji} Profile {i + 1}", 
                    callback_data=f"view_profile_{i}"
                )
            ])
        
        # Add management options
        keyboard.extend([
            [
                InlineKeyboardButton(
                    text="➕ Add New Profile", 
                    callback_data=CallbackData.USER_ADD_PROFILE
                ),
                InlineKeyboardButton(
                    text="📊 Profile Stats", 
                    callback_data="profile_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Main", 
                    callback_data=CallbackData.BACK_TO_MAIN
                )
            ]
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def profile_detail(profile_index: int, is_active: bool = True) -> InlineKeyboardMarkup:
        """Individual profile management options"""
        keyboard = []
        
        if is_active:
            keyboard.extend([
                [
                    InlineKeyboardButton(
                        text="✏️ Edit Profile", 
                        callback_data=f"edit_profile_{profile_index}"
                    ),
                    InlineKeyboardButton(
                        text="⏸️ Pause Profile", 
                        callback_data=f"pause_profile_{profile_index}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑️ Delete Profile", 
                        callback_data=f"delete_profile_{profile_index}"
                    ),
                    InlineKeyboardButton(
                        text="📊 View Progress", 
                        callback_data=f"progress_profile_{profile_index}"
                    )
                ]
            ])
        else:
            keyboard.extend([
                [
                    InlineKeyboardButton(
                        text="▶️ Resume Profile", 
                        callback_data=f"resume_profile_{profile_index}"
                    ),
                    InlineKeyboardButton(
                        text="✏️ Edit Profile", 
                        callback_data=f"edit_profile_{profile_index}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑️ Delete Profile", 
                        callback_data=f"delete_profile_{profile_index}"
                    )
                ]
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 Back to Profiles", 
                callback_data=CallbackData.USER_PROFILES
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def deposit_options() -> InlineKeyboardMarkup:
        """Deposit amount quick select"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="100 ⭐", callback_data="deposit_100"),
                InlineKeyboardButton(text="500 ⭐", callback_data="deposit_500"),
                InlineKeyboardButton(text="1000 ⭐", callback_data="deposit_1000")
            ],
            [
                InlineKeyboardButton(text="2500 ⭐", callback_data="deposit_2500"),
                InlineKeyboardButton(text="5000 ⭐", callback_data="deposit_5000"),
                InlineKeyboardButton(text="Custom", callback_data="deposit_custom")
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Main", 
                    callback_data=CallbackData.BACK_TO_MAIN
                )
            ]
        ])
    
    @staticmethod
    def withdrawal_options() -> InlineKeyboardMarkup:
        """Withdrawal options with different methods"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💸 Withdraw by Transaction ID", 
                    callback_data="withdraw_by_txn"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Withdraw All Balance", 
                    callback_data="withdraw_all_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Transaction History", 
                    callback_data="withdrawal_history"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Main", 
                    callback_data=CallbackData.BACK_TO_MAIN
                )
            ]
        ])
    
    @staticmethod
    def gift_store_categories() -> InlineKeyboardMarkup:
        """Gift store with categorized browsing"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Popular Gifts", 
                    callback_data="store_popular"
                ),
                InlineKeyboardButton(
                    text="⭐ Premium Gifts", 
                    callback_data="store_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Rare Gifts", 
                    callback_data="store_rare"
                ),
                InlineKeyboardButton(
                    text="🆕 New Arrivals", 
                    callback_data="store_new"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Search Gifts", 
                    callback_data="store_search"
                ),
                InlineKeyboardButton(
                    text="🛒 Auto Purchase", 
                    callback_data="store_auto"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Main", 
                    callback_data=CallbackData.BACK_TO_MAIN
                )
            ]
        ])
    
    @staticmethod
    def settings_panel() -> InlineKeyboardMarkup:
        """User settings and preferences"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Language", 
                    callback_data="settings_language"
                ),
                InlineKeyboardButton(
                    text="🔔 Notifications", 
                    callback_data="settings_notifications"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔐 Privacy", 
                    callback_data="settings_privacy"
                ),
                InlineKeyboardButton(
                    text="📊 Account Info", 
                    callback_data="settings_account"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💾 Export Data", 
                    callback_data="settings_export"
                ),
                InlineKeyboardButton(
                    text="🗑️ Delete Account", 
                    callback_data="settings_delete"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Main", 
                    callback_data=CallbackData.BACK_TO_MAIN
                )
            ]
        ])
    
    @staticmethod
    def confirmation_dialog(action: str, confirm_data: str, cancel_data: str = None) -> InlineKeyboardMarkup:
        """Generic confirmation dialog"""
        cancel_callback = cancel_data or CallbackData.BACK_TO_MAIN
        
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, Confirm", 
                    callback_data=confirm_data
                ),
                InlineKeyboardButton(
                    text="❌ Cancel", 
                    callback_data=cancel_callback
                )
            ]
        ])
    
    @staticmethod
    def pagination(current_page: int, total_pages: int, base_callback: str) -> InlineKeyboardMarkup:
        """Pagination controls for long lists"""
        keyboard = []
        
        if total_pages > 1:
            nav_buttons = []
            
            # Previous page
            if current_page > 1:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="⬅️ Previous", 
                        callback_data=f"{base_callback}_page_{current_page - 1}"
                    )
                )
            
            # Page indicator
            nav_buttons.append(
                InlineKeyboardButton(
                    text=f"📄 {current_page}/{total_pages}", 
                    callback_data="page_info"
                )
            )
            
            # Next page
            if current_page < total_pages:
                nav_buttons.append(
                    InlineKeyboardButton(
                        text="Next ➡️", 
                        callback_data=f"{base_callback}_page_{current_page + 1}"
                    )
                )
            
            keyboard.append(nav_buttons)
        
        # Back button
        keyboard.append([
            InlineKeyboardButton(
                text="🔙 Back", 
                callback_data=CallbackData.BACK_TO_MAIN
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard) 