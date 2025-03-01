from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from database import get_db
from models import Wallet
from services import process_operation, create_wallet

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
async def create_wallet_route(request: WalletCreateRequest, db: AsyncSession = Depends(get_db)):
    wallet = await create_wallet(db, request.initial_balance)
    return {"wallet_uuid": str(wallet["wallet_uuid"]), "balance": wallet["balance"]}  # Используем wallet_uuid


# Получение баланса по wallet_uuid
@router.get("/{wallet_uuid}", response_model=dict, summary="Получение баланса")
async def get_wallet_balance(wallet_uuid: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Wallet).filter_by(wallet_uuid=wallet_uuid))
    wallet = result.scalars().first()

    if not wallet:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Wallet not found")

    return {"wallet_uuid": str(wallet.wallet_uuid), "balance": wallet.balance}


@router.post("/{wallet_uuid}/operation", response_model=dict, summary="Депозит/Снятие средств")
async def wallet_operation(wallet_uuid: UUID, request: WalletOperationRequest, db: AsyncSession = Depends(get_db)):
    try:
        balance = await process_operation(db, wallet_uuid, request.operationType, request.amount)
        return {"wallet_uuid": str(wallet_uuid), "new_balance": balance}
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(e))
