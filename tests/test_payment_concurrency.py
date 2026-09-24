from concurrent.futures import ThreadPoolExecutor

from app.db import get_connection


def test_concurrent_payment_only_one_succeeds(client):
    response = client.post(
        "/orders",
        json={
            "product_id": 1001,
            "quantity": 1,
        },
    )

    assert response.status_code == 201

    order_id = response.json()["id"]

    def pay(key):
        headers = {"Idempotency-Key": key}
        return client.post(f"/orders/{order_id}/pay", headers=headers)

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(pay, "pay-A")
        future2 = executor.submit(pay, "pay-B")

        response1 = future1.result()
        response2 = future2.result()

    status_codes = sorted(
        [
            response1.status_code,
            response2.status_code,
        ]
    )

    assert status_codes == [200, 409]

    response = client.get(f"/orders/{order_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "PAID"

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
