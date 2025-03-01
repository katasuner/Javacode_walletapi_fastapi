from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from uuid import UUID
from decimal import Decimal

# Создание кошелька (оставляем ORM)
async def create_wallet(db: AsyncSession, initial_balance: float):
    async with db.begin():
        result = await db.execute(
            text("INSERT INTO wallet (balance) VALUES (:balance) RETURNING wallet_uuid, balance"),
            {"balance": initial_balance}
        )
        wallet = result.fetchone()
        if wallet is None:
            raise ValueError("Wallet creation failed")
        return {"wallet_uuid": wallet[0], "balance": wallet[1]}

# Операции с кошельком (DEPOSIT / WITHDRAW)
async def process_operation(db: AsyncSession, wallet_uuid: UUID, operation_type: str, amount: float) -> float:
    async with db.begin():
        # Получаем текущий баланс с блокировкой строки
        result = await db.execute(
            text("SELECT balance FROM wallet WHERE wallet_uuid = :wallet_uuid FOR UPDATE"),
            {"wallet_uuid": str(wallet_uuid)}
        )
        row = result.fetchone()

        if not row:
            raise ValueError("Wallet not found")

        current_balance = row[0]

        # Приводим amount к Decimal, чтобы не возникала ошибка
        amount = Decimal(amount)

        # Проверяем операцию
        if operation_type == "WITHDRAW":
            if current_balance < amount:
                raise ValueError("Insufficient funds")
            new_balance = current_balance - amount
        elif operation_type == "DEPOSIT":
            new_balance = current_balance + amount
        else:
            raise ValueError("Invalid operation type")

        # Обновляем баланс
        await db.execute(
            text("UPDATE wallet SET balance = :new_balance WHERE wallet_uuid = :wallet_uuid"),
            {"new_balance": new_balance, "wallet_uuid": str(wallet_uuid)}
        )

    return new_balance