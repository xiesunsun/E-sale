from fastapi.testclient import TestClient
from app.main import app


def test_create_order(client):
    response = client.post(
        "/orders",
        json={
            "product_id": 1001,
            "quantity": 2,
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["product_id"] == 1001
    assert created["quantity"] == 2
    assert created["status"] == "CREATED"
    order_id = created["id"]
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched == created
