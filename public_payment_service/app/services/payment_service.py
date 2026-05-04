import uuid
import hashlib
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Payment, Transaction, AuditLog, Institution
from ..models.payment import PaymentStatus, PaymentMethod
from ..models.transaction import TransactionType
from ..schemas.payment import PaymentCreate, PaymentStatusUpdate, RefundRequest
from ..config import settings
from .currency_service import CurrencyService

logger = logging.getLogger(__name__)
currency_service = CurrencyService()


def _generate_reference_number() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand = secrets.token_hex(4).upper()
    return f"PAY-{ts}-{rand}"


def _generate_receipt_number(payment_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short_id = payment_id[:8].upper()
    return f"RCP-{ts}-{short_id}"


class PaymentService:
    def create_payment(
        self,
        db: Session,
        institution: Institution,
        data: PaymentCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Payment:
        if not currency_service.validate_currency(data.currency):
            raise ValueError(f"Unsupported currency: {data.currency}")

        allowed = [c.strip() for c in institution.supported_currencies.split(",")]
        if data.currency not in allowed:
            raise ValueError(
                f"Currency {data.currency} not supported by this institution"
            )

        if data.amount > settings.max_amount_per_transaction:
            raise ValueError(
                f"Amount exceeds maximum allowed: {settings.max_amount_per_transaction}"
            )

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.payment_expiry_minutes
        )

        payment = Payment(
            reference_number=_generate_reference_number(),
            institution_id=institution.id,
            payer_name=data.payer_name,
            payer_email=data.payer_email,
            payer_phone=data.payer_phone,
            payer_country_code=data.payer_country_code,
            payer_id_type=data.payer_id_type,
            payer_id_number=data.payer_id_number,
            amount=data.amount,
            currency=data.currency,
            payment_method=PaymentMethod(data.payment_method.value),
            status=PaymentStatus.PENDING,
            service_code=data.service_code,
            service_description=data.service_description,
            fiscal_year=data.fiscal_year,
            due_date=data.due_date,
            extra_data=data.extra_data,
            ip_address=ip_address,
            user_agent=user_agent,
            language=data.language or settings.default_language,
            expires_at=expires_at,
        )

        db.add(payment)
        db.flush()

        self._audit(
            db,
            payment_id=payment.id,
            institution_id=institution.id,
            action="payment.created",
            actor=institution.id,
            ip_address=ip_address,
            after_state={"status": PaymentStatus.PENDING, "amount": data.amount, "currency": data.currency},
        )

        db.commit()
        db.refresh(payment)
        return payment

    def update_status(
        self,
        db: Session,
        payment: Payment,
        update: PaymentStatusUpdate,
        actor: str,
        ip_address: Optional[str] = None,
    ) -> Payment:
        before = {"status": payment.status}
        new_status = PaymentStatus(update.status.value)

        self._validate_status_transition(payment.status, new_status)

        payment.status = new_status
        if update.provider_transaction_id:
            payment.provider_transaction_id = update.provider_transaction_id
        if update.provider_response:
            payment.provider_response = update.provider_response

        if new_status == PaymentStatus.COMPLETED:
            payment.receipt_number = _generate_receipt_number(payment.id)
            payment.receipt_issued_at = datetime.now(timezone.utc)

            transaction = Transaction(
                payment_id=payment.id,
                transaction_type=TransactionType.CHARGE,
                amount=payment.amount,
                currency=payment.currency,
                fee_amount=0,
                net_amount=payment.amount,
                provider_transaction_id=update.provider_transaction_id,
                provider_response=update.provider_response,
                note=update.note,
            )
            db.add(transaction)

        self._audit(
            db,
            payment_id=payment.id,
            institution_id=payment.institution_id,
            action=f"payment.{new_status.value}",
            actor=actor,
            ip_address=ip_address,
            before_state=before,
            after_state={"status": new_status, "provider_transaction_id": update.provider_transaction_id},
            details=update.note,
        )

        db.commit()
        db.refresh(payment)
        return payment

    def process_refund(
        self,
        db: Session,
        payment: Payment,
        refund: RefundRequest,
        actor: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[Payment, Transaction]:
        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError("Only completed payments can be refunded")

        refund_amount = refund.amount if refund.amount else payment.amount
        if refund_amount > payment.amount:
            raise ValueError("Refund amount exceeds original payment amount")

        is_partial = refund_amount < payment.amount
        transaction_type = TransactionType.PARTIAL_REFUND if is_partial else TransactionType.REFUND

        transaction = Transaction(
            payment_id=payment.id,
            transaction_type=transaction_type,
            amount=refund_amount,
            currency=payment.currency,
            fee_amount=0,
            net_amount=refund_amount,
            note=refund.reason,
        )
        db.add(transaction)

        if not is_partial:
            payment.status = PaymentStatus.REFUNDED

        self._audit(
            db,
            payment_id=payment.id,
            institution_id=payment.institution_id,
            action="payment.refunded",
            actor=actor,
            ip_address=ip_address,
            before_state={"status": payment.status},
            after_state={"refund_amount": refund_amount, "is_partial": is_partial},
            details=refund.reason,
        )

        db.commit()
        db.refresh(payment)
        db.refresh(transaction)
        return payment, transaction

    def expire_pending_payments(self, db: Session) -> int:
        now = datetime.now(timezone.utc)
        expired = (
            db.query(Payment)
            .filter(
                Payment.status == PaymentStatus.PENDING,
                Payment.expires_at < now,
            )
            .all()
        )
        for p in expired:
            p.status = PaymentStatus.EXPIRED
            self._audit(
                db,
                payment_id=p.id,
                institution_id=p.institution_id,
                action="payment.expired",
                actor="system",
            )
        db.commit()
        return len(expired)

    def _validate_status_transition(self, current: PaymentStatus, new: PaymentStatus) -> None:
        allowed_transitions = {
            PaymentStatus.PENDING: {PaymentStatus.PROCESSING, PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.EXPIRED},
            PaymentStatus.PROCESSING: {PaymentStatus.COMPLETED, PaymentStatus.FAILED},
            PaymentStatus.COMPLETED: {PaymentStatus.REFUNDED},
            PaymentStatus.FAILED: set(),
            PaymentStatus.REFUNDED: set(),
            PaymentStatus.CANCELLED: set(),
            PaymentStatus.EXPIRED: set(),
        }
        if new not in allowed_transitions.get(current, set()):
            raise ValueError(
                f"Cannot transition from {current.value} to {new.value}"
            )

    def _audit(
        self,
        db: Session,
        action: str,
        payment_id: Optional[str] = None,
        institution_id: Optional[str] = None,
        actor: Optional[str] = None,
        ip_address: Optional[str] = None,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        details: Optional[str] = None,
    ) -> None:
        log = AuditLog(
            payment_id=payment_id,
            institution_id=institution_id,
            action=action,
            actor=actor,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
            details=details,
        )
        db.add(log)
