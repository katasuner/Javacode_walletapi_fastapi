import os
import asyncio
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from models import Base, Wallet
from services import create_wallet, process_operation, OperationType
from custom_exceptions import WalletNotFoundError, InsufficientFundsError, WalletCreationError, InvalidOperationTypeError

# Читаем URL тестовой базы из переменной окружения, если она задана.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://user:password@localhost/test_wallets")

# Создаём движок для тестовой базы
@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    # Создаём все таблицы перед тестами
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Удаляем все таблицы после завершения тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

# Фабрика сессий для тестов
@pytest.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)

# Фикстура для отдельной сессии с откатом транзакций после каждого теста
@pytest.fixture
async def db_session(session_factory) -> AsyncSession:
    async with session_factory() as session:
        async with session.begin():
            yield session
            # Все изменения откатываются после выхода из контекста

@pytest.mark.asyncio
async def test_create_wallet(db_session: AsyncSession):
    initial_balance = Decimal("100.00")
    wallet_data = await create_wallet(db_session, initial_balance)
    assert wallet_data["balance"] == initial_balance
    assert uuid.UUID(str(wallet_data["wallet_uuid"]))

@pytest.mark.asyncio
async def test_deposit_operation(db_session: AsyncSession):
    initial_balance = Decimal("50.00")
    wallet_data = await create_wallet(db_session, initial_balance)
    wallet_uuid = wallet_data["wallet_uuid"]

    # Выполняем депозит 25.00
    new_balance = await process_operation(db_session, wallet_uuid, OperationType.DEPOSIT, Decimal("25.00"))
    assert new_balance == initial_balance + Decimal("25.00")

@pytest.mark.asyncio
async def test_withdraw_operation(db_session: AsyncSession):
    initial_balance = Decimal("100.00")
    wallet_data = await create_wallet(db_session, initial_balance)
    wallet_uuid = wallet_data["wallet_uuid"]

    # Выполняем успешное снятие средств 40.00
    new_balance = await process_operation(db_session, wallet_uuid, OperationType.WITHDRAW, Decimal("40.00"))
    assert new_balance == initial_balance - Decimal("40.00")

@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(db_session: AsyncSession):
    initial_balance = Decimal("30.00")
    wallet_data = await create_wallet(db_session, initial_balance)
    wallet_uuid = wallet_data["wallet_uuid"]

    # Попытка снятия суммы больше, чем имеется
    with pytest.raises(InsufficientFundsError):
        await process_operation(db_session, wallet_uuid, OperationType.WITHDRAW, Decimal("50.00"))

@pytest.mark.asyncio
async def test_wallet_not_found(db_session: AsyncSession):
    fake_wallet_uuid = uuid.uuid4()
    with pytest.raises(WalletNotFoundError):
        await process_operation(db_session, fake_wallet_uuid, OperationType.DEPOSIT, Decimal("10.00"))
