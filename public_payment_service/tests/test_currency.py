import pytest
from app.services.currency_service import CurrencyService


@pytest.fixture
def svc():
    return CurrencyService()


def test_format_usd(svc):
    assert svc.format_amount(1050, "USD") == "$10.50"


def test_format_jpy(svc):
    assert svc.format_amount(1050, "JPY") == "¥1,050"


def test_format_eur(svc):
    assert svc.format_amount(9999, "EUR") == "€99.99"


def test_format_krw(svc):
    assert svc.format_amount(10000, "KRW") == "₩10,000"


def test_is_zero_decimal_jpy(svc):
    assert svc.is_zero_decimal("JPY") is True


def test_is_zero_decimal_usd(svc):
    assert svc.is_zero_decimal("USD") is False


def test_validate_currency_valid(svc):
    assert svc.validate_currency("USD") is True
    assert svc.validate_currency("EUR") is True
    assert svc.validate_currency("JPY") is True


def test_validate_currency_invalid(svc):
    assert svc.validate_currency("ZZZ") is False
    assert svc.validate_currency("XXX") is False


def test_to_display_amount_usd(svc):
    assert svc.to_display_amount(1050, "USD") == 10.50


def test_to_display_amount_jpy(svc):
    assert svc.to_display_amount(1050, "JPY") == 1050.0


def test_to_smallest_unit_usd(svc):
    assert svc.to_smallest_unit(10.50, "USD") == 1050


def test_to_smallest_unit_jpy(svc):
    assert svc.to_smallest_unit(1050, "JPY") == 1050


def test_get_currency_info(svc):
    info = svc.get_currency_info("USD")
    assert info is not None
    assert info["symbol"] == "$"
    assert info["decimals"] == 2


def test_get_currency_info_unknown(svc):
    assert svc.get_currency_info("ZZZ") is None
