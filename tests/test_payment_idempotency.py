from app.db import get_connection


def test_payment_idempotency(client):
    response = client.post("/orders", json={"product_id": 1001, "quantity": 1})
    order_id = response.json()["id"]
    headers = {"Idempotency-Key": "pay-test-001"}
    first=client.post(f"/orders/{order_id}/pay", headers=headers)
    second=client.post(f"/orders/{order_id}/pay", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()==first.json()
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
