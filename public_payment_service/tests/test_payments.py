import pytest
from fastapi.testclient import TestClient


def test_create_payment_success(client: TestClient, auth_headers, sample_payment_data):
    response = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["amount"] == 50000
    assert data["currency"] == "JPY"
    assert data["reference_number"].startswith("PAY-")
    assert data["expires_at"] is not None


def test_create_payment_invalid_currency(client: TestClient, auth_headers, sample_payment_data):
    sample_payment_data["currency"] = "ZZZ"
    response = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers)
    assert response.status_code == 400


def test_create_payment_unsupported_currency_for_institution(
    client: TestClient, auth_headers, sample_payment_data
):
    sample_payment_data["currency"] = "CNY"  # not in institution's supported_currencies
    response = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers)
    assert response.status_code == 400


def test_create_payment_zero_amount(client: TestClient, auth_headers, sample_payment_data):
    sample_payment_data["amount"] = 0
    response = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers)
    assert response.status_code == 422


def test_create_payment_unauthenticated(client: TestClient, sample_payment_data):
    response = client.post("/api/v1/payments", json=sample_payment_data)
    assert response.status_code == 403


def test_list_payments(client: TestClient, auth_headers, sample_payment_data):
    client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers)
    client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers)

    response = client.get("/api/v1/payments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_payments_filter_by_status(client: TestClient, auth_headers, sample_payment_data):
    client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers)

    response = client.get("/api/v1/payments?status=pending", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/payments?status=completed", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_get_payment_by_id(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    payment_id = created["id"]

    response = client.get(f"/api/v1/payments/{payment_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == payment_id


def test_get_payment_not_found(client: TestClient, auth_headers):
    response = client.get("/api/v1/payments/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_get_payment_by_reference(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    ref = created["reference_number"]

    response = client.get(f"/api/v1/payments/ref/{ref}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["reference_number"] == ref


def test_update_payment_status_to_processing(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    payment_id = created["id"]

    response = client.patch(
        f"/api/v1/payments/{payment_id}/status",
        json={"status": "processing"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_update_payment_status_to_completed(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    payment_id = created["id"]

    client.patch(
        f"/api/v1/payments/{payment_id}/status",
        json={"status": "processing"},
        headers=auth_headers,
    )
    response = client.patch(
        f"/api/v1/payments/{payment_id}/status",
        json={"status": "completed", "provider_transaction_id": "ch_test_123"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["receipt_number"] is not None
    assert data["receipt_number"].startswith("RCP-")


def test_invalid_status_transition(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    payment_id = created["id"]

    # Cannot go directly from pending to completed
    response = client.patch(
        f"/api/v1/payments/{payment_id}/status",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_refund_completed_payment(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    payment_id = created["id"]

    client.patch(f"/api/v1/payments/{payment_id}/status", json={"status": "processing"}, headers=auth_headers)
    client.patch(f"/api/v1/payments/{payment_id}/status", json={"status": "completed"}, headers=auth_headers)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        json={"reason": "Overpayment"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "refunded"


def test_refund_non_completed_payment(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    payment_id = created["id"]

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        json={"reason": "Test"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_cancel_pending_payment(client: TestClient, auth_headers, sample_payment_data):
    created = client.post("/api/v1/payments", json=sample_payment_data, headers=auth_headers).json()
    payment_id = created["id"]

    response = client.delete(f"/api/v1/payments/{payment_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
