"""
Clean, professional admin handlers for Area 51 Bot
Demonstrates the new modular structure and proper separation of concerns
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from datetime import datetime

# Import our clean modules
from core.config import config, CallbackData
from keyboards.admin import AdminKeyboards
from utils.formatters import DashboardFormatter, UIFormatter

# Import database functions with fallback
try:
    from utils.database import get_owner_data, get_analytics, save_owner_data
except ImportError:
    from services.database import get_owner_data, get_analytics, save_owner_data

# Create router for admin handlers
admin_router = Router()

class AdminHandlers:
    """Clean admin handlers with proper separation of concerns"""
    
    @staticmethod
    @admin_router.callback_query(F.data == CallbackData.ADMIN_DASHBOARD)
    async def show_dashboard(call: CallbackQuery):
        """Display professional owner dashboard"""
        try:
            # Get data from database
            owner_data = await get_owner_data()
            analytics = await get_analytics()
            
            # Prepare dashboard data
            dashboard_data = {
                "uptime": UIFormatter.format_uptime(datetime.now()),  # This would use actual start time
                "commission_rate": owner_data.get("commission_rate", 0) * 100,
                "commission_balance": owner_data.get("commission_balance", 0),
                "total_earned": owner_data.get("total_commissions_earned", 0),
                "total_deposits": owner_data.get("total_deposits_processed", 0),
                "total_users": analytics.get("total_users", 0),
                "active_users": analytics.get("active_users", 0),
                "new_today": 0,  # Would calculate from logs
                "last_update": "Just now"
            }
            
            # Use formatter for clean display
            text = DashboardFormatter.owner_dashboard(dashboard_data)
            keyboard = AdminKeyboards.main_dashboard()
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
        except Exception as e:
            await call.answer(f"Error: {str(e)}", show_alert=True)
    
    @staticmethod
    @admin_router.callback_query(F.data == CallbackData.ADMIN_COMMISSION)
    async def show_commission_panel(call: CallbackQuery):
        """Display commission management panel"""
        try:
            owner_data = await get_owner_data()
            
            # Use formatter for consistent display
            text = DashboardFormatter.commission_panel(owner_data)
            keyboard = AdminKeyboards.commission_management()
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
        except Exception as e:
            await call.answer(f"Error: {str(e)}", show_alert=True)
    
    @staticmethod
    @admin_router.callback_query(F.data == CallbackData.ADMIN_USERS)
    async def show_user_management(call: CallbackQuery):
        """Display user management panel"""
        try:
            analytics = await get_analytics()
            
            # Add calculated fields for user management
            analytics.update({
                "blocked_users": 0,  # Would calculate from database
                "new_24h": 0,        # Would calculate from logs
                "deposits_24h": 0,   # Would calculate from logs
                "withdrawals_24h": 0 # Would calculate from logs
            })
            
            text = DashboardFormatter.user_management_panel(analytics)
            keyboard = AdminKeyboards.user_management()
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
        except Exception as e:
            await call.answer(f"Error: {str(e)}", show_alert=True)
    
    @staticmethod
    @admin_router.callback_query(F.data == CallbackData.ADMIN_WITHDRAW)
    async def withdraw_commission(call: CallbackQuery):
        """Handle commission withdrawal with confirmation"""
        try:
            owner_data = await get_owner_data()
            commission_balance = owner_data.get("commission_balance", 0)
            
            if commission_balance <= 0:
                await call.answer("No commission available to withdraw!", show_alert=True)
                return
            
            # Show confirmation dialog
            text = f"""💸 <b>Commission Withdrawal</b>

<b>Available Balance:</b> {UIFormatter.format_currency(commission_balance)} coins

Are you sure you want to withdraw all commission funds?

