import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Institution
from app.security.auth import generate_api_key, hash_api_key

TEST_DATABASE_URL = "sqlite:///./test_payment.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def institution_and_key(db):
    api_key = generate_api_key()
    institution = Institution(
        name="Test Municipality",
        institution_type="municipality",
        country_code="JP",
        contact_email="test@city.jp",
        api_key_hash=hash_api_key(api_key),
        supported_currencies="JPY,USD,EUR",
    )
    db.add(institution)
    db.commit()
    db.refresh(institution)
    return institution, api_key


@pytest.fixture
def auth_headers(institution_and_key):
    _, api_key = institution_and_key
    return {"X-API-Key": api_key}


@pytest.fixture
def sample_payment_data():
    return {
        "payer_name": "Taro Yamada",
        "payer_email": "taro@example.com",
        "payer_country_code": "JP",
        "amount": 50000,
        "currency": "JPY",
        "payment_method": "bank_transfer",
        "service_code": "TAX_MUNICIPAL",
        "service_description": "Municipal tax payment FY2026",
        "fiscal_year": "2026",
        "language": "ja",
    }
