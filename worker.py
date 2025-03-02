import asyncio
import json
import logging
from decimal import Decimal

from redis.asyncio import from_url as redis_from_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from services import process_operation, OperationType

# Настройка базового уровня логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы подключения к базе данных и Redis
DATABASE_URL = "postgresql+asyncpg://user:password@pgbouncer:6432/wallets"
REDIS_URL = "redis://redis:6379"

async def worker_loop():
    """
    Основной цикл воркера, который обрабатывает операции из очереди Redis.
    В цикле происходит:
      1. Ожидание поступления нового элемента в очередь "operation_queue".
      2. Парсинг полученного JSON-сообщения с данными операции.
      3. Преобразование строки операции в Enum, а суммы в Decimal.
      4. Выполнение операции в базе данных через функцию process_operation.
      5. Логирование ошибок, если операция завершилась неудачно.
    """
    # Создаём асинхронное подключение к Redis
    redis_conn = redis_from_url(REDIS_URL, decode_responses=True)

    # Создаём движок SQLAlchemy с увеличенным пулом соединений для повышения производительности
    engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=10)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    logger.info("Worker started. Waiting for operations in Redis queue...")

    while True:
        # Ожидание нового элемента в очереди (блокирующий вызов)
        op = await redis_conn.blpop("operation_queue")
        # op представляет собой кортеж (имя очереди, JSON-строка)
        _, json_str = op

        # Десериализуем данные операции из JSON
        data = json.loads(json_str)
        wallet_uuid = data["wallet_uuid"]

        # Преобразуем строковое представление типа операции в OperationType Enum
        try:
            operation_type = OperationType(data["operation_type"])
        except ValueError:
            logger.error("Invalid operation type: %s", data["operation_type"])
            continue  # Пропускаем операцию, если тип некорректен

        # Преобразуем сумму в Decimal для точных расчётов
        amount = Decimal(data["amount"])

        # Выполняем операцию в базе данных с использованием сессии
        async with session_factory() as db_session:
            try:
                await process_operation(db_session, wallet_uuid, operation_type, amount)
            except Exception as e:
                # Логируем ошибку с полной информацией для отладки
                logger.error("Error processing operation for wallet %s: %s", wallet_uuid, e, exc_info=True)

async def main():
    """Запускает основной цикл воркера."""
    await worker_loop()

if __name__ == "__main__":
    asyncio.run(main())
