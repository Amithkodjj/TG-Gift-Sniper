# --- Стандартные библиотеки ---
import asyncio

# --- Сторонние библиотеки ---
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

# --- Внутренние модули ---
from services.config import get_target_display_local
from services.menu import update_menu
from services.gifts import get_filtered_gifts
from services.buy import buy_gift
from services.balance import refresh_balance

wizard_router = Router()

class CatalogFSM(StatesGroup):
    """
    States for gift catalog FSM.
    """
    waiting_gift = State()
    waiting_quantity = State()
    waiting_confirm = State()


def gifts_catalog_keyboard(gifts):
    """
    Forms keyboard for catalog подарков. 
    Каждый подарок — отдельная кнопка, плюс кнопка возврата в меню.
    """
    keyboard = []
    for gift in gifts:
        if gift['supply'] == None:
            btn = InlineKeyboardButton(
                text=f"{gift['emoji']} — ★{gift['price']:,}",
                callback_data=f"catalog_gift_{gift['id']}"
            )
        else:
            btn = InlineKeyboardButton(
                text=f"{gift['left']:,} из {gift['supply']:,} — ★{gift['price']:,}",
                callback_data=f"catalog_gift_{gift['id']}"
            )
        keyboard.append([btn])

    # Back to main menu button  
    keyboard.append([
        InlineKeyboardButton(
            text="☰ Back to Menu", 
            callback_data="catalog_main_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@wizard_router.callback_query(F.data == "catalog")
async def catalog(call: CallbackQuery, state: FSMContext):
    """
    Handle catalog opening. Gets gift list и forms message with keyboard.
    """
    gifts = await get_filtered_gifts(
        bot=call.bot,
        min_price=0,
        max_price=1000000,
        min_supply=0,
        max_supply=100000000,
        unlimited = True
    )

    # Сохраняем текущий каталог в FSM — нужен для последующих шагов
    await state.update_data(gifts_catalog=gifts)

    gifts_limited = [g for g in gifts if g['supply'] != None]
    gifts_unlimited = [g for g in gifts if g['supply'] == None]

    from services.localization import get_text
    header_text = await get_text(call.from_user.id, "catalog_header", 
                                unlimited=len(gifts_unlimited), 
                                limited=len(gifts_limited))
    
    await call.message.answer(header_text, reply_markup=gifts_catalog_keyboard(gifts))

    await call.answer()


@wizard_router.callback_query(F.data == "catalog_main_menu")
async def start_callback(call: CallbackQuery, state: FSMContext):
    """
    Показывает главное меню по нажатию кнопки "Вернуться в меню".
    Очищает все состояния FSM для пользователя.
    """
    await state.clear()
    from services.localization import get_text
    closed_text = await get_text(call.from_user.id, "catalog_closed")
    
    await call.answer()
    await safe_edit_text(call.message, closed_text, reply_markup=None)
    await refresh_balance(call.bot)
    await update_menu(
        bot=call.bot,
        chat_id=call.message.chat.id,
        user_id=call.from_user.id,
        message_id=call.message.message_id
    )


@wizard_router.callback_query(F.data.startswith("catalog_gift_"))
async def on_gift_selected(call: CallbackQuery, state: FSMContext):
    """
    Хендлер выбора подарка из каталога. Запрашивает у пользователя количество для покупки.
    """
    gift_id = call.data.split("_")[-1]
    data = await state.get_data()
    gifts = data.get("gifts_catalog", [])
    if not gifts:
        outdated_text = await get_text(call.from_user.id, "catalog_outdated")
        await call.answer(outdated_text, show_alert=True)
        await safe_edit_text(call.message, outdated_text, reply_markup=None)
        return
    gift = next((g for g in gifts if str(g['id']) == gift_id), None)

    gift_display = f"{gift['left']:,} из {gift['supply']:,}" if gift.get("supply") != None else gift.get("emoji")

    await state.update_data(selected_gift=gift)
    from services.localization import get_text
    
    text = await get_text(call.from_user.id, "gift_selected", 
                         gift_display=gift_display, 
                         price=gift['price'])
    
    await call.message.edit_text(text, reply_markup=None)
    await state.set_state(CatalogFSM.waiting_quantity)
    await call.answer()


@wizard_router.message(CatalogFSM.waiting_quantity)
async def on_quantity_entered(message: Message, state: FSMContext):
    """
    Handle quantity input for gift purchase.
    Automatically uses user's own ID as recipient and proceeds to confirmation.
    """
    if await try_cancel(message, state):
        return
    
    try:
        qty = int(message.text)
        if qty <= 0:
            raise ValueError
    except Exception:
        from services.localization import get_text
        error_text = await get_text(message.from_user.id, "enter_quantity_error")
        await message.answer(error_text)
        return
    
    # Auto-set recipient as the user themselves
    target_user_id = message.from_user.id
    target_chat_id = None
    
    await state.update_data(
        selected_qty=qty,
        target_user_id=target_user_id,
        target_chat_id=target_chat_id
    )

    # Get data for confirmation
    data = await state.get_data()
    gift = data["selected_gift"]
    price = gift.get("price")
    total = price * qty

    gift_display = f"{gift['emoji']} {gift.get('name', 'Gift')}" if gift.get("supply") == None else f"{gift['left']:,} of {gift['supply']:,} available"

    from services.localization import get_text
    confirm_text = await get_text(message.from_user.id, "confirm_btn")
    cancel_text = await get_text(message.from_user.id, "cancel_btn")
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=confirm_text, callback_data="confirm_purchase"),
                InlineKeyboardButton(text=cancel_text, callback_data="cancel_purchase"),
            ]
        ]
    )
    
    recipient_display = f"<code>{target_user_id}</code> (You)"
    summary_text = await get_text(message.from_user.id, "purchase_summary",
                                 gift_display=gift_display,
                                 qty=qty,
                                 price=price,
                                 total=total,
                                 recipient=recipient_display)
    
    await message.answer(summary_text, reply_markup=kb)
    await state.set_state(CatalogFSM.waiting_confirm)


