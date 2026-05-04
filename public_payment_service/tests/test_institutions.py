import pytest
from fastapi.testclient import TestClient


def test_register_institution(client: TestClient):
    payload = {
        "name": "Tokyo Metropolitan Government",
        "name_local": "東京都",
        "institution_type": "government",
        "country_code": "JP",
        "region": "Kanto",
        "contact_email": "admin@tokyo.lg.jp",
        "supported_currencies": ["JPY", "USD"],
    }
    response = client.post("/api/v1/institutions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "institution_id" in data
    assert "api_key" in data
    assert data["api_key"].startswith("pps_")
    assert "message" in data


def test_register_institution_invalid_country_code(client: TestClient):
    payload = {
        "name": "Bad Institution",
        "institution_type": "government",
        "country_code": "INVALID",
        "contact_email": "admin@bad.gov",
        "supported_currencies": ["USD"],
    }
    response = client.post("/api/v1/institutions", json=payload)
    assert response.status_code == 422


def test_register_institution_invalid_email(client: TestClient):
    payload = {
        "name": "Bad Institution",
        "institution_type": "government",
        "country_code": "US",
        "contact_email": "not-an-email",
        "supported_currencies": ["USD"],
    }
    response = client.post("/api/v1/institutions", json=payload)
    assert response.status_code == 422


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "database" in data
