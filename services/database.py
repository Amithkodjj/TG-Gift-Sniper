import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List
import aiofiles

logger = logging.getLogger(__name__)

# Get optional environment variables - FIXED TO 10%
DEFAULT_COMMISSION_RATE = float(os.getenv("COMMISSION_RATE", "0.10"))  # 10% default

# Default user profile structure
DEFAULT_USER_PROFILE = {
    "MIN_PRICE": 5000,
    "MAX_PRICE": 10000,
    "MIN_SUPPLY": 1000,
    "MAX_SUPPLY": 10000,
    "LIMIT": 1000000,
    "COUNT": 5,
    "TARGET_USER_ID": None,
    "TARGET_CHAT_ID": None,
    "BOUGHT": 0,
    "SPENT": 0,
    "DONE": False
}

async def ensure_directories():
    """Ensure required directories exist with proper Linux permissions"""
    os.makedirs("users", mode=0o755, exist_ok=True)
    os.makedirs("logs", mode=0o755, exist_ok=True)

async def get_user_data(user_id: int) -> Dict:
    """Get user data, create if doesn't exist"""
    await ensure_directories()
    
    try:
        async with aiofiles.open(f"users/{user_id}.json", "r", encoding="utf-8") as f:
            data = json.loads(await f.read())
            # Update last_active
            data["last_active"] = datetime.now().isoformat()
            await save_user_data(user_id, data)
            return data
    except FileNotFoundError:
        # Create new user
        default_profile = DEFAULT_USER_PROFILE.copy()
        default_profile["TARGET_USER_ID"] = user_id
        
        default_data = {
            "user_id": user_id,
            "balance": 0,
            "total_deposited": 0,
            "total_spent": 0,
            "language": "en",  # Default language - English
            "profiles": [default_profile],
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "is_blocked": False,
            "total_purchases": 0
        }
        await save_user_data(user_id, default_data)
        logger.info(f"Created new user: {user_id}")
        return default_data