@wizard_router.callback_query(F.data == "confirm_purchase")
async def confirm_purchase(call: CallbackQuery, state: FSMContext):
    """
    Подтверждение и запуск покупки выбранного подарка в заданном количестве для выбранного получателя.
    """
    data = await state.get_data()
    gift = data["selected_gift"]
    from services.localization import get_text
    
    if not gift:
        invalid_text = await get_text(call.from_user.id, "invalid_purchase")
        await call.answer(invalid_text, show_alert=True)
        await safe_edit_text(call.message, invalid_text, reply_markup=None)
        return
    
    processing_text = await get_text(call.from_user.id, "purchase_processing")
    await call.message.edit_text(text=processing_text, reply_markup=None)
    gift_id = gift.get("id")
    gift_price = gift.get("price")
    qty = data["selected_qty"]
    target_user_id=data.get("target_user_id")
    target_chat_id=data.get("target_chat_id")
    gift_display = f"{gift['left']:,} из {gift['supply']:,}" if gift.get("supply") != None else gift.get("emoji")

    bought = 0
    while bought < qty:
        success = await buy_gift(
            bot=call.bot,
            env_user_id=call.from_user.id,
            gift_id=gift_id,
            user_id=target_user_id,
            chat_id=target_chat_id,
            gift_price=gift_price,
            file_id=None
        )

        if not success:
            break

        bought += 1
        await asyncio.sleep(0.3)

    recipient = get_target_display_local(target_user_id, target_chat_id, call.from_user.id)
    
    if bought == qty:
        success_text = await get_text(call.from_user.id, "purchase_success",
                                    gift_display=gift_display,
                                    bought=bought,
                                    qty=qty,
                                    recipient=recipient)
        await call.message.answer(success_text)
    else:
        partial_text = await get_text(call.from_user.id, "purchase_partial",
                                    gift_display=gift_display,
                                    bought=bought,
                                    qty=qty,
                                    recipient=recipient)
        await call.message.answer(partial_text)
    
    await state.clear()
    await call.answer()
    await update_menu(bot=call.bot, chat_id=call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


@wizard_router.callback_query(lambda c: c.data == "cancel_purchase")
async def cancel_callback(call: CallbackQuery, state: FSMContext):
    """
    Отмена покупки подарка на этапе подтверждения.
    """
    from services.localization import get_text
    cancelled_text = await get_text(call.from_user.id, "action_cancelled")
    
    await state.clear()
    await call.answer()
    await safe_edit_text(call.message, cancelled_text, reply_markup=None)
    await update_menu(bot=call.bot, chat_id=call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


async def try_cancel(message: Message, state: FSMContext) -> bool:
    """
    Универсальная функция для обработки отмены любого шага с помощью /cancel.
    Очищает состояние, возвращает True если была отмена.
    """
    if message.text and message.text.strip().lower() == "/cancel":
        from services.localization import get_text
        cancelled_text = await get_text(message.from_user.id, "action_cancelled")
        
        await state.clear()
        await message.answer(cancelled_text)
        await update_menu(bot=message.bot, chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id)
        return True
    return False


async def safe_edit_text(message, text, reply_markup=None):
    """
    Safely edits message text, ignoring errors "нельзя редактировать" и "сообщение не найдено".
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup)
        return True
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e) or "message to edit not found" in str(e):
            # Simply ignore — message is outdated or deleted
            return False
        else:
            raise


def register_catalog_handlers(dp):
    """
    Registers all handlers, related to gift catalog.
    """
    dp.include_router(wizard_router)
