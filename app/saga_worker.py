import os
import time

import httpx
from fastapi import HTTPException

from app.db import open_pool, close_pool, get_connection
from app.main import mark_order_paid

PAYMENT_SERVICE_URL = os.getenv(
    "ESALE_PAYMENT_SERVICE_URL",
    "http://127.0.0.1:9000",
)


def update_saga_status(order_id: int, status: str):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE payment_sagas
            SET status = %s
            WHERE order_id = %s
            """,
            (status, order_id),
        )


def load_pending_sagas():
    with get_connection() as conn:
        return conn.execute("""
            SELECT order_id, idempotency_key, status
            FROM payment_sagas
            WHERE status IN (
                'STARTED',
                'PAYMENT_SUCCEEDED'
            )
            ORDER BY id
            LIMIT 20
            """).fetchall()


def recover_saga(saga):
    order_id = saga["order_id"]
    key = saga["idempotency_key"]
    status = saga["status"]

    # 不确定支付有没有完成
    if status == "STARTED":
        try:
            response = httpx.post(
                f"{PAYMENT_SERVICE_URL}/internal/pay/{order_id}",
                headers={
                    "Idempotency-Key": key,
                },
                timeout=2.0,
            )
        except httpx.HTTPError as e:
            print("PAYMENT RECOVERY FAILED:", e)
            return

        if response.status_code != 200:
            print(
                "PAYMENT RECOVERY RETURNED:",
                response.status_code,
            )
            return

        update_saga_status(
            order_id,
            "PAYMENT_SUCCEEDED",
        )

    # 已知支付成功，继续完成订单
    try:
        mark_order_paid(order_id)

        update_saga_status(
            order_id,
            "COMPLETED",
        )

        print(
            "SAGA COMPLETED:",
            order_id,
        )

    except HTTPException:
        # 业务上已经不能继续前进 → 补偿
        try:
            response = httpx.post(
                f"{PAYMENT_SERVICE_URL}/internal/refund/{order_id}",
                headers={
                    "Idempotency-Key": f"{key}:refund",
                },
                timeout=2.0,
            )
        except httpx.HTTPError as e:
            print("REFUND RECOVERY FAILED:", e)
            return

        if response.status_code < 400:
            update_saga_status(
                order_id,
                "COMPENSATED",
            )

            print(
                "SAGA COMPENSATED:",
                order_id,
            )

    except Exception as e:
        # 数据库暂时挂了之类，不急着退款
        # 留给下一轮再试
        print(
            "SAGA TEMPORARY FAILURE:",
            order_id,
            e,
        )


def main():
    open_pool()

    try:
        while True:
            sagas = load_pending_sagas()

            for saga in sagas:
                recover_saga(saga)

            time.sleep(1)

    finally:
        close_pool()


if __name__ == "__main__":
    main()
