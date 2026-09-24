from app.db import get_connection
from concurrent.futures import ThreadPoolExecutor


def test_payment_idempotency(client):
    response = client.post("/orders", json={"product_id": 1001, "quantity": 1})
    order_id = response.json()["id"]
    headers = {"Idempotency-Key": "pay-test-001"}
    first = client.post(f"/orders/{order_id}/pay", headers=headers)
    second = client.post(f"/orders/{order_id}/pay", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM payments
            WHERE order_id = %s
            """,
            (order_id,),
        ).fetchone()
        assert row["count"] == 1


def test_same_idempotency_key_concurrently_executes_once(client):
    response = client.post("/orders", json={"product_id": 1001, "quantity": 1})
    assert response.status_code == 201
    order_id = response.json()["id"]
    headers = {"Idempotency-Key": "pay-concurrent-same-key"}

    def pay():
        return client.post(f"/orders/{order_id}/pay", headers=headers)

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(pay)
        future2 = executor.submit(pay)
        response1 = future1.result()
        response2 = future2.result()
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()
    with get_connection() as conn:
        payments_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM payments
            WHERE order_id = %s
            """,
            (order_id,),
        ).fetchone()
        key_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM idempotency_keys
            WHERE idempotency_key = %s
            """,
            (headers["Idempotency-Key"],),
        ).fetchone()
        assert payments_count["count"] == 1
        assert key_count["count"] == 1
