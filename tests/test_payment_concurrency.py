from fastapi.testclient import TestClient
from app.main import app
from concurrent.futures import ThreadPoolExecutor
from app.db import get_connection, init_db


def test_concurrent_payment_only_one_succeeds(
    tmp_path,
    monkeypatch,
):
    testdb = tmp_path / "test.db"
    monkeypatch.setenv("ESALE_DB_PATH", str(testdb))
    with TestClient(app) as client:
        response = client.post(
            "/orders",
            json={
                "product_id": 1001,
                "quantity": 1,
            },
        )
        assert response.status_code == 201
        order_id = response.json()["id"]

        def pay():
            return client.post(f"/orders/{order_id}/pay")

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(pay)
            future2 = executor.submit(pay)
            response1 = future1.result()
            response2 = future2.result()
            status_codes = sorted([response1.status_code, response2.status_code])
            assert status_codes == [200, 429]
            response = client.get(f"/orders/{order_id}")
            assert response.status_code == 200
            assert response.json()["status"] == "PAID"
            conn = get_connection()
            try:
                count = conn.execute(
                    "SELECT COUNT(*) FROM payments WHERE order_id=?", (order_id,)
                ).fetchone()[0]
                assert count == 1
            finally:
                conn.close()
