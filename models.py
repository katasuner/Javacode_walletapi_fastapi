from sqlalchemy import Column, Numeric, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallet"

    id = Column(Numeric, primary_key=True, autoincrement=True)
    wallet_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=func.gen_random_uuid())
    balance = Column(Numeric(20, 2), nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="wallet")


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Numeric, primary_key=True, autoincrement=True)
    wallet_id = Column(Numeric, ForeignKey("wallet.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(8), nullable=False)
    amount = Column(Numeric(20, 2), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    wallet = relationship("Wallet", back_populates="transactions")
