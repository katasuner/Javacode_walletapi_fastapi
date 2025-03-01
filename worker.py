import asyncio
import json
from redis.asyncio import from_url as redis_from_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from services import process_operation
from decimal import Decimal

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/wallets"
REDIS_URL = "redis://redis:6379"

async def worker_loop():
    # Создаём подключение к Redis
    redis_conn = redis_from_url(REDIS_URL, decode_responses=True)

    # Создаём движок и фабрику сессий к Postgres
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    print("Worker started. Waiting for operations in Redis queue...")

    while True:
        # BLPOP блокирующе ждёт элемент из списка operation_queue
        # Если очередь пуста, он будет ждать.
        op = await redis_conn.blpop("operation_queue")
        # op будет кортеж (queue_name, json_string)
        queue_name, json_str = op
        data = json.loads(json_str)

        wallet_uuid = data["wallet_uuid"]
        operation_type = data["operation_type"]
        amount = Decimal(data["amount"])

        # Теперь делаем UPDATE в БД (process_operation)
        # Открываем сессию:
        async with session_factory() as db_session:
            try:
                new_balance = await process_operation(
                    db_session, wallet_uuid, operation_type, amount
                )
                print(f"Processed {operation_type} on {wallet_uuid}: new balance={new_balance}")
            except Exception as e:
                print(f"Error processing operation: {e}")

async def main():
    await worker_loop()

if __name__ == "__main__":
    asyncio.run(main())
