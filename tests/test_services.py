# tests/test_services.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from services import create_wallet, process_operation, OperationType
from custom_exceptions import WalletNotFoundError, InsufficientFundsError, InvalidOperationTypeError
from tests.database import async_session_factory, init_test_db

# Фикстура для сессии базы данных для тестов
@pytest.fixture
async def db_session() -> AsyncSession:
    # Инициализация базы данных для тестов
    await init_test_db()  # Создаём таблицы для тестов
    async with async_session_factory() as session:
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_create_wallet(db_session: AsyncSession):
    initial_balance = Decimal("100.00")
    wallet = await create_wallet(db_session, initial_balance)
    assert "wallet_uuid" in wallet
    assert wallet["balance"] == initial_balance

# Тест на операцию депозита
@pytest.mark.asyncio
async def test_deposit(db_session: AsyncSession):
    # Создаем кошелек с начальным балансом
    wallet = await create_wallet(db_session, Decimal("50.00"))

    # Выполняем депозит
    new_balance = await process_operation(db_session, wallet["wallet_uuid"], OperationType.DEPOSIT, Decimal("25.00"))

    # Проверяем, что новый баланс правильный
    assert new_balance == Decimal("75.00")

# Тест на успешное снятие средств
@pytest.mark.asyncio
async def test_withdraw_success(db_session: AsyncSession):
    # Создаем кошелек с балансом 100.00
    wallet = await create_wallet(db_session, Decimal("100.00"))

    # Выполняем снятие
    new_balance = await process_operation(db_session, wallet["wallet_uuid"], OperationType.WITHDRAW, Decimal("40.00"))

    # Проверяем, что новый баланс правильный
    assert new_balance == Decimal("60.00")

# Тест на попытку снять средства, которых нет на кошельке
@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(db_session: AsyncSession):
    # Создаем кошелек с балансом 30.00
    wallet = await create_wallet(db_session, Decimal("30.00"))

    # Проверяем, что будет выброшено исключение при попытке снять больше средств
    with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
        await process_operation(db_session, wallet["wallet_uuid"], OperationType.WITHDRAW, Decimal("50.00"))

# Тест на неверный тип операции
@pytest.mark.asyncio
async def test_invalid_operation_type(db_session: AsyncSession):
    # Создаем кошелек с балансом 100.00
    wallet = await create_wallet(db_session, Decimal("100.00"))

    # Проверяем, что будет выброшено исключение для неправильного типа операции
    with pytest.raises(InvalidOperationTypeError, match="Invalid operation type"):
        await process_operation(db_session, wallet["wallet_uuid"], "INVALID", Decimal("10.00"))
