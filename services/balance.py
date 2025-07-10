# --- Стандартные библиотеки ---
from itertools import combinations
import os

# --- Внутренние модули ---
from services.database import get_owner_data, save_owner_data

async def get_stars_balance(bot) -> int:
    """
    Получает суммарный баланс звёзд по всем транзакциям пользователя через API бота.
    """
    offset = 0
    limit = 100
    balance = 0

    while True:
        get_transactions = await bot.get_star_transactions(offset=offset, limit=limit)
        transactions = get_transactions.transactions

        if not transactions:
            break

        for transaction in transactions:
            source = transaction.source
            amount = transaction.amount
            if source is not None:
                balance += amount
            else:
                balance -= amount

        offset += limit

    return balance


async def refresh_balance(bot) -> int:
    """
    Обновляет и сохраняет баланс звёзд в данных владельца, возвращает актуальное значение.
    """
    balance = await get_stars_balance(bot)
    owner_data = await get_owner_data()
    owner_data["stars_balance"] = balance
    await save_owner_data(owner_data)
    return balance


async def change_balance(delta: int) -> int:
    """
    Изменяет баланс звёзд в данных владельца на указанное значение delta, не допуская отрицательных значений.
    """
    owner_data = await get_owner_data()
    current_balance = owner_data.get("stars_balance", 0)
    new_balance = max(0, current_balance + delta)
    owner_data["stars_balance"] = new_balance
    await save_owner_data(owner_data)
    return new_balance


async def refund_all_star_payments(bot, username, user_id, message_func=None, max_refund_amount=None):
    """
    FIXED: Возвращает звёзды только по депозитам без возврата, совершённым указанным username.
    Подбирает оптимальную комбинацию для вывода максимально возможной суммы.
    При необходимости сообщает пользователю о дальнейших действиях.
    
    max_refund_amount: Максимальная сумма для возврата (рекомендуется передавать баланс пользователя)
    """
    # CRITICAL FIX: Use user's balance instead of bot's total balance
    if max_refund_amount is not None:
        balance = max_refund_amount  # Use user's specific balance
    else:
        balance = await refresh_balance(bot)  # Fallback to bot balance (legacy)
    
    if balance <= 0:
        return {"refunded": 0, "count": 0, "txn_ids": [], "left": 0}

    # Получаем все транзакции
    offset = 0
    limit = 100
    all_txns = []
    while True:
        res = await bot.get_star_transactions(offset=offset, limit=limit)
        txns = res.transactions
        if not txns:
            break
        all_txns.extend(txns)
        offset += limit

    # Filter deposits without refund и only with needed username
    deposits = [
        t for t in all_txns
        if t.source is not None
        and getattr(t.source, "user", None)
        and getattr(t.source.user, "username", None) == username
    ]
    refunded_ids = {t.id for t in all_txns if t.source is None}
    unrefunded_deposits = [t for t in deposits if t.id not in refunded_ids]

    n = len(unrefunded_deposits)
    best_combo = []
    best_sum = 0

    # Ищем идеальную комбинацию или greedy
    if n <= 18:
        for r in range(1, n+1):
            for combo in combinations(unrefunded_deposits, r):
                s = sum(t.amount for t in combo)
                if s <= balance and s > best_sum:
                    best_combo = combo
                    best_sum = s
                if best_sum == balance:
                    break
            if best_sum == balance:
                break
    else:
        unrefunded_deposits.sort(key=lambda t: t.amount, reverse=True)
        curr_sum = 0
        best_combo = []
        for t in unrefunded_deposits:
            if curr_sum + t.amount <= balance:
                best_combo.append(t)
                curr_sum += t.amount
        best_sum = curr_sum

    if not best_combo:
        return {"refunded": 0, "count": 0, "txn_ids": [], "left": balance}

    # Делаем возвраты только по выбранным транзакциям
    total_refunded = 0
    refund_ids = []
    for txn in best_combo:
        txn_id = getattr(txn, "id", None)
        if not txn_id:
            continue
        try:
            await bot.refund_star_payment(
                user_id=user_id,
                telegram_payment_charge_id=txn_id
            )
            total_refunded += txn.amount
            refund_ids.append(txn_id)
        except Exception as e:
            if message_func:
                await message_func(f"🚫 Ошибка при возврате ★{txn.amount}")

    left = balance - best_sum

    # Находим транзакцию, которой хватит чтобы покрыть остаток
    # Берём минимальную сумму среди транзакций, где amount > min_needed
    def find_next_possible_deposit(unused_deposits, min_needed):
        bigger = [t for t in unused_deposits if t.amount > min_needed]
        if not bigger:
            return None
        best = min(bigger, key=lambda t: t.amount)
        return {"amount": best.amount, "id": getattr(best, "id", None)}

    unused_deposits = [t for t in unrefunded_deposits if t not in best_combo]
    next_possible = None
    if left > 0 and unused_deposits:
        next_possible = find_next_possible_deposit(unused_deposits, left)

    return {
        "refunded": total_refunded,
        "count": len(refund_ids),
        "txn_ids": refund_ids,
        "left": left,
        "next_deposit": next_possible
    }
