# --- Стандартные библиотеки ---
import logging

# --- Сторонние библиотеки ---
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

# --- Внутренние модули ---
from services.config import get_valid_config, get_target_display, save_config
from services.menu import update_menu, payment_keyboard
from services.balance import refresh_balance, refund_all_star_payments
from services.config import CURRENCY, MAX_PROFILES, add_profile, remove_profile, update_profile
from services.localization import get_text

logger = logging.getLogger(__name__)
wizard_router = Router()

class ConfigWizard(StatesGroup):
    """
    State class for FSM wizard (step-by-step configuration editing).
    Each state is a separate step in the process.
    """
    min_price = State()
    max_price = State()
    min_supply = State()
    max_supply = State()
    count = State()
    limit = State()
    user_id = State()
    edit_min_price = State()
    edit_max_price = State()
    edit_min_supply = State()
    edit_max_supply = State()
    edit_count = State()
    edit_limit = State()
    edit_user_id = State()
    deposit_amount = State()
    refund_id = State()
    guest_deposit_amount = State()
    guest_refund_id = State()


async def profiles_menu(message: Message, user_id: int):
    """
    Показывает пользователю главное меню управления профилями.
    Displays list of all created profiles и предоставляет кнопки для их редактирования, удаления или добавления нового профиля.
    """
    config = await get_valid_config(user_id)
    profiles = config.get("PROFILES", [])

    # Form profiles keyboard
    keyboard = []
    for idx, profile in enumerate(profiles):
        btns = [
            InlineKeyboardButton(
                text=f"✏️ Profile {idx+1}", callback_data=f"profile_edit_{idx}"
            ),
            InlineKeyboardButton(
                text="🗑 Delete", callback_data=f"profile_delete_{idx}"
            ),
        ]
        keyboard.append(btns)
    # Add button (maximum 3 profiles)
    if len(profiles) < MAX_PROFILES:
        keyboard.append([InlineKeyboardButton(text="➕ Add", callback_data="profile_add")])
    # Back button
    keyboard.append([InlineKeyboardButton(text="☰ Back to menu", callback_data="profiles_main_menu")])

    profiles = config.get("PROFILES", [])

    lines = []
    for idx, profile in enumerate(profiles, 1):
        target_display = get_target_display(profile, user_id)
        if idx == 1 and len(profiles) == 1: line = (f"🔘 <b>Profile {idx}</b> – {target_display}")
        elif idx == 1: line = (f"┌🔘 <b>Profile {idx}</b> – {target_display}")
        elif len(profiles) == idx: line = (f"└🔘 <b>Profile {idx}</b> – {target_display}")
        else: line = (f"├🔘 <b>Profile {idx}</b> – {target_display}")
        lines.append(line)
    text_profiles = "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(f"📝 <b>Profile Management (max 3):</b>\n\n{text_profiles}", reply_markup=kb)


@wizard_router.callback_query(F.data == "profiles_menu")
async def on_profiles_menu(call: CallbackQuery):
    """
    Handles button click "Профили" или переход к списку профилей.
    Opens menu with all profiles пользователя и возможностью их выбора для редактирования или удаления.
    """
    await profiles_menu(call.message, call.from_user.id)
    await call.answer()


def profile_text(profile, idx, user_id):
    """
    Forms text description параметров профиля по его данным.
    Includes prices, limits, supply, получателя и другую основную информацию по выбранному профилю.
    Используется для вывода информации при редактировании профиля.
    """
    target_display = get_target_display(profile, user_id)
    return (f"✏️ <b>Editing Profile {idx+1}</b>\n\n"
            f"┌─────────────────────────────────┐\n"
            f"│       📊 <b>PROFILE {idx+1}</b>          │\n"
            f"├─────────────────────────────────┤\n"
            f"│ 💎 Price: <code>{profile.get('MIN_PRICE'):,}</code> - <code>{profile.get('MAX_PRICE'):,}</code> coins │\n"
            f"│ 📦 Supply: <code>{profile.get('MIN_SUPPLY'):,}</code> - <code>{profile.get('MAX_SUPPLY'):,}</code> left   │\n"
            f"│ 🎁 Count: <code>{profile.get('COUNT'):,}</code> gifts max         │\n"
            f"│ 💸 Limit: <code>{profile.get('LIMIT'):,}</code> coins budget      │\n"
            f"│ 👤 Target: {target_display}         │\n"
            f"└─────────────────────────────────┘\n\n"
            f"<b>Select setting to modify:</b>")


