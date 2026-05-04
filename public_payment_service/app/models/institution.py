from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from ..database import Base


class InstitutionType(str, enum.Enum):
    GOVERNMENT = "government"
    MUNICIPALITY = "municipality"
    PUBLIC_UTILITY = "public_utility"
    EDUCATIONAL = "educational"
    HEALTHCARE = "healthcare"
    OTHER = "other"


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    name_local = Column(String(255), nullable=True)
    institution_type = Column(SAEnum(InstitutionType), nullable=False)
    country_code = Column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    region = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    supported_currencies = Column(Text, nullable=False, default="USD")  # comma-separated ISO 4217
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    payments = relationship("Payment", back_populates="institution")
