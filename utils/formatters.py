"""
Professional UI formatting utilities for Area 51 Bot
Provides consistent, clean formatting across all bot interfaces
"""
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from core.config import config, UIConstants

class UIFormatter:
    """Professional UI formatting utilities"""
    
    @staticmethod
    def format_currency(amount: Union[int, float]) -> str:
        """Format currency with proper separators"""
        return f"{amount:,}"
    
    @staticmethod
    def format_percentage(rate: float) -> str:
        """Format percentage properly"""
        return f"{rate:.1f}%"
    
    @staticmethod
    def format_status(is_active: bool) -> str:
        """Format status with appropriate emoji and text"""
        return f"{UIConstants.STATUS_ONLINE} ACTIVE" if is_active else f"{UIConstants.STATUS_OFFLINE} INACTIVE"
    
    @staticmethod
    def format_uptime(start_time: datetime) -> str:
        """Format uptime in human-readable format"""
        delta = datetime.now() - start_time
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m"
    
    @staticmethod
    def format_time_ago(timestamp: datetime) -> str:
        """Format time as 'X minutes/hours/days ago'"""
        delta = datetime.now() - timestamp
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    @staticmethod
    def format_section_header(title: str, emoji: str = "") -> str:
        """Create consistent section headers"""
        if emoji:
            return f"<b>{emoji} {title.upper()}</b>"
        return f"<b>{UIConstants.SECTION_SEP} {title.upper()} {UIConstants.SECTION_SEP}</b>"
    
    @staticmethod
    def format_profile_card(profile: Dict, index: int, user_id: int) -> str:
        """Format a single profile card with clean layout"""
        status_emoji = UIConstants.STATUS_COMPLETED if profile.get("DONE", False) else UIConstants.STATUS_PENDING
        status_text = "COMPLETED" if profile.get("DONE", False) else "ACTIVE"
        progress = f"{profile.get('BOUGHT', 0)}/{profile.get('COUNT', 0)}"
        target_display = UIFormatter._format_target(profile.get('TARGET_USER_ID'), user_id)
        
        return f"""<b>{UIConstants.PROFILE} Profile #{index + 1}</b>

<b>Status:</b> {status_emoji} {status_text}
<b>Progress:</b> {progress} gifts completed
<b>Price Range:</b> {UIFormatter.format_currency(profile.get('MIN_PRICE', 0))} - {UIFormatter.format_currency(profile.get('MAX_PRICE', 0))} coins
<b>Supply Range:</b> {UIFormatter.format_currency(profile.get('MIN_SUPPLY', 0))} - {UIFormatter.format_currency(profile.get('MAX_SUPPLY', 0))} available
<b>Budget:</b> {UIFormatter.format_currency(profile.get('SPENT', 0))} / {UIFormatter.format_currency(profile.get('LIMIT', 0))} coins
<b>Target:</b> {target_display}"""
    
    @staticmethod
    def _format_target(target_id: Optional[int], current_user_id: int) -> str:
        """Format target user display"""
        if not target_id:
            return "Not set"
        if target_id == current_user_id:
            return f"<code>{target_id}</code> (You)"
        return f"<code>{target_id}</code>"
    
    @staticmethod
    def format_transaction_success(deposit_amount: int, fee: int, final_balance: int) -> str:
        """Format transaction success message"""
        net_amount = deposit_amount - fee
        fee_percent = (fee / deposit_amount) * 100 if deposit_amount > 0 else 0
        
        return f"""✅ <b>DEPOSIT SUCCESSFUL!</b>

{UIConstants.MONEY} <b>Deposited:</b> {UIFormatter.format_currency(net_amount)} coins
{UIConstants.COMMISSION} <b>Fee ({UIFormatter.format_percentage(fee_percent)}):</b> {UIFormatter.format_currency(fee)} coins
{UIConstants.REPORTS} <b>New Balance:</b> {UIFormatter.format_currency(final_balance)} coins

🙏 <b>Thank you for using {config.BOT_NAME}!</b>"""
    
    @staticmethod
    def format_withdrawal_success(amount: int, new_balance: int) -> str:
        """Format withdrawal success message"""
        return f"""✅ <b>WITHDRAWAL SUCCESSFUL!</b>

{UIConstants.COMMISSION} <b>Stars Returned:</b> Full amount
{UIConstants.MONEY} <b>Balance Deducted:</b> {UIFormatter.format_currency(amount)} coins
{UIConstants.REPORTS} <b>New Balance:</b> {UIFormatter.format_currency(new_balance)} coins

🙏 <b>Thank you for using {config.BOT_NAME}!</b>"""

