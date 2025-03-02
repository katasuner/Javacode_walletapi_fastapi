import json
from typing import Annotated

import redis.asyncio as aioredis
from redis.asyncio import Redis
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from database import get_db
from models import Wallet
from services import create_wallet

REDIS_URL = "redis://redis:6379"

# Глобальный клиент, создаётся один раз при первом запросе
redis_client: aioredis.Redis | None = None

async def get_redis() -> Redis:
    global redis_client
    if redis_client is None:
        # Подключаемся к Redis асинхронно
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

router = APIRouter(
    prefix="/api/v1/wallets",
    tags=["wallets"]
)

# Схемы для запросов
class WalletCreateRequest(BaseModel):
    initial_balance: float = Field(..., ge=0, description="Начальный баланс кошелька")

class WalletOperationRequest(BaseModel):
    operationType: str = Field(..., pattern="^(DEPOSIT|WITHDRAW)$", description="Тип операции: DEPOSIT или WITHDRAW")
    amount: float = Field(..., gt=0, description="Сумма операции")


@router.post("/", response_model=dict, summary="Создание кошелька")
async def create_wallet_route(
    request: WalletCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    wallet = await create_wallet(db, request.initial_balance)
    return {
        "wallet_uuid": str(wallet["wallet_uuid"]),
        "balance": wallet["balance"],
    }


@router.get("/{wallet_uuid}", response_model=dict, summary="Получение баланса")
async def get_wallet_balance(wallet_uuid: UUID, db: AsyncSession = Depends(get_db)):
    redis_conn = await get_redis()
    cache_key = f"wallet:{wallet_uuid}"

    #  Проверяем кэш Redis
    cached_balance = await redis_conn.get(cache_key)
    if cached_balance is not None:
        return {"wallet_uuid": str(wallet_uuid), "balance": float(cached_balance)}

    #  Если нет в кэше — запрос в БД
    result = await db.execute(select(Wallet).filter_by(wallet_uuid=wallet_uuid))
    wallet = result.scalars().first()
    if not wallet:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Wallet not found")

    #  Кэшируем баланс в Redis на 60 секунд
    await redis_conn.setex(cache_key, 60, str(wallet.balance))

    return {"wallet_uuid": str(wallet.wallet_uuid), "balance": wallet.balance}


@router.post("/{wallet_uuid}/operation", response_model=dict, summary="Депозит/Снятие средств (асинхронная очередь)")
async def wallet_operation(
    wallet_uuid: UUID,
    request: WalletOperationRequest,
    redis_conn: Annotated[Redis, Depends(get_redis)],
):
    """
    Вместо прямого UPDATE в БД - складываем операцию в очередь Redis.
    Фоновый воркер прочитает эту операцию и выполнит process_operation.
    """
    # Формируем JSON-объект с операцией
    op_data = {
        "wallet_uuid": str(wallet_uuid),
        "operation_type": request.operationType,
        "amount": request.amount,
    }
    # Кладём в список (очередь) под названием "operation_queue"
    await redis_conn.rpush("operation_queue", json.dumps(op_data))

    # Возвращаем быстрый ответ
    return {"status": "queued", "detail": "Operation is queued for async processing"}
