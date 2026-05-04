from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PaymentMethodEnum(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTO = "crypto"
    DIRECT_DEBIT = "direct_debit"
    VOUCHER = "voucher"


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentCreate(BaseModel):
    payer_name: str
    payer_email: EmailStr
    payer_phone: Optional[str] = None
    payer_country_code: str
    payer_id_type: Optional[str] = None
    payer_id_number: Optional[str] = None

    amount: int  # in smallest currency unit (cents/yen/etc.)
    currency: str
    payment_method: PaymentMethodEnum

    service_code: str
    service_description: str
    fiscal_year: Optional[str] = None
    due_date: Optional[datetime] = None

    extra_data: Optional[Dict[str, Any]] = None
    language: Optional[str] = "en"

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO 4217 code")
        return v.upper()

    @field_validator("payer_country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        if len(v) != 2:
            raise ValueError("Country code must be a 2-letter ISO 3166-1 alpha-2 code")
        return v.upper()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class PaymentResponse(BaseModel):
    id: str
    reference_number: str
    institution_id: str
    payer_name: str
    payer_email: str
    payer_country_code: str
    amount: int
    currency: str
    payment_method: PaymentMethodEnum
    status: PaymentStatusEnum
    service_code: str
    service_description: str
    fiscal_year: Optional[str] = None
    due_date: Optional[datetime] = None
    receipt_number: Optional[str] = None
    receipt_issued_at: Optional[datetime] = None
    provider_transaction_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PaymentResponse]


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatusEnum
    provider_transaction_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    note: Optional[str] = None


class RefundRequest(BaseModel):
    amount: Optional[int] = None  # partial refund if specified, full if None
    reason: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Refund amount must be positive")
        return v