⚠️ <b>Note:</b> This action cannot be undone."""
            
            keyboard = AdminKeyboards.withdrawal_confirmation(commission_balance)
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
        except Exception as e:
            await call.answer(f"Error: {str(e)}", show_alert=True)
    
    @staticmethod
    @admin_router.callback_query(F.data == "confirm_withdraw_commission")
    async def confirm_withdrawal(call: CallbackQuery):
        """Confirm and process commission withdrawal"""
        try:
            owner_data = await get_owner_data()
            withdrawal_amount = owner_data.get("commission_balance", 0)
            
            if withdrawal_amount <= 0:
                await call.answer("No funds to withdraw!", show_alert=True)
                return
            
            # Process withdrawal
            owner_data["commission_balance"] = 0
            owner_data["last_withdrawal"] = datetime.now().isoformat()
            await save_owner_data(owner_data)
            
            # Success message with clean formatting
            success_text = f"""✅ <b>WITHDRAWAL SUCCESSFUL!</b>

{UIFormatter.format_section_header("TRANSACTION DETAILS")}
Amount Withdrawn: {UIFormatter.format_currency(withdrawal_amount)} coins
Transaction Time: {UIFormatter.format_time_ago(datetime.now())}
New Commission Balance: 0 coins

💡 <b>Tip:</b> Commission will accumulate again as users make deposits."""
            
            keyboard = AdminKeyboards.navigation_back("dashboard")
            
            await call.message.edit_text(success_text, reply_markup=keyboard)
            await call.answer("Withdrawal completed successfully!")
            
        except Exception as e:
            await call.answer(f"Withdrawal failed: {str(e)}", show_alert=True)
    
    @staticmethod
    @admin_router.callback_query(F.data == CallbackData.COMM_CHANGE_RATE)
    async def change_commission_rate(call: CallbackQuery):
        """Show commission rate change options"""
        try:
            owner_data = await get_owner_data()
            current_rate = owner_data.get("commission_rate", 0) * 100
            
            text = f"""📈 <b>Change Commission Rate</b>

<b>Current Rate:</b> {UIFormatter.format_percentage(current_rate)}

Select a new commission rate:

⚠️ <b>Note:</b> Changes affect future deposits only."""
            
            keyboard = AdminKeyboards.rate_change_options()
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer()
            
        except Exception as e:
            await call.answer(f"Error: {str(e)}", show_alert=True)
    
    @staticmethod
    @admin_router.callback_query(F.data.startswith("set_rate_"))
    async def set_commission_rate(call: CallbackQuery):
        """Set new commission rate"""
        try:
            # Extract rate from callback data
            rate_str = call.data.split("_")[-1]
            
            if rate_str == "custom":
                # Would trigger FSM for custom rate input
                await call.answer("Custom rate input would be implemented here")
                return
            
            new_rate = float(rate_str) / 100
            
            # Validate rate
            if not config.validate_commission_rate(new_rate):
                await call.answer(
                    f"Rate must be between {config.MIN_COMMISSION_RATE*100}% and {config.MAX_COMMISSION_RATE*100}%", 
                    show_alert=True
                )
                return
            
            # Update rate
            owner_data = await get_owner_data()
            old_rate = owner_data.get("commission_rate", 0) * 100
            owner_data["commission_rate"] = new_rate
            await save_owner_data(owner_data)
            
            # Success message
            success_text = f"""✅ <b>COMMISSION RATE UPDATED!</b>

<b>Previous Rate:</b> {UIFormatter.format_percentage(old_rate)}
<b>New Rate:</b> {UIFormatter.format_percentage(new_rate * 100)}

The new rate will apply to all future deposits."""
            
            keyboard = AdminKeyboards.navigation_back("commission")
            
            await call.message.edit_text(success_text, reply_markup=keyboard)
            await call.answer("Commission rate updated successfully!")
            
        except Exception as e:
            await call.answer(f"Failed to update rate: {str(e)}", show_alert=True)
    
    @staticmethod
    @admin_router.callback_query(F.data == CallbackData.ADMIN_REFRESH)
    async def refresh_dashboard(call: CallbackQuery):
        """Refresh dashboard data"""
        await call.answer("Refreshing data...")
        await AdminHandlers.show_dashboard(call)

# Register all handlers
def register_admin_handlers(dp):
    """Register admin handlers with the dispatcher"""
    dp.include_router(admin_router) 