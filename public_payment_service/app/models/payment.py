from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from ..database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTO = "crypto"
    DIRECT_DEBIT = "direct_debit"
    VOUCHER = "voucher"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_number = Column(String(50), unique=True, nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)

    # Payer information
    payer_name = Column(String(255), nullable=False)
    payer_email = Column(String(255), nullable=False)
    payer_phone = Column(String(50), nullable=True)
    payer_country_code = Column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    payer_id_type = Column(String(50), nullable=True)   # passport, national_id, etc.
    payer_id_number = Column(String(100), nullable=True)

    # Payment details
    amount = Column(Integer, nullable=False)           # amount in smallest unit (cents)
    currency = Column(String(3), nullable=False)       # ISO 4217
    payment_method = Column(SAEnum(PaymentMethod), nullable=False)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    # Service details
    service_code = Column(String(100), nullable=False)  # e.g. "TAX_INCOME", "FEE_PERMIT"
    service_description = Column(Text, nullable=False)
    fiscal_year = Column(String(10), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)

    # Provider details
    provider_name = Column(String(100), nullable=True)    # stripe, paypal, etc.
    provider_transaction_id = Column(String(255), nullable=True)
    provider_response = Column(JSON, nullable=True)

    # Receipt
    receipt_number = Column(String(100), nullable=True)
    receipt_issued_at = Column(DateTime(timezone=True), nullable=True)

    # Extra data
    extra_data = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    language = Column(String(10), nullable=True, default="en")

    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    institution = relationship("Institution", back_populates="payments")
    transactions = relationship("Transaction", back_populates="payment")
    audit_logs = relationship("AuditLog", back_populates="payment")
