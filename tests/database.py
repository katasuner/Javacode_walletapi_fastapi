# tests/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Тестовая база данных, которая будет использоваться только для тестов
DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/test_wallets")

# Создание асинхронного двигателя базы данных
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сессий для тестов
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

# Базовый класс для моделей в тестах
class Base(DeclarativeBase):
    pass

# Функция для получения сессии
async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e

# Инициализация базы данных для тестов (создание таблиц)
async def init_test_db():
    # Создание всех таблиц, если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
