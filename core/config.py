"""
Centralized configuration for Area 51 Bot
Professional configuration management with environment variable support
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class BotConfig:
    """Main bot configuration with all settings centralized"""
    
    # Bot Identity
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    OWNER_ID: int = int(os.getenv("TELEGRAM_USER_ID", "0"))
    BOT_NAME: str = "Area 51"
    BOT_VERSION: str = "2.1.0"
    BOT_EMOJI: str = "🛸"
    
    # Commission Settings
    DEFAULT_COMMISSION_RATE: float = 0.10  # 10%
    MIN_COMMISSION_RATE: float = 0.01      # 1%
    MAX_COMMISSION_RATE: float = 0.25      # 25%
    
    # Payment Settings
    MIN_DEPOSIT: int = 1
    MAX_DEPOSIT: int = 10000
    CURRENCY: str = "XTR"
    
    # File Paths
    USER_DATA_DIR: str = "data/users"
    LOGS_DIR: str = "data/logs"
    OWNER_DATA_FILE: str = "data/owner_data.json"
    
    # UI Settings
    MAX_PROFILES_PER_USER: int = 10
    PAGINATION_SIZE: int = 5
    
    # Security Settings
    RATE_LIMIT_REQUESTS: int = 30  # per minute
    SESSION_TIMEOUT: int = 3600    # seconds
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not self.OWNER_ID:
            raise ValueError("OWNER_ID is required")
    
    @property
    def commission_rate_percent(self) -> float:
        """Get commission rate as percentage"""
        return self.DEFAULT_COMMISSION_RATE * 100
    
    def validate_commission_rate(self, rate: float) -> bool:
        """Validate if commission rate is within allowed range"""
        return self.MIN_COMMISSION_RATE <= rate <= self.MAX_COMMISSION_RATE

# Global configuration instance
config = BotConfig()

# Callback data constants for clean separation
class CallbackData:
    """Centralized callback data constants"""
    
    # Admin callbacks
    ADMIN_DASHBOARD = "admin_dashboard"
    ADMIN_COMMISSION = "admin_commission"
    ADMIN_USERS = "admin_users"
    ADMIN_SETTINGS = "admin_settings"
    ADMIN_LOGS = "admin_logs"
    ADMIN_WITHDRAW = "admin_withdraw"
    ADMIN_REFRESH = "admin_refresh"
    
    # Commission management
    COMM_CHANGE_RATE = "comm_change_rate"
    COMM_HISTORY = "comm_history"
    COMM_WITHDRAW = "comm_withdraw"
    COMM_EXPORT = "comm_export"
    
    # User callbacks
    USER_DEPOSIT = "user_deposit"
    USER_WITHDRAW = "user_withdraw"
    USER_PROFILES = "user_profiles"
    USER_ADD_PROFILE = "user_add_profile"
    USER_STORE = "user_store"
    USER_ORDERS = "user_orders"
    USER_SETTINGS = "user_settings"
    USER_HELP = "user_help"
    
    # Profile management
    PROFILE_EDIT = "profile_edit"
    PROFILE_DELETE = "profile_delete"
    PROFILE_ACTIVATE = "profile_activate"
    PROFILE_DEACTIVATE = "profile_deactivate"
    
    # Navigation
    BACK_TO_MAIN = "back_to_main"
    BACK_TO_ADMIN = "back_to_admin"
    CANCEL = "cancel"
    CONFIRM = "confirm"

# UI Constants
class UIConstants:
    """UI formatting constants"""
    
    # Emojis with purpose
    STATUS_ONLINE = "🟢"
    STATUS_OFFLINE = "🔴"
    STATUS_PENDING = "🟡"
    STATUS_COMPLETED = "✅"
    
    MONEY = "💰"
    COMMISSION = "💸"
    USERS = "👥"
    SETTINGS = "⚙️"
    REPORTS = "📊"
    PROFILE = "👤"
    GIFT = "🎁"
    STORE = "🏪"
    ORDERS = "📦"
    
    # Section separators
    SECTION_SEP = "─" * 3
    BOX_TOP = "┌" + "─" * 35 + "┐"
    BOX_MID = "├" + "─" * 35 + "┤"
    BOX_BOT = "└" + "─" * 35 + "┘" 