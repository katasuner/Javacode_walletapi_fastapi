import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from decimal import Decimal
from enum import Enum
from custom_exceptions import (
    WalletNotFoundError,
    InsufficientFundsError,
    WalletCreationError,
    InvalidOperationTypeError,
)


class WalletCreationError(Exception):
    """Ошибка создания кошелька."""
    pass


class InvalidOperationTypeError(Exception):
    """Недопустимый тип операции."""
    pass


# Настройка логгера для модуля
logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Перечисление для типов операций с кошельком."""
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


async def create_wallet(db: AsyncSession, initial_balance: Decimal):
    """
    Создает новый кошелёк с начальным балансом.

    Параметры:
        db (AsyncSession): сессия для работы с базой данных.
        initial_balance (Decimal): начальный баланс кошелька.

    Возвращает:
        dict: словарь с wallet_uuid и balance.

    Исключения:
        WalletCreationError: если создание кошелька не удалось.
    """
    async with db.begin():
        result = await db.execute(
            text(
                """
                INSERT INTO wallet (balance) 
                VALUES (:balance) 
                RETURNING wallet_uuid, balance
                """
            ),
            {"balance": initial_balance}
        )
        wallet = result.fetchone()
        if wallet is None:
            logger.error("Не удалось создать кошелёк с балансом %s", initial_balance)
            raise WalletCreationError("Wallet creation failed")
        logger.info("Создан кошелёк: %s", wallet[0])
        return {"wallet_uuid": wallet[0], "balance": wallet[1]}


async def process_operation(
        db: AsyncSession,
        wallet_uuid: UUID,
        operation_type: OperationType,
        amount: Decimal
) -> Decimal:
    """
    Выполняет депозит или снятие денег за один SQL UPDATE.

    Для операции DEPOSIT:
      - увеличивает баланс на указанную сумму.

    Для операции WITHDRAW:
      - уменьшает баланс на указанную сумму, если средств достаточно.
    """
    # Формируем SQL-запрос и параметры в зависимости от типа операции
    if operation_type == OperationType.DEPOSIT:
        query = text(
            """
            UPDATE wallet
            SET balance = balance + :amount
            WHERE wallet_uuid = :wallet_uuid
            RETURNING balance
            """
        )
        params = {"amount": amount, "wallet_uuid": str(wallet_uuid)}
    elif operation_type == OperationType.WITHDRAW:
        query = text(
            """
            UPDATE wallet
            SET balance = balance - :amount
            WHERE wallet_uuid = :wallet_uuid
              AND balance >= :amount
            RETURNING balance
            """
        )
        params = {"amount": amount, "wallet_uuid": str(wallet_uuid)}
    else:
        raise InvalidOperationTypeError("Invalid operation type")

    async with db.begin():
        result = await db.execute(query, params)
        row = result.fetchone()

        # Если обновление не вернуло строку, проверяем существование кошелька
        if not row:
            check_query = text(
                """
                SELECT wallet_uuid, balance 
                FROM wallet 
                WHERE wallet_uuid = :wallet_uuid
                """
            )
            check_result = await db.execute(check_query, {"wallet_uuid": str(wallet_uuid)})
            wallet_row = check_result.fetchone()
            if wallet_row is None:
                logger.error("Кошелёк %s не найден", wallet_uuid)
                raise WalletNotFoundError("Wallet not found")
            else:
                logger.error("Недостаточно средств на кошельке %s: операция %s, сумма %s",
                             wallet_uuid, operation_type, amount)
                raise InsufficientFundsError("Insufficient funds")

    new_balance = row[0]
    #logger.info("Операция %s на кошельке %s выполнена. Новый баланс: %s",
     #           operation_type, wallet_uuid, new_balance)
    return new_balance
