import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from ..config import settings
from ..models.payment import Payment

logger = logging.getLogger(__name__)

TEMPLATES = {
    "en": {
        "payment_created": {
            "subject": "Payment Confirmation - {reference_number}",
            "body": (
                "Dear {payer_name},\n\n"
                "Your payment has been received.\n\n"
                "Reference: {reference_number}\n"
                "Amount: {amount} {currency}\n"
                "Service: {service_description}\n"
                "Status: {status}\n\n"
                "Thank you."
            ),
        },
        "payment_completed": {
            "subject": "Payment Receipt - {receipt_number}",
            "body": (
                "Dear {payer_name},\n\n"
                "Your payment has been successfully processed.\n\n"
                "Receipt: {receipt_number}\n"
                "Reference: {reference_number}\n"
                "Amount: {amount} {currency}\n"
                "Service: {service_description}\n\n"
                "Thank you."
            ),
        },
        "payment_failed": {
            "subject": "Payment Failed - {reference_number}",
            "body": (
                "Dear {payer_name},\n\n"
                "Unfortunately, your payment could not be processed.\n\n"
                "Reference: {reference_number}\n"
                "Amount: {amount} {currency}\n\n"
                "Please try again or contact support."
            ),
        },
    },
    "ja": {
        "payment_created": {
            "subject": "お支払い確認 - {reference_number}",
            "body": (
                "{payer_name} 様\n\n"
                "お支払いを受け付けました。\n\n"
                "参照番号: {reference_number}\n"
                "金額: {amount} {currency}\n"
                "サービス: {service_description}\n"
                "状態: {status}\n\n"
                "ありがとうございます。"
            ),
        },
        "payment_completed": {
            "subject": "領収書 - {receipt_number}",
            "body": (
                "{payer_name} 様\n\n"
                "お支払いが正常に処理されました。\n\n"
                "領収書番号: {receipt_number}\n"
                "参照番号: {reference_number}\n"
                "金額: {amount} {currency}\n"
                "サービス: {service_description}\n\n"
                "ありがとうございます。"
            ),
        },
        "payment_failed": {
            "subject": "お支払いに失敗しました - {reference_number}",
            "body": (
                "{payer_name} 様\n\n"
                "お支払いを処理できませんでした。\n\n"
                "参照番号: {reference_number}\n"
                "金額: {amount} {currency}\n\n"
                "再度お試しいただくか、サポートまでお問い合わせください。"
            ),
        },
    },
}


class NotificationService:
    def send_payment_notification(
        self, payment: Payment, event: str, language: Optional[str] = None
    ) -> bool:
        lang = language or payment.language or settings.default_language
        if lang not in TEMPLATES:
            lang = "en"

        template = TEMPLATES[lang].get(event)
        if not template:
            logger.warning(f"No template found for event={event} lang={lang}")
            return False

        context = {
            "payer_name": payment.payer_name,
            "reference_number": payment.reference_number,
            "receipt_number": payment.receipt_number or "",
            "amount": payment.amount,
            "currency": payment.currency,
            "service_description": payment.service_description,
            "status": payment.status,
        }

        subject = template["subject"].format(**context)
        body = template["body"].format(**context)

        return self._send_email(payment.payer_email, subject, body)

    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        if not settings.smtp_host:
            logger.info(f"[DRY RUN] Email to {to_email}: {subject}")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = settings.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.from_email, to_email, msg.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
