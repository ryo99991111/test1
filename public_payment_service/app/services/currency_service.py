from typing import Dict, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

# Zero-decimal currencies (amounts are in the whole unit, not cents)
ZERO_DECIMAL_CURRENCIES = {
    "BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW",
    "MGA", "PYG", "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
}

# Currency display metadata
CURRENCY_META: Dict[str, Dict] = {
    "USD": {"symbol": "$", "name": "US Dollar", "decimals": 2},
    "EUR": {"symbol": "€", "name": "Euro", "decimals": 2},
    "GBP": {"symbol": "£", "name": "British Pound", "decimals": 2},
    "JPY": {"symbol": "¥", "name": "Japanese Yen", "decimals": 0},
    "CNY": {"symbol": "¥", "name": "Chinese Yuan", "decimals": 2},
    "KRW": {"symbol": "₩", "name": "Korean Won", "decimals": 0},
    "AUD": {"symbol": "A$", "name": "Australian Dollar", "decimals": 2},
    "CAD": {"symbol": "C$", "name": "Canadian Dollar", "decimals": 2},
    "CHF": {"symbol": "Fr", "name": "Swiss Franc", "decimals": 2},
    "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar", "decimals": 2},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar", "decimals": 2},
    "SEK": {"symbol": "kr", "name": "Swedish Krona", "decimals": 2},
    "NOK": {"symbol": "kr", "name": "Norwegian Krone", "decimals": 2},
    "DKK": {"symbol": "kr", "name": "Danish Krone", "decimals": 2},
    "NZD": {"symbol": "NZ$", "name": "New Zealand Dollar", "decimals": 2},
    "MXN": {"symbol": "MX$", "name": "Mexican Peso", "decimals": 2},
    "BRL": {"symbol": "R$", "name": "Brazilian Real", "decimals": 2},
    "INR": {"symbol": "₹", "name": "Indian Rupee", "decimals": 2},
    "ZAR": {"symbol": "R", "name": "South African Rand", "decimals": 2},
    "TRY": {"symbol": "₺", "name": "Turkish Lira", "decimals": 2},
    "SAR": {"symbol": "﷼", "name": "Saudi Riyal", "decimals": 2},
    "AED": {"symbol": "د.إ", "name": "UAE Dirham", "decimals": 2},
    "THB": {"symbol": "฿", "name": "Thai Baht", "decimals": 2},
    "MYR": {"symbol": "RM", "name": "Malaysian Ringgit", "decimals": 2},
    "IDR": {"symbol": "Rp", "name": "Indonesian Rupiah", "decimals": 2},
    "PHP": {"symbol": "₱", "name": "Philippine Peso", "decimals": 2},
    "VND": {"symbol": "₫", "name": "Vietnamese Dong", "decimals": 0},
    "EGP": {"symbol": "E£", "name": "Egyptian Pound", "decimals": 2},
    "NGN": {"symbol": "₦", "name": "Nigerian Naira", "decimals": 2},
    "KES": {"symbol": "KSh", "name": "Kenyan Shilling", "decimals": 2},
    "GHS": {"symbol": "GH₵", "name": "Ghanaian Cedi", "decimals": 2},
    "MAD": {"symbol": "MAD", "name": "Moroccan Dirham", "decimals": 2},
}


class CurrencyService:
    def is_zero_decimal(self, currency: str) -> bool:
        return currency.upper() in ZERO_DECIMAL_CURRENCIES

    def format_amount(self, amount: int, currency: str) -> str:
        currency = currency.upper()
        meta = CURRENCY_META.get(currency, {"symbol": currency, "decimals": 2})
        symbol = meta["symbol"]
        decimals = meta["decimals"]

        if decimals == 0:
            return f"{symbol}{amount:,}"
        else:
            value = amount / (10 ** decimals)
            return f"{symbol}{value:,.{decimals}f}"

    def get_currency_info(self, currency: str) -> Optional[Dict]:
        return CURRENCY_META.get(currency.upper())

    def validate_currency(self, currency: str) -> bool:
        return currency.upper() in CURRENCY_META

    def to_display_amount(self, amount: int, currency: str) -> float:
        currency = currency.upper()
        meta = CURRENCY_META.get(currency, {"decimals": 2})
        decimals = meta["decimals"]
        if decimals == 0:
            return float(amount)
        return amount / (10 ** decimals)

    def to_smallest_unit(self, display_amount: float, currency: str) -> int:
        currency = currency.upper()
        meta = CURRENCY_META.get(currency, {"decimals": 2})
        decimals = meta["decimals"]
        return int(round(display_amount * (10 ** decimals)))
