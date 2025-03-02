from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from decimal import Decimal

# Создание кошелька
async def create_wallet(db: AsyncSession, initial_balance: float):
    async with db.begin():
        result = await db.execute(
            text("""
                INSERT INTO wallet (balance) 
                VALUES (:balance) 
                RETURNING wallet_uuid, balance
            """),
            {"balance": initial_balance}
        )
        wallet = result.fetchone()
        if wallet is None:
            raise ValueError("Wallet creation failed")
        return {"wallet_uuid": wallet[0], "balance": wallet[1]}



async def process_operation(db: AsyncSession, wallet_uuid: UUID, operation_type: str, amount: float) -> float:
    """
    Выполняет депозит или снятие денег за 1 SQL UPDATE:
      - DEPOSIT: увеличивает balance на :amount
      - WITHDRAW: уменьшает balance на :amount, только если balance >= amount
    Возвращает новое значение баланса.
    """
    amount_dec = Decimal(amount)

    if operation_type == "DEPOSIT":
        query = text("""
            UPDATE wallet
            SET balance = balance + :amount
            WHERE wallet_uuid = :wallet_uuid
            RETURNING balance
        """)
        params = {"amount": amount_dec, "wallet_uuid": str(wallet_uuid)}
    elif operation_type == "WITHDRAW":
        # Аналогично, но "AND balance >= :amount" — условие для списания
        query = text("""
            UPDATE wallet
            SET balance = balance - :amount
            WHERE wallet_uuid = :wallet_uuid
              AND balance >= :amount
            RETURNING balance
        """)
        params = {"amount": amount_dec, "wallet_uuid": str(wallet_uuid)}
    else:
        raise ValueError("Invalid operation type")

    async with db.begin():
        result = await db.execute(query, params)
        row = result.fetchone()

        if not row:
            # Нет возвращённых строк:
            #   - либо кошелёк не найден,
            #   - либо (при WITHDRAW) баланс меньше суммы списания
            raise ValueError("Wallet not found or insufficient funds")

    # row[0] = новое значение баланса
    return float(row[0])
