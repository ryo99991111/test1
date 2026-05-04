from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "Public Payment Service"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    # Database
    database_url: str = "sqlite:///./payment_service.db"

    # Security
    secret_key: str = "change-this-in-production-use-256-bit-random-key"
    api_key_prefix: str = "pps_"
    access_token_expire_minutes: int = 60

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Payment settings
    payment_expiry_minutes: int = 30
    max_amount_per_transaction: int = 100_000_00  # $100,000 in cents
    supported_currencies: List[str] = [
        "USD", "EUR", "GBP", "JPY", "CNY", "KRW", "AUD", "CAD",
        "CHF", "HKD", "SGD", "SEK", "NOK", "DKK", "NZD", "MXN",
        "BRL", "INR", "ZAR", "TRY", "SAR", "AED", "THB", "MYR",
        "IDR", "PHP", "VND", "CZK", "HUF", "PLN", "ILS", "CLP",
        "ARS", "COP", "PEN", "EGP", "NGN", "KES", "GHS", "MAD",
    ]

    # Supported payment providers
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_mode: str = "sandbox"  # sandbox or live

    # CORS
    allowed_origins: List[str] = ["*"]

    # Notification
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@payment.service"

    # Localization
    default_language: str = "en"
    supported_languages: List[str] = [
        "en", "ja", "zh", "ko", "fr", "de", "es", "pt", "ar",
        "hi", "id", "th", "vi", "tr", "ru", "it", "nl", "pl",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
