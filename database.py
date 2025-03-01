from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Читаем параметры БД из переменных среды
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/wallets")

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)

# Создаем фабрику сессий
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# Зависимость для FastAPI (получение сессии БД)
async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
