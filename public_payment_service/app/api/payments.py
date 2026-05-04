from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Institution, Payment
from ..models.payment import PaymentStatus
from ..schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    PaymentStatusUpdate,
    RefundRequest,
)
from ..security.auth import get_current_institution
from ..services.payment_service import PaymentService
from ..services.notification_service import NotificationService

router = APIRouter()
payment_service = PaymentService()
notification_service = NotificationService()


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    data: PaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    institution: Institution = Depends(get_current_institution),
):
    """Create a new payment request."""
    try:
        payment = payment_service.create_payment(
            db=db,
            institution=institution,
            data=data,
            ip_address=_get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    notification_service.send_payment_notification(payment, "payment_created", data.language)
    return payment


@router.get("", response_model=PaymentListResponse)
def list_payments(
    db: Session = Depends(get_db),
    institution: Institution = Depends(get_current_institution),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[PaymentStatus] = None,
    currency: Optional[str] = None,
    service_code: Optional[str] = None,
):
    """List payments for the authenticated institution."""
    query = db.query(Payment).filter(Payment.institution_id == institution.id)

    if status:
        query = query.filter(Payment.status == status)
    if currency:
        query = query.filter(Payment.currency == currency.upper())
    if service_code:
        query = query.filter(Payment.service_code == service_code)

    total = query.count()
    items = (
        query.order_by(Payment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaymentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    institution: Institution = Depends(get_current_institution),
):
    """Get a specific payment by ID."""
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.institution_id == institution.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.get("/ref/{reference_number}", response_model=PaymentResponse)
def get_payment_by_reference(
    reference_number: str,
    db: Session = Depends(get_db),
    institution: Institution = Depends(get_current_institution),
):
    """Get a payment by its reference number."""
    payment = (
        db.query(Payment)
        .filter(
            Payment.reference_number == reference_number,
            Payment.institution_id == institution.id,
        )
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.patch("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(
    payment_id: str,
    update: PaymentStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    institution: Institution = Depends(get_current_institution),
):
    """Update payment status (used by payment provider webhooks/callbacks)."""
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.institution_id == institution.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    try:
        payment = payment_service.update_status(
            db=db,
            payment=payment,
            update=update,
            actor=institution.id,
            ip_address=_get_client_ip(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    event = f"payment_{update.status.value}"
    notification_service.send_payment_notification(payment, event)
    return payment


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: str,
    refund: RefundRequest,
    request: Request,
    db: Session = Depends(get_db),
    institution: Institution = Depends(get_current_institution),
):
    """Refund a completed payment (full or partial)."""
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.institution_id == institution.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    try:
        payment, _ = payment_service.process_refund(
            db=db,
            payment=payment,
            refund=refund,
            actor=institution.id,
            ip_address=_get_client_ip(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    notification_service.send_payment_notification(payment, "payment_refunded")
    return payment


@router.delete("/{payment_id}", response_model=PaymentResponse)
def cancel_payment(
    payment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    institution: Institution = Depends(get_current_institution),
):
    """Cancel a pending payment."""
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.institution_id == institution.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    try:
        update = PaymentStatusUpdate(status="cancelled")
        payment = payment_service.update_status(
            db=db,
            payment=payment,
            update=update,
            actor=institution.id,
            ip_address=_get_client_ip(request),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return payment
