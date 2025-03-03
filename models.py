from sqlalchemy import Column, Numeric, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallet"

    id = Column(Numeric, primary_key=True, autoincrement=True)
    wallet_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=func.gen_random_uuid())
    balance = Column(Numeric(20, 2), nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())