async def save_user_data(user_id: int, data: Dict):
    """Save user data to file"""
    await ensure_directories()
    async with aiofiles.open(f"users/{user_id}.json", "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))

async def get_owner_data() -> Dict:
    """Get owner commission data"""
    try:
        async with aiofiles.open("owner_data.json", "r", encoding="utf-8") as f:
            return json.loads(await f.read())
    except FileNotFoundError:
        # Get owner ID from environment
        owner_id = int(os.getenv("TELEGRAM_USER_ID"))
        default_data = {
            "owner_id": owner_id,
            "commission_balance": 0,
            "total_commissions_earned": 0,
            "total_users": 0,
            "total_deposits_processed": 0,
            "last_withdrawal": None,
            "commission_rate": DEFAULT_COMMISSION_RATE,  # From environment or 10% default
            "stars_balance": 0,  # For main bot balance
            "created_at": datetime.now().isoformat()
        }
        await save_owner_data(default_data)
        return default_data

async def save_owner_data(data: Dict):
    """Save owner data"""
    async with aiofiles.open("owner_data.json", "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))

async def add_commission(amount: int, user_id: int) -> int:
    """Add commission to owner balance"""
    owner_data = await get_owner_data()
    owner_data["commission_balance"] += amount
    owner_data["total_commissions_earned"] += amount
    owner_data["total_deposits_processed"] += amount / owner_data["commission_rate"]
    
    # Log the commission
    await log_transaction("commission", {
        "amount": amount,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "commission_rate": owner_data["commission_rate"]
    })
    
    await save_owner_data(owner_data)
    return owner_data["commission_balance"]

async def withdraw_commission(amount: int) -> bool:
    """Withdraw commission from owner balance"""
    owner_data = await get_owner_data()
    if owner_data["commission_balance"] >= amount:
        owner_data["commission_balance"] -= amount
        owner_data["last_withdrawal"] = datetime.now().isoformat()
        
        # Log the withdrawal
        await log_transaction("commission_withdrawal", {
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        })
        
        await save_owner_data(owner_data)
        return True
    return False

async def update_user_balance(user_id: int, amount: int) -> int:
    """Update user balance and return new balance"""
    user_data = await get_user_data(user_id)
    old_balance = user_data["balance"]
    user_data["balance"] = max(0, user_data["balance"] + amount)
    if amount > 0:
        user_data["total_deposited"] += amount
    else:
        user_data["total_spent"] += abs(amount)
    await save_user_data(user_id, user_data)
    
    # DEBUG: Log only withdrawals (negative amounts) for debugging
    if amount < 0:
        print(f"🔍 DEBUG - Withdrawal balance update for user {user_id}:")
        print(f"   Old balance: {old_balance}")
        print(f"   Amount change: {amount}")
        print(f"   New balance: {user_data['balance']}")
        print(f"   Saved to file: users/{user_id}.json")
    
    return user_data["balance"]

async def get_fresh_balance(user_id: int) -> int:
    """Get fresh balance from file storage (no caching)"""
    fresh_user_data = await get_user_data(user_id)
    return fresh_user_data.get("balance", 0)

async def withdraw_admin_stars(amount: int) -> bool:
    """
    سحب النجوم المخصصة للأدمن من المبلغ القابل للسحب
    """
    owner_data = await get_owner_data()
    admin_withdrawable = owner_data.get("admin_withdrawable_stars", 0)
    
    if amount <= 0 or amount > admin_withdrawable:
        return False
    
    # خصم المبلغ من النجوم القابلة للسحب
    owner_data["admin_withdrawable_stars"] = admin_withdrawable - amount
    
    # إضافة المبلغ إلى رصيد النجوم الرئيسي للأدمن
    owner_data["stars_balance"] = owner_data.get("stars_balance", 0) + amount
    
    # تسجيل آخر عملية سحب
    owner_data["last_withdrawal"] = datetime.now().isoformat()
    
    # تسجيل المعاملة
    await log_transaction("admin_stars_withdrawal", {
        "amount": amount,
        "timestamp": datetime.now().isoformat(),
        "remaining_withdrawable": owner_data["admin_withdrawable_stars"]
    })
    
    await save_owner_data(owner_data)
    return True

async def get_admin_spending_stats() -> dict:
    """
    الحصول على إحصائيات إنفاق النجوم والمبلغ القابل للسحب للأدمن
    """
    owner_data = await get_owner_data()
    return {
        "total_stars_spent_on_gifts": owner_data.get("total_stars_spent_on_gifts", 0),
        "admin_withdrawable_stars": owner_data.get("admin_withdrawable_stars", 0),
        "total_gifts_purchased": owner_data.get("total_gifts_purchased", 0),
        "last_gift_purchase": owner_data.get("last_gift_purchase"),
        "withdrawal_percentage": 10.0  # ثابت 10%
    }

async def get_user_language(user_id: int) -> str:
    """Get user's preferred language"""
    user_data = await get_user_data(user_id)
    return user_data.get("language", "en")

async def set_user_language(user_id: int, language: str):
    """Set user's preferred language"""
    user_data = await get_user_data(user_id)
    user_data["language"] = language
    await save_user_data(user_id, user_data)

async def get_all_users() -> List[Dict]:
    """Get all users data for admin panel"""
    await ensure_directories()
    users = []
    
    if os.path.exists("users"):
        for filename in os.listdir("users"):
            if filename.endswith(".json"):
                user_id = int(filename.replace(".json", ""))
                user_data = await get_user_data(user_id)
                users.append(user_data)
    
    return users

async def get_analytics() -> Dict:
    """Get system analytics"""
    users = await get_all_users()
    owner_data = await get_owner_data()
    
    total_users = len(users)
    active_users = len([u for u in users if u.get("total_purchases", 0) > 0])
    total_balance = sum(u.get("balance", 0) for u in users)
    total_spent = sum(u.get("total_spent", 0) for u in users)
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_balance": total_balance,
        "total_spent": total_spent,
        "commission_balance": owner_data["commission_balance"],
        "total_commissions": owner_data["total_commissions_earned"],
        "commission_rate": owner_data["commission_rate"]
    }

async def block_user(user_id: int) -> bool:
    """Block a user"""
    try:
        user_data = await get_user_data(user_id)
        user_data["is_blocked"] = True
        await save_user_data(user_id, user_data)
        return True
    except:
        return False

async def unblock_user(user_id: int) -> bool:
    """Unblock a user"""
    try:
        user_data = await get_user_data(user_id)
        user_data["is_blocked"] = False
        await save_user_data(user_id, user_data)
        return True
    except:
        return False

async def is_user_blocked(user_id: int) -> bool:
    """Check if user is blocked"""
    try:
        user_data = await get_user_data(user_id)
        return user_data.get("is_blocked", False)
    except:
        return False

async def log_transaction(transaction_type: str, data: Dict):
    """Log transaction for audit trail"""
    await ensure_directories()
    
    log_entry = {
        "type": transaction_type,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    # Write to daily log file
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiofiles.open(f"logs/transactions_{today}.json", "a", encoding="utf-8") as f:
        await f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

async def migrate_from_single_user(old_config_path: str = "config.json", owner_id: int = None):
    """Migrate from single-user config to multi-user database"""
    if not os.path.exists(old_config_path) or not owner_id:
        return False
    
    try:
        with open(old_config_path, "r", encoding="utf-8") as f:
            old_config = json.load(f)
        
        # Create user data from old config
        user_data = {
            "user_id": owner_id,
            "balance": old_config.get("BALANCE", 0),
            "total_deposited": old_config.get("BALANCE", 0),
            "total_spent": 0,
            "language": "en",  # Default to English for migrated users
            "profiles": old_config.get("PROFILES", []),
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "is_blocked": False,
            "total_purchases": 0
        }
        
        await save_user_data(owner_id, user_data)
        
        # Backup old config
        os.rename(old_config_path, f"{old_config_path}.backup")
        
        logger.info(f"Successfully migrated single-user config to multi-user for user {owner_id}")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False 