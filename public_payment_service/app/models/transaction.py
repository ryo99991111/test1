from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from ..database import Base


class TransactionType(str, enum.Enum):
    CHARGE = "charge"
    REFUND = "refund"
    PARTIAL_REFUND = "partial_refund"
    VOID = "void"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    transaction_type = Column(SAEnum(TransactionType), nullable=False)

    amount = Column(Integer, nullable=False)       # in smallest currency unit
    currency = Column(String(3), nullable=False)
    fee_amount = Column(Integer, default=0)        # processing fee
    net_amount = Column(Integer, nullable=False)   # amount after fees

    provider_transaction_id = Column(String(255), nullable=True)
    provider_response = Column(JSON, nullable=True)

    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payment = relationship("Payment", back_populates="transactions")
