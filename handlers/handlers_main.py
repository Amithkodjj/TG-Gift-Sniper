#!/usr/bin/env python3
# --- Сторонние библиотеки ---
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
import logging

# --- Внутренние модули ---
from services.database import get_user_data, save_user_data, get_owner_data
from services.menu import update_menu
from services.balance import refresh_balance
from services.buy import buy_gift

logger = logging.getLogger(__name__)

def register_main_handlers(dp, bot, version):
    """
    Registers main handlers for main menu, start and control commands.
    """

    @dp.message(CommandStart())
    async def command_status_handler(message: Message, state: FSMContext):
        """
        Обрабатывает команду /start — обновляет баланс и показывает главное меню.
        Очищает все состояния FSM для пользователя.
        """
        await state.clear()
        owner_data = await get_owner_data()
        is_owner = message.from_user.id == owner_data.get("owner_id", message.from_user.id)
        
        if is_owner:
            await refresh_balance(bot)
            
        await update_menu(
            bot=bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            message_id=message.message_id,
            is_owner=is_owner
        )


    @dp.callback_query(F.data == "main_menu")
    async def start_callback(call: CallbackQuery, state: FSMContext):
        """
        Показывает главное меню по нажатию кнопки "Вернуться в меню".
        Очищает все состояния FSM для пользователя.
        """
        await state.clear()
        await call.answer()
        
        owner_data = await get_owner_data()
        is_owner = call.from_user.id == owner_data.get("owner_id", call.from_user.id)
        
        if is_owner:
            await refresh_balance(call.bot)
            
        await update_menu(
            bot=call.bot,
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
            message_id=call.message.message_id,
            is_owner=is_owner
        )


    @dp.callback_query(F.data == "show_help")
    async def help_callback(call: CallbackQuery):
        """
        Показывает подробную справку по работе с ботом.
        """
        from services.localization import get_text
        
        bot_info = await call.bot.get_me()
        bot_username = bot_info.username
        
        help_text = await get_text(call.from_user.id, "help_text", 
                                 version=version, 
                                 bot_username=bot_username)
        
        help_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=await get_text(call.from_user.id, "contact_dev_button"), callback_data="contact_developer")],
            [InlineKeyboardButton(text=await get_text(call.from_user.id, "donate_to_dev_button"), callback_data="donate_to_dev")],
            [InlineKeyboardButton(text=await get_text(call.from_user.id, "back_to_menu"), callback_data="main_menu")]
        ])
        
        await call.answer()
        await call.message.answer(help_text, reply_markup=help_keyboard)


    @dp.callback_query(F.data == "contact_developer")
    async def contact_developer(call: CallbackQuery):
        """
        توجيه المستخدم للتحدث مع المطور.
        """
        await call.answer()
        contact_text = (
            "💬 <b>Contact Developer</b>\n\n"
            "📲 Click the link below to start a chat with the developer:\n\n"
            "👨‍💻 @TheSniper051\n\n"
            "💡 <b>Available for:</b>\n"
            "• Technical support\n"
            "• Feature requests\n"
            "• Bug reports\n"
            "• Custom development"
        )
        
        contact_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Open Chat", url="https://t.me/TheSniper051")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="show_help")]
        ])
        
        await call.message.edit_text(contact_text, reply_markup=contact_keyboard)

    @dp.callback_query(F.data == "donate_to_dev")
    async def donate_to_dev(call: CallbackQuery):
        """
        تبرع للمطور بنجمة واحدة.
        """
        from services.localization import get_text
        from aiogram.types import LabeledPrice
        
        try:
            # Create invoice for 100 stars donation
            prices = [LabeledPrice(label="XTR", amount=100)]
            
            await call.message.answer_invoice(
                title="💝 Donate to Developer",
                description="Support the developer with 100 stars donation",
                prices=prices,
                provider_token="",
                payload="dev_donation",
                currency="XTR",
                start_parameter="donate",
            )
            
            await call.answer("💝 Thank you for considering a donation!")
        
        except Exception as e:
            await call.answer()
            donation_failed_text = await get_text(call.from_user.id, "donation_failed")
            await call.message.answer(donation_failed_text)


    @dp.callback_query(F.data == "reset_bought")
    async def reset_bought_callback(call: CallbackQuery):
        """
        Сброс счетчиков купленных подарков и статусов выполнения по всем профилям.
        """
        from services.localization import get_text
        
        user_data = await get_user_data(call.from_user.id)
        profiles = user_data.get("profiles", [])
        
        # Сбросить счетчики во всех профилях
        for profile in profiles:
            profile["bought"] = 0
            profile["spent"] = 0
            profile["done"] = False
        
        user_data["active"] = False
        await save_user_data(call.from_user.id, user_data)
        
        reset_text = await get_text(call.from_user.id, "counters_reset")
        await call.answer(reset_text)
        
        owner_data = await get_owner_data()
        is_owner = call.from_user.id == owner_data.get("owner_id", call.from_user.id)
        await update_menu(
            bot=call.bot,
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
            message_id=call.message.message_id,
            is_owner=is_owner
        )


    @dp.callback_query(F.data == "toggle_active")
    async def toggle_active_callback(call: CallbackQuery):
        """
        Переключение статуса работы бота: активен/неактивен.
        """
        from services.localization import get_text
        
        user_data = await get_user_data(call.from_user.id)
        user_data["active"] = not user_data.get("active", False)
        await save_user_data(call.from_user.id, user_data)
        
        status_text = await get_text(call.from_user.id, "status_updated")
        await call.answer(status_text)
        
        owner_data = await get_owner_data()
        is_owner = call.from_user.id == owner_data.get("owner_id", call.from_user.id)
        await update_menu(
            bot=call.bot,
            chat_id=call.message.chat.id,
            user_id=call.from_user.id,
            message_id=call.message.message_id,
            is_owner=is_owner
        )

    @dp.pre_checkout_query()
    async def pre_checkout_handler(pre_checkout_query):
        """
        Обработка предоплаты в Telegram Invoice.
        """
        await pre_checkout_query.answer(ok=True)


    @dp.message(F.successful_payment)
    async def process_successful_payment(message: Message):
        """
        Process successful payment with commission deduction for multi-user system.
        Enhanced to track developer donations.
        """
        from services.database import get_owner_data, add_commission, update_user_balance, save_owner_data
        from services.localization import get_text
        
        # Check if this is a developer donation
        if message.successful_payment.invoice_payload == "dev_donation":
            # Handle developer donation
            owner_data = await get_owner_data()
            owner_data["developer_donations"] = owner_data.get("developer_donations", 0) + 1
            owner_data["total_donations_received"] = owner_data.get("total_donations_received", 0) + message.successful_payment.total_amount
            await save_owner_data(owner_data)
            
            # Send thank you message
            donation_success_text = await get_text(message.from_user.id, "donation_success")
            await message.answer(
                donation_success_text,
                message_effect_id="5104841245755180586"
            )
            
            # Notify developer about donation
            try:
                owner_id = owner_data.get("owner_id")
                if owner_id and owner_id != message.from_user.id:
                    donation_notification = (
                        f"💝 <b>NEW DONATION RECEIVED!</b>\n\n"
                        f"👤 <b>From:</b> {message.from_user.first_name or 'Unknown'} ({message.from_user.id})\n"
                        f"⭐ <b>Amount:</b> {message.successful_payment.total_amount} stars\n"
                        f"📊 <b>Total Donations:</b> {owner_data['developer_donations']} donations\n"
                        f"💰 <b>Total Received:</b> {owner_data['total_donations_received']} stars\n\n"
                        f"🙏 <b>Thank you for the generous support!</b>"
                    )
                    await bot.send_message(owner_id, donation_notification)
            except Exception as e:
                logger.error(f"Failed to send donation notification: {e}")
            
            return
        
        # Regular deposit processing
        # Get payment amount
        total_amount = message.successful_payment.total_amount
        
        # Get commission rate
        owner_data = await get_owner_data()
        commission_rate = owner_data.get("commission_rate", 0.05)
        
        # Calculate commission and user amount
        commission = int(total_amount * commission_rate)
        user_amount = total_amount - commission
        
        # Add commission to owner balance
        await add_commission(commission, message.from_user.id)
        
        # Add amount to user balance
        await update_user_balance(message.from_user.id, user_amount)
        
        # Send success message with commission info
        success_text = await get_text(
            message.from_user.id,
            "deposit_success",
            total_amount=total_amount,
            user_amount=user_amount,
            commission=commission,
            rate=commission_rate * 100
        )
        
        await message.answer(
            success_text,
            message_effect_id="5104841245755180586"
        )
        
        # Send commission notification to owner (if not the owner depositing)
        if message.from_user.id != owner_data.get("owner_id", message.from_user.id):
            try:
                owner_balance = (await get_owner_data())["commission_balance"]
                notification_text = await get_text(
                    owner_data.get("owner_id", message.from_user.id),
                    "commission_notification",
                    commission=commission,
                    user_name=message.from_user.first_name or "Unknown",
                    balance=owner_balance
                )
                await bot.send_message(
                    owner_data.get("owner_id", message.from_user.id),
                    notification_text
                )
            except Exception as e:
                logger.error(f"Failed to send commission notification: {e}")
        
        # Update menu
        is_owner = message.from_user.id == owner_data.get("owner_id", message.from_user.id)
        await update_menu(
            bot=bot, 
            chat_id=message.chat.id, 
            user_id=message.from_user.id, 
            message_id=message.message_id,
            is_owner=is_owner
        )