def profile_edit_keyboard(idx):
    """
    Creates inline keyboard для быстрого редактирования параметров выбранного профиля.
    Каждая кнопка отвечает за редактирование отдельного поля (цены, supply, лимита и т.д.).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Price", callback_data=f"edit_profile_price_{idx}"),
                InlineKeyboardButton(text="📦 Supply", callback_data=f"edit_profile_supply_{idx}"),
            ],
            [
                InlineKeyboardButton(text="🎁 Count", callback_data=f"edit_profile_count_{idx}"),
                InlineKeyboardButton(text="💸 Limit", callback_data=f"edit_profile_limit_{idx}")
            ],
            [
                InlineKeyboardButton(text="👤 Target", callback_data=f"edit_profile_target_{idx}"),
                InlineKeyboardButton(text="⬅️ Back", callback_data=f"edit_profiles_menu_{idx}")
            ]
        ]
    )


@wizard_router.callback_query(lambda c: c.data.startswith("profile_edit_"))
async def on_profile_edit(call: CallbackQuery, state: FSMContext):
    """
    Opens detailed editing screen конкретного профиля.
    Показывает все параметры профиля и инлайн-кнопки для выбора нужного параметра для изменения.
    """
    idx = int(call.data.split("_")[-1])
    config = await get_valid_config(call.from_user.id)
    profile = config["PROFILES"][idx]
    await state.update_data(profile_index=idx)
    await state.update_data(message_id=call.message.message_id)
    await call.message.edit_text(
        profile_text(profile, idx, call.from_user.id),
        reply_markup=profile_edit_keyboard(idx)
    )
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("edit_profile_price_"))
async def edit_profile_min_price(call: CallbackQuery, state: FSMContext):
    """
    Handles button click изменения минимальной цены в профиле.
    Moves user to state ввода новой минимальной цены.
    """
    idx = int(call.data.split("_")[-1])
    await state.update_data(profile_index=idx)
    await state.update_data(message_id=call.message.message_id)
    await call.message.answer(f"✏️ <b>Editing Profile {idx + 1}:</b>\n\n�� Minimum gift price, for example: <code>5000</code>\n\n/cancel — cancel")
    await state.set_state(ConfigWizard.edit_min_price)
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("edit_profile_supply_"))
async def edit_profile_min_supply(call: CallbackQuery, state: FSMContext):
    """
    Handles button click изменения минимального supply для профиля.
    Moves user to state ввода нового минимального значения supply.
    """
    idx = int(call.data.split("_")[-1])
    await state.update_data(profile_index=idx)
    await state.update_data(message_id=call.message.message_id)
    await call.message.answer(f"✏️ <b>Editing Profile {idx + 1}:</b>\n\n📦 Minimum supply for gift, for example: <code>1000</code>\n\n/cancel — cancel")
    await state.set_state(ConfigWizard.edit_min_supply)
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("edit_profile_limit_"))
async def edit_profile_limit(call: CallbackQuery, state: FSMContext):
    """
    Handles button click изменения лимита по звёздам (максимальной суммы расходов) для профиля.
    Moves user to state ввода нового лимита.
    """
    idx = int(call.data.split("_")[-1])
    await state.update_data(profile_index=idx)
    await state.update_data(message_id=call.message.message_id)
    await call.message.answer(
            f"✏️ <b>Editing Profile {idx + 1}:</b>\n\n"
                            "💸 <b>Enter coin limit for this profile</b> (example: `10000`)\n\n"
            "`/cancel` — cancel"
        )
    await state.set_state(ConfigWizard.edit_limit)
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("edit_profile_count_"))
async def edit_profile_count(call: CallbackQuery, state: FSMContext):
    """
    Handles button click изменения количества подарков в профиле.
    Moves user to state ввода нового количества.
    """
    idx = int(call.data.split("_")[-1])
    await state.update_data(profile_index=idx)
    await state.update_data(message_id=call.message.message_id)
    await call.message.answer(f"✏️ <b>Editing Profile {idx + 1}:</b>\n\n🎁 Maximum number of gifts, for example: <code>5</code>\n\n/cancel — cancel")
    await state.set_state(ConfigWizard.edit_count)
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("edit_profile_target_"))
async def edit_profile_target(call: CallbackQuery, state: FSMContext):
    """
    Handles button click изменения получателя подарков (user_id или @username).
    Moves user to state ввода нового получателя.
    """
    idx = int(call.data.split("_")[-1])
    await state.update_data(profile_index=idx)
    await state.update_data(message_id=call.message.message_id)
    await call.message.answer(
            f"✏️ <b>Editing Profile {idx + 1}:</b>\n\n"
            "👤 Enter recipient address:\n\n"
            f"• <b>User ID</b> (for example: <code>6920475855</code>)\n"
            "• Or <b>channel username</b> (for example: <code>@channel</code>)\n\n"
            "❗️ Get user ID here @userinfobot\n\n"
            "/cancel — cancel"
        )
    await state.set_state(ConfigWizard.edit_user_id)
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("edit_profiles_menu_"))
async def edit_profiles_menu(call: CallbackQuery):
    """
    Handles return from edit mode профиля в основное меню профилей.
    Открывает пользователю общий список всех профилей.
    """
    idx = int(call.data.split("_")[-1])
    await safe_edit_text(call.message, f"✅ Profile <b>{idx + 1}</b> edited.", reply_markup=None)
    await profiles_menu(call.message, call.from_user.id)
    await call.answer()


@wizard_router.message(ConfigWizard.edit_min_price)
async def step_edit_min_price(message: Message, state: FSMContext):
    """
    Handles user input нового значения минимальной цены для профиля.
    Validates input, сохраняет и возвращает пользователя в меню профиля.
    """
    if await try_cancel(message, state):
        return
    
    data = await state.get_data()
    idx = data["profile_index"]
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        await state.update_data(MIN_PRICE=value)
        await message.answer(f"✏️ <b>Editing Profile {idx + 1}:</b>\n\n💰 Maximum gift price, for example: <code>10000</code>\n\n/cancel — cancel")
        await state.set_state(ConfigWizard.edit_max_price)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.edit_max_price)
async def step_edit_max_price(message: Message, state: FSMContext):
    """
    Handles user input нового значения максимальной цены для профиля.
    Validates input, сохраняет и возвращает пользователя в меню профиля.
    """
    if await try_cancel(message, state):
        return
    
    data = await state.get_data()
    idx = data["profile_index"]
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError

        data = await state.get_data()
        min_price = data.get("MIN_PRICE")
        if min_price and value < min_price:
            await message.answer("🚫 Maximum price cannot be less than minimum. Try again.")
            return

        config = await get_valid_config(message.from_user.id)
        config["PROFILES"][idx]["MIN_PRICE"] = data["MIN_PRICE"]
        config["PROFILES"][idx]["MAX_PRICE"] = value
        await save_config(config)

        try:
            await message.bot.delete_message(message.chat.id, data["message_id"])
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")

        await message.answer(
            profile_text(config["PROFILES"][idx], idx, message.from_user.id),
            reply_markup=profile_edit_keyboard(idx)
        )
        await state.clear()
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.edit_min_supply)
async def step_edit_min_supply(message: Message, state: FSMContext):
    """
    Handles user input нового значения минимального supply для профиля.
    Validates input, сохраняет и возвращает пользователя в меню профиля.
    """
    if await try_cancel(message, state):
        return
    
    data = await state.get_data()
    idx = data["profile_index"]
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        await state.update_data(MIN_SUPPLY=value)
        await message.answer(f"✏️ <b>Editing Profile {idx + 1}:</b>\n\n📦 Maximum supply for gift, for example: <code>10000</code>\n\n/cancel — cancel")
        await state.set_state(ConfigWizard.edit_max_supply)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.edit_max_supply)
async def step_edit_max_supply(message: Message, state: FSMContext):
    """
    Handles user input нового значения максимального supply для профиля.
    Validates input, сохраняет и возвращает пользователя в меню профиля.
    """
    if await try_cancel(message, state):
        return
    
    data = await state.get_data()
    idx = data["profile_index"]
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError

        data = await state.get_data()
        min_supply = data.get("MIN_SUPPLY")
        if min_supply and value < min_supply:
            await message.answer("🚫 Maximum supply cannot be less than minimum. Try again.")
            return
        
        config = await get_valid_config(message.from_user.id)
        config["PROFILES"][idx]["MIN_SUPPLY"] = data["MIN_SUPPLY"]
        config["PROFILES"][idx]["MAX_SUPPLY"] = value
        await save_config(config)

        try:
            await message.bot.delete_message(message.chat.id, data["message_id"])
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")

        await message.answer(
            profile_text(config["PROFILES"][idx], idx, message.from_user.id),
            reply_markup=profile_edit_keyboard(idx)
        )
        await state.clear()
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.edit_limit)
async def step_edit_limit(message: Message, state: FSMContext):
    """
    Handles user input нового значения лимита (максимальной суммы расходов) для профиля.
    Validates input, сохраняет и возвращает пользователя в меню профиля.
    """
    if await try_cancel(message, state):
        return

    data = await state.get_data()
    idx = data["profile_index"]

    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        
        config = await get_valid_config(message.from_user.id)
        config["PROFILES"][idx]["LIMIT"] = value
        await save_config(config)

        try:
            await message.bot.delete_message(message.chat.id, data["message_id"])
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")

        await message.answer(
            profile_text(config["PROFILES"][idx], idx, message.from_user.id),
            reply_markup=profile_edit_keyboard(idx)
        )
        await state.clear()
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.edit_count)
async def step_edit_count(message: Message, state: FSMContext):
    """
    Handles user input нового количества подарков для профиля.
    Validates input, сохраняет и возвращает пользователя в меню профиля.
    """
    if await try_cancel(message, state):
        return
    
    data = await state.get_data()
    idx = data["profile_index"]

    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        
        config = await get_valid_config(message.from_user.id)
        config["PROFILES"][idx]["COUNT"] = value
        await save_config(config)

        try:
            await message.bot.delete_message(message.chat.id, data["message_id"])
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")

        await message.answer(
            profile_text(config["PROFILES"][idx], idx, message.from_user.id),
            reply_markup=profile_edit_keyboard(idx)
        )
        await state.clear()
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.edit_user_id)
async def step_edit_user_id(message: Message, state: FSMContext):
    """
    Handles user input нового получателя (user_id или @username) для профиля.
    Проверяет корректность, сохраняет и возвращает пользователя в меню профиля.
    """
    if await try_cancel(message, state):
        return
    
    data = await state.get_data()
    idx = data["profile_index"]

    user_input = message.text.strip()
    if user_input.startswith("@"):
        chat_type = await get_chat_type(bot=message.bot, username=user_input)
        if chat_type == "channel":
            target_chat = user_input
            target_user = None
        else:
            await message.answer("🚫 You entered an incorrect <b>channel username</b>. Try again.")
            return
    elif user_input.isdigit():
        target_chat = None
        target_user = int(user_input)
    else:
        await message.answer("🚫 Enter user ID or channel username. Try again.")
        return
    
    config = await get_valid_config(message.from_user.id)
    config["PROFILES"][idx]["TARGET_USER_ID"] = target_user
    config["PROFILES"][idx]["TARGET_CHAT_ID"] = target_chat
    await save_config(config)

    try:
        await message.bot.delete_message(message.chat.id, data["message_id"])
    except Exception as e:
        logger.warning(f"Failed to delete message: {e}")

    await message.answer(
            profile_text(config["PROFILES"][idx], idx, message.from_user.id),
            reply_markup=profile_edit_keyboard(idx)
        )
    await state.clear()


@wizard_router.callback_query(F.data == "profile_add")
async def on_profile_add(call: CallbackQuery, state: FSMContext):
    """
    Starts step-by-step creation wizard нового профиля подарков.
    Moves user to first stage ввода параметров нового профиля.
    """
    await state.update_data(profile_index=None)
    await call.message.answer("➕ Adding <b>new profile</b>.\n\n"
                              "💰 Minimum gift price, for example: <code>5000</code>\n\n"
                              "/cancel — cancel", reply_markup=None)
    await state.set_state(ConfigWizard.min_price)
    await call.answer()


@wizard_router.message(ConfigWizard.user_id)
async def step_user_id(message: Message, state: FSMContext):
    """
    Handles recipient address input (user ID или username) и сохраняет профиль.
    """
    if await try_cancel(message, state):
        return

    user_input = message.text.strip()
    if user_input.startswith("@"):
        chat_type = await get_chat_type(bot=message.bot, username=user_input)
        if chat_type == "channel":
            target_chat = user_input
            target_user = None
        else:
            await message.answer("🚫 You entered an incorrect <b>channel username</b>. Try again.")
            return
    elif user_input.isdigit():
        target_chat = None
        target_user = int(user_input)
    else:
        await message.answer("🚫 Enter user ID or channel username. Try again.")
        return

    data = await state.get_data()
    profile_data = {
        "MIN_PRICE": data["MIN_PRICE"],
        "MAX_PRICE": data["MAX_PRICE"],
        "MIN_SUPPLY": data["MIN_SUPPLY"],
        "MAX_SUPPLY": data["MAX_SUPPLY"],
        "LIMIT": data["LIMIT"],
        "COUNT": data["COUNT"],
        "TARGET_USER_ID": target_user,
        "TARGET_CHAT_ID": target_chat,
        "BOUGHT": 0,
        "SPENT": 0,
        "DONE": False,
    }

    config = await get_valid_config(message.from_user.id)
    profile_index = data.get("profile_index")

    if profile_index is None:
        await add_profile(config, profile_data)
        await message.answer("✅ <b>New profile</b> created.")
    else:
        await update_profile(config, profile_index, profile_data)
        await message.answer(f"✅ <b>Profile {profile_index+1}</b> updated.")

    await state.clear()
    await update_menu(bot=message.bot, chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id)


@wizard_router.callback_query(F.data == "profiles_main_menu")
async def start_callback(call: CallbackQuery, state: FSMContext):
    """
    Показывает главное меню по нажатию кнопки "Вернуться в меню".
    Очищает все состояния FSM для пользователя.
    """
    await state.clear()
    await call.answer()
    await safe_edit_text(call.message, "✅ Profile editing completed.", reply_markup=None)
    await refresh_balance(call.bot)
    await update_menu(
        bot=call.bot,
        chat_id=call.message.chat.id,
        user_id=call.from_user.id,
        message_id=call.message.message_id
    )


@wizard_router.callback_query(lambda c: c.data.startswith("profile_delete_"))
async def on_profile_delete_confirm(call: CallbackQuery, state: FSMContext):
    """
    Запрашивает подтверждение удаления профиля.
    """
    idx = int(call.data.split("_")[-1])
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes", callback_data=f"confirm_delete_{idx}"),
                InlineKeyboardButton(text="❌ No", callback_data=f"cancel_delete_{idx}"),
            ]
        ]
    )
    config = await get_valid_config(call.from_user.id)
    profiles = config.get("PROFILES", [])
    profile = profiles[idx]
    target_display = get_target_display(profile, call.from_user.id)
    message = (f"┌─────────────────────────────────┐\n"
                            f"│     📊 <b>Profile {idx+1}</b>           │\n"
            f"├─────────────────────────────────┤\n"
            f"│ 🎁 Progress: <code>{profile.get('BOUGHT'):,}/{profile.get('COUNT'):,}</code> gifts      │\n"
            f"│ 💎 Price: <code>{profile.get('MIN_PRICE'):,}</code> - <code>{profile.get('MAX_PRICE'):,}</code> coins │\n"
            f"│ 📦 Supply: <code>{profile.get('MIN_SUPPLY'):,}</code> - <code>{profile.get('MAX_SUPPLY'):,}</code> left   │\n"
            f"│ 👤 Target: <code>{target_display}</code>         │\n"
            f"└─────────────────────────────────┘")
    await call.message.edit_text(
        f"⚠️ Are you sure you want to delete <b>profile {idx+1}</b>?\n\n{message}",
        reply_markup=kb
    )
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("confirm_delete_"))
async def on_profile_delete_final(call: CallbackQuery):
    """
    Окончательно удаляет профиль после подтверждения.
    """
    idx = int(call.data.split("_")[-1])
    config = await get_valid_config(call.from_user.id)
    deafult_added = "\n➕ <b>Added</b> default profile.\n🚦 Status changed to 🔴 (inactive)." if len(config["PROFILES"]) == 1 else ""
    if len(config["PROFILES"]) == 1:
        config["ACTIVE"] = False
        await save_config(config)
    await remove_profile(config, idx, call.from_user.id)
    await call.message.edit_text(f"✅ <b>Profile {idx+1}</b> deleted.{deafult_added}", reply_markup=None)
    await profiles_menu(call.message, call.from_user.id)
    await call.answer()


@wizard_router.callback_query(lambda c: c.data.startswith("cancel_delete_"))
async def on_profile_delete_cancel(call: CallbackQuery):
    """
    Отмена удаления профиля.
    """
    idx = int(call.data.split("_")[-1])
    await call.message.edit_text(f"🚫 Deletion of <b>profile {idx + 1}</b> cancelled.", reply_markup=None)
    await profiles_menu(call.message, call.from_user.id)
    await call.answer()


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


@wizard_router.callback_query(F.data == "edit_config")
async def edit_config_handler(call: CallbackQuery, state: FSMContext):
    """
    Запуск мастера редактирования configурации.
    """
    await call.message.answer("💰 Minimum gift price, for example: <code>5000</code>\n\n/cancel — cancel")
    await state.set_state(ConfigWizard.min_price)
    await call.answer()


@wizard_router.message(ConfigWizard.min_price)
async def step_min_price(message: Message, state: FSMContext):
    """
    Обработка ввода минимальной цены подарка.
    """
    if await try_cancel(message, state):
        return
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        await state.update_data(MIN_PRICE=value)
        await message.answer("💰 Maximum gift price, for example: <code>10000</code>\n\n/cancel — cancel")
        await state.set_state(ConfigWizard.max_price)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.max_price)
async def step_max_price(message: Message, state: FSMContext):
    """
    Обработка ввода максимальной цены подарка и проверка корректности диапазона.
    """
    if await try_cancel(message, state):
        return
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError

        data = await state.get_data()
        min_price = data.get("MIN_PRICE")
        if min_price and value < min_price:
            await message.answer("🚫 Maximum price cannot be less than minimum. Try again.")
            return

        await state.update_data(MAX_PRICE=value)
        await message.answer("📦 Minimum supply for gift, for example: <code>1000</code>\n\n/cancel — cancel")
        await state.set_state(ConfigWizard.min_supply)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.min_supply)
async def step_min_supply(message: Message, state: FSMContext):
    """
    Обработка ввода минимального саплая для подарка.
    """
    if await try_cancel(message, state):
        return
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        await state.update_data(MIN_SUPPLY=value)
        await message.answer("📦 Maximum supply for gift, for example: <code>10000</code>\n\n/cancel — cancel")
        await state.set_state(ConfigWizard.max_supply)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.max_supply)
async def step_max_supply(message: Message, state: FSMContext):
    """
    Обработка ввода максимального саплая для подарка, проверка диапазона.
    """
    if await try_cancel(message, state):
        return
    
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError

        data = await state.get_data()
        min_supply = data.get("MIN_SUPPLY")
        if min_supply and value < min_supply:
            await message.answer("🚫 Maximum supply cannot be less than minimum. Try again.")
            return

        await state.update_data(MAX_SUPPLY=value)
        await message.answer("🎁 Maximum number of gifts, for example: <code>5</code>\n\n/cancel — cancel")
        await state.set_state(ConfigWizard.count)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.count)
async def step_count(message: Message, state: FSMContext):
    """
    Обработка ввода количества подарков.
    """
    if await try_cancel(message, state):
        return

    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        await state.update_data(COUNT=value)
        await message.answer(
            "⭐️ Enter coin limit for this profile (example: <code>10000</code>)\n\n"
            "/cancel — cancel"
        )
        await state.set_state(ConfigWizard.limit)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.message(ConfigWizard.limit)
async def step_limit(message: Message, state: FSMContext):
    """
    Обработка ввода лимита звёзд на ордер.
    """
    if await try_cancel(message, state):
        return

    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        await state.update_data(LIMIT=value)
        await message.answer(
            "👤 Enter recipient address:\n\n"
            f"• <b>User ID</b> (for example: <code>6920475855</code>)\n"
            "• Or <b>channel username</b> (for example: <code>@channel</code>)\n\n"
            "❗️ Get user ID here @userinfobot\n\n"
            "/cancel — cancel"
        )
        await state.set_state(ConfigWizard.user_id)
    except ValueError:
        await message.answer("🚫 Enter a positive number. Try again.")


@wizard_router.callback_query(F.data == "deposit_menu")
async def deposit_menu(call: CallbackQuery, state: FSMContext):
    """
    Переход к шагу пополнения баланса.
    """
    text = await get_text(call.from_user.id, "wizard_deposit_amount")
    await call.message.answer(text)
    await state.set_state(ConfigWizard.deposit_amount)
    await call.answer()


@wizard_router.message(ConfigWizard.deposit_amount)
async def deposit_amount_input(message: Message, state: FSMContext):
    """
    Обработка суммы для пополнения и отправка счёта на оплату.
    """
    if await try_cancel(message, state):
        return

    try:
        amount = int(message.text)
        if amount < 1 or amount > 10000:
            raise ValueError
        prices = [LabeledPrice(label=CURRENCY, amount=amount)]
        title = await get_text(message.from_user.id, "gift_bot_title")
        description = await get_text(message.from_user.id, "deposit_description")
        await message.answer_invoice(
            title=title,
            description=description,
            prices=prices,
            provider_token="",  # Укажи свой токен
            payload="stars_deposit",
            currency=CURRENCY,
            start_parameter="deposit",
            reply_markup=payment_keyboard(amount=amount),
        )
        await state.clear()
    except ValueError:
        text = await get_text(message.from_user.id, "wizard_deposit_range_error")
        await message.answer(text)


@wizard_router.callback_query(F.data == "refund_menu")
async def refund_menu(call: CallbackQuery, state: FSMContext):
    """
    Переход к возврату звёзд (по ID транзакции).
    """
    text = await get_text(call.from_user.id, "wizard_refund_id")
    await call.message.answer(text)
    await state.set_state(ConfigWizard.refund_id)
    await call.answer()


@wizard_router.message(ConfigWizard.refund_id)
async def refund_input(message: Message, state: FSMContext):
    """
    FIXED: Enhanced refund processing - deducts from user balance AND reduces commission
    """
    if message.text and message.text.strip().lower() == "/withdraw_all":
        await state.clear()
        await withdraw_all_handler(message)
        return
    
    if await try_cancel(message, state):
        return

    txn_id = message.text.strip()
    
    # Import required functions
    from services.database import update_user_balance, get_user_data, get_owner_data, save_owner_data
    
    try:
        # 1. Get user current balance BEFORE refund
        user_data = await get_user_data(message.from_user.id)
        current_balance = user_data.get("balance", 0)
        
        if current_balance <= 0:
            await message.answer("🚫 <b>No balance to withdraw!</b>\n\nYour balance is empty.")
            await state.clear()
            return
        
        # 2. Get transaction details to know the refund amount
        # Note: We need to get the actual star amount from the transaction
        try:
            # Try to get star transaction details first
            star_transactions = await message.bot.get_star_transactions(limit=100)
            target_transaction = None
            
            for txn in star_transactions.transactions:
                if hasattr(txn, 'id') and txn.id == txn_id and txn.source is not None:
                    target_transaction = txn
                    break
            
            if not target_transaction:
                await message.answer("🚫 <b>Transaction not found!</b>\n\nInvalid transaction ID or transaction already refunded.")
                await state.clear()
                return
                
            stars_refunded = target_transaction.amount
            
        except Exception:
            # Fallback: execute refund and assume standard amount
            stars_refunded = None
        
        # 3. Execute the star refund
        await message.bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=txn_id
        )
        
        # 4. Calculate coin amount to deduct (reverse of deposit logic)
        if stars_refunded:
            # We know exact amount - calculate corresponding coins  
            owner_data = await get_owner_data()
            commission_rate = owner_data.get("commission_rate", 0.10)
            # User received: stars_refunded * (1 - commission_rate) coins
            coins_to_deduct = int(stars_refunded * (1 - commission_rate))
        else:
            # Fallback: Ask user or estimate (this shouldn't happen in normal flow)
            await message.answer("⚠️ <b>Refund processed but amount unclear.</b>\n\nPlease check your balance manually.")
            await state.clear()
            return
        
        # 5. Validate user has enough coins for this specific withdrawal
        if coins_to_deduct > current_balance:
            coins_to_deduct = current_balance  # Don't overdraw
            
        # 6. DEDUCT only the specific transaction amount
        new_balance = await update_user_balance(message.from_user.id, -coins_to_deduct)
        
        # DEBUG: Log balance update
        print(f"🔍 DEBUG - Withdrawal for user {message.from_user.id}:")
        print(f"   Original balance: {current_balance}")
        print(f"   Stars refunded: {stars_refunded}")
        print(f"   Coins deducted: {coins_to_deduct}")
        print(f"   New balance returned: {new_balance}")
        
        # 7. REDUCE commission balance (since no commission on withdrawals)
        owner_data = await get_owner_data()
        commission_rate = owner_data.get("commission_rate", 0.10)
        
        # Calculate original commission that was taken during this specific deposit
        original_commission = int(stars_refunded * commission_rate)
        
        # Reduce commission balance
        owner_data["commission_balance"] = max(0, owner_data["commission_balance"] - original_commission)
        await save_owner_data(owner_data)
        
        # 8. Success message with details
        await message.answer(
            f"✅ <b>WITHDRAWAL SUCCESSFUL!</b>\n\n"
            f"⭐ <b>Stars returned:</b> <code>{stars_refunded:,}</code>\n"
            f"💰 <b>Coins deducted:</b> <code>{coins_to_deduct:,}</code>\n"
            f"📊 <b>New balance:</b> <code>{new_balance:,}</code> coins\n"
            f"📉 <b>Commission reduced:</b> <code>{original_commission:,}</code> coins\n\n"
            f"🙏 <b>Thank you for using Area 51!</b>"
        )
        
        # CRITICAL FIX: Force fresh user data reload before menu update
        fresh_user_data = await get_user_data(message.from_user.id)
        fresh_balance = fresh_user_data.get("balance", 0)
        
        # DEBUG: Verify fresh data is loaded
        print(f"🔍 DEBUG - Fresh user data reload after withdrawal:")
        print(f"   Fresh balance from file: {fresh_balance}")
        print(f"   Expected balance: {current_balance - coins_to_deduct}")
        
        # Update menu with owner status check
        owner_data = await get_owner_data()
        is_owner = message.from_user.id == owner_data.get("owner_id", message.from_user.id)
        await update_menu(bot=message.bot, chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id, is_owner=is_owner)
        
    except Exception as e:
        await message.answer(f"🚫 Error during refund:\n<code>{e}</code>")
    
    await state.clear()


@wizard_router.callback_query(F.data == "guest_deposit_menu")
async def guest_deposit_menu(call: CallbackQuery, state: FSMContext):
    """
    Переход к шагу пополнения баланса для гостей.
    """
    await call.message.answer("💰 Enter amount for deposit, for example: <code>5000</code>")
    await state.set_state(ConfigWizard.guest_deposit_amount)
    await call.answer()


@wizard_router.message(ConfigWizard.guest_deposit_amount)
async def guest_deposit_amount_input(message: Message, state: FSMContext):
    """
    Обработка суммы для пополнения и отправка счёта на оплату для гостей.
    """
    if await try_cancel(message, state):
        return

    try:
        amount = int(message.text)
        if amount < 1 or amount > 10000:
            raise ValueError
        prices = [LabeledPrice(label=CURRENCY, amount=amount)]
        await message.answer_invoice(
            title="Gift Bot",
            description="Balance top-up",
            prices=prices,
            provider_token="",  # Укажи свой токен
            payload="stars_deposit",
            currency=CURRENCY,
            start_parameter="deposit",
            reply_markup=payment_keyboard(amount=amount),
        )
        await state.clear()
    except ValueError:
        await message.answer("🚫 Enter a number between 1 and 10000. Try again.")


@wizard_router.callback_query(F.data == "guest_refund_menu")
async def guest_refund_menu(call: CallbackQuery, state: FSMContext):
    """
    Переход к возврату звёзд для гостей (по ID транзакции).
    """
    await call.message.answer("🆔 Enter transaction ID for refund:")
    await state.set_state(ConfigWizard.guest_refund_id)
    await call.answer()


@wizard_router.message(ConfigWizard.guest_refund_id)
async def guest_refund_input(message: Message, state: FSMContext):
    """
    Обработка возврата по ID транзакции для гостей.
    """
    if await try_cancel(message, state):
        return

    txn_id = message.text.strip()
    try:
        await message.bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=txn_id
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"🚫 Error during refund:\n<code>{e}</code>")


@wizard_router.message(Command("withdraw_all"))
async def withdraw_all_handler(message: Message):
    """
    Запрос подтверждения на вывод всех звёзд с баланса.
    """
    balance = await refresh_balance(message.bot)
    if balance == 0:
        text = await get_text(message.from_user.id, "no_stars_found")
        await message.answer(text)
        await update_menu(bot=message.bot, chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id)
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes", callback_data="withdraw_all_confirm"),
                InlineKeyboardButton(text="❌ No", callback_data="withdraw_all_cancel"),
            ]
        ]
    )
    await message.answer(
        "⚠️ Are you sure you want to withdraw all stars?",
        reply_markup=keyboard,
    )


@wizard_router.callback_query(lambda c: c.data == "withdraw_all_confirm")
async def withdraw_all_confirmed(call: CallbackQuery):
    """
    FIXED: Complete withdrawal with user balance update and commission reduction
    """
    from services.database import update_user_balance, get_user_data, get_owner_data, save_owner_data
    
    await call.message.edit_text("⏳ Withdrawing stars...")

    async def send_status(msg):
        await call.message.answer(msg)

    await call.answer()

    # Get user balance before withdrawal
    user_data = await get_user_data(call.from_user.id)
    current_balance = user_data.get("balance", 0)
    
    if current_balance <= 0:
        await call.message.answer("🚫 <b>No balance to withdraw!</b>\n\nYour balance is empty.")
        owner_data = await get_owner_data()
        is_owner = call.from_user.id == owner_data.get("owner_id", call.from_user.id)
        await update_menu(bot=call.bot, chat_id=call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id, is_owner=is_owner)
        return

    # Execute star refunds with user's actual balance limit
    # CRITICAL FIX: Convert user balance (coins) to equivalent stars for withdrawal
    from services.database import get_owner_data, save_owner_data
    owner_data = await get_owner_data()
    commission_rate = owner_data.get("commission_rate", 0.10)
    # Calculate equivalent stars: if user has X coins, they can withdraw X / (1 - commission_rate) stars
    max_stars_to_refund = int(current_balance / (1 - commission_rate))
    
    result = await refund_all_star_payments(
        bot=call.bot,
        user_id=call.from_user.id,
        username=call.from_user.username,
        message_func=send_status,
        max_refund_amount=max_stars_to_refund,  # Limit to equivalent stars
    )
    
    if result["count"] > 0:
        # CRITICAL FIX: Deduct user balance (complete withdrawal)
        withdrawal_amount = current_balance
        new_balance = await update_user_balance(call.from_user.id, -withdrawal_amount)
        
        # CRITICAL FIX: Reduce commission balance (no commission on withdrawals)
        owner_data = await get_owner_data()
        commission_rate = owner_data.get("commission_rate", 0.10)
        original_commission = int(withdrawal_amount * commission_rate / (1 - commission_rate))
        owner_data["commission_balance"] = max(0, owner_data["commission_balance"] - original_commission)
        await save_owner_data(owner_data)
        
        # DEBUG: Log complete withdrawal (this one zeros balance intentionally)
        print(f"🔍 DEBUG - Withdraw ALL for user {call.from_user.id}:")
        print(f"   Stars refunded: {result['refunded']}")
        print(f"   Balance deducted: {withdrawal_amount} (COMPLETE WITHDRAWAL)")
        print(f"   New balance: {new_balance}")
        print(f"   Commission reduced: {original_commission}")
        
        msg = f"✅ <b>COMPLETE WITHDRAWAL!</b>\n\n"
        msg += f"⭐ <b>Stars refunded:</b> {result['refunded']}\n"
        msg += f"🔄 <b>Transactions:</b> {result['count']}\n"
        msg += f"💰 <b>Balance cleared:</b> <code>{withdrawal_amount:,}</code> coins\n"
        msg += f"📊 <b>New balance:</b> <code>{new_balance:,}</code> coins\n"
        msg += f"📉 <b>Commission reduced:</b> <code>{original_commission:,}</code> coins"
        
        if result["left"] > 0:
            msg += f"\n💰 Stars remaining: {result['left']}"
            dep = result.get("next_deposit")
            if dep:
                need = dep['amount'] - result['left']
                msg += (
                    f"\n➕ Top up balance by at least ★{need} (or total up to ★{dep['amount']})."
                )
        await call.message.answer(msg)
    else:
        await call.message.answer("🚫 No stars for refund found.")

    # CRITICAL FIX: Force fresh user data reload before menu update
    fresh_user_data = await get_user_data(call.from_user.id)
    fresh_balance = fresh_user_data.get("balance", 0)
    
    # DEBUG: Verify fresh data is loaded
    print(f"🔍 DEBUG - Fresh user data after withdraw_all:")
    print(f"   Fresh balance from file: {fresh_balance}")
    print(f"   Expected balance: 0 (COMPLETE WITHDRAWAL)")
    
    # Update menu with owner status check
    owner_data = await get_owner_data()
    is_owner = call.from_user.id == owner_data.get("owner_id", call.from_user.id)
    await update_menu(bot=call.bot, chat_id=call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id, is_owner=is_owner)


@wizard_router.callback_query(lambda c: c.data == "withdraw_all_cancel")
async def withdraw_all_cancel(call: CallbackQuery):
    """
    Обработка отмены возврата всех звёзд.
    """
    await call.message.edit_text("🚫 Action cancelled.")
    await call.answer()
    await update_menu(bot=call.bot, chat_id=call.message.chat.id, user_id=call.from_user.id, message_id=call.message.message_id)


# ------------- Дополнительные функции ---------------------


async def try_cancel(message: Message, state: FSMContext) -> bool:
    """
    Проверка, ввёл ли пользователь /cancel, и отмена мастера, если да.
    """
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("🚫 Action cancelled.")
        await update_menu(bot=message.bot, chat_id=message.chat.id, user_id=message.from_user.id, message_id=message.message_id)
        return True
    return False


async def get_chat_type(bot: Bot, username: str):
    """
    Определяет тип Telegram-объекта по username для каналов.
    """
    if not username.startswith("@"):
        username = "@" + username
    try:
        chat = await bot.get_chat(username)
        if chat.type == "private":
            if getattr(chat, "is_bot", False):
                return "bot"
            else:
                return "user"
        elif chat.type == "channel":
            return "channel"
        elif chat.type in ("group", "supergroup"):
            return "group"
        else:
            return chat.type  # на всякий случай
    except TelegramAPIError as e:
        return f"error: {e}"
    

def register_wizard_handlers(dp):
    """
    Регистрация wizard_router в диспетчере (Dispatcher).
    """
    dp.include_router(wizard_router)
