from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=True)
    institution_id = Column(String(36), nullable=True)

    action = Column(String(100), nullable=False)       # e.g. "payment.created", "payment.completed"
    actor = Column(String(255), nullable=True)          # API key id or system
    ip_address = Column(String(45), nullable=True)

    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payment = relationship("Payment", back_populates="audit_logs")