class DashboardFormatter:
    """Specialized formatters for dashboard displays"""
    
    @staticmethod
    def owner_dashboard(data: Dict) -> str:
        """Format professional owner dashboard"""
        return f"""{config.BOT_EMOJI} <b>{config.BOT_NAME} Control Center</b>

{UIFormatter.format_section_header("SYSTEM STATUS", UIConstants.REPORTS)}
Status: {UIConstants.STATUS_ONLINE} ONLINE
Version: v{config.BOT_VERSION}
Uptime: {data.get('uptime', 'Unknown')}

{UIFormatter.format_section_header("FINANCIAL OVERVIEW", UIConstants.MONEY)}
Commission Rate: {UIFormatter.format_percentage(data.get('commission_rate', 0))}
Commission Balance: {UIFormatter.format_currency(data.get('commission_balance', 0))} coins
Total Earned: {UIFormatter.format_currency(data.get('total_earned', 0))} coins
Processed Deposits: {UIFormatter.format_currency(data.get('total_deposits', 0))} coins

{UIFormatter.format_section_header("USER ANALYTICS", UIConstants.USERS)}
Total Users: {UIFormatter.format_currency(data.get('total_users', 0))}
Active Users: {UIFormatter.format_currency(data.get('active_users', 0))}
New Today: {UIFormatter.format_currency(data.get('new_today', 0))}

{UIFormatter.format_section_header("QUICK ACCESS")}
Last Update: {data.get('last_update', 'Just now')}"""
    
    @staticmethod
    def user_dashboard(user_data: Dict, profiles: List[Dict]) -> str:
        """Format clean user dashboard"""
        status = UIFormatter.format_status(user_data.get("active", False))
        active_profiles = len([p for p in profiles if not p.get("DONE", False)])
        
        return f"""{config.BOT_EMOJI} <b>{config.BOT_NAME} v{config.BOT_VERSION}</b>

{UIFormatter.format_section_header("USER PANEL", "⚡")}
{UIConstants.MONEY} <b>Balance:</b> {UIFormatter.format_currency(user_data.get('balance', 0))} coins
{UIConstants.PROFILE} <b>Profiles:</b> {active_profiles} active
{UIFormatter.format_section_header("")}
{UIConstants.REPORTS} <b>Status:</b> {status}"""
    
    @staticmethod
    def commission_panel(owner_data: Dict) -> str:
        """Format commission management panel"""
        return f"""{UIConstants.COMMISSION} <b>Commission Management</b>

{UIFormatter.format_section_header("CURRENT SETTINGS")}
Rate: {UIFormatter.format_percentage(owner_data.get('commission_rate', 0) * 100)}
Balance: {UIFormatter.format_currency(owner_data.get('commission_balance', 0))} coins
Total Earned: {UIFormatter.format_currency(owner_data.get('total_commissions_earned', 0))} coins

{UIFormatter.format_section_header("AVAILABLE ACTIONS")}
• Change commission rate (1% - 25%)
• View detailed commission history
• Export financial reports
• Withdraw commission balance"""
    
    @staticmethod
    def user_management_panel(analytics: Dict) -> str:
        """Format user management panel"""
        return f"""{UIConstants.USERS} <b>User Management</b>

{UIFormatter.format_section_header("OVERVIEW")}
Total Users: {UIFormatter.format_currency(analytics.get('total_users', 0))}
Active Users: {UIFormatter.format_currency(analytics.get('active_users', 0))}
Blocked Users: {UIFormatter.format_currency(analytics.get('blocked_users', 0))}

{UIFormatter.format_section_header("RECENT ACTIVITY")}
New Registrations (24h): {UIFormatter.format_currency(analytics.get('new_24h', 0))}
Recent Deposits (24h): {UIFormatter.format_currency(analytics.get('deposits_24h', 0))}
Recent Withdrawals (24h): {UIFormatter.format_currency(analytics.get('withdrawals_24h', 0))}""" 