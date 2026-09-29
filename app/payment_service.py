from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from psycopg.types.json import Jsonb

from app.db import open_pool, close_pool, get_connection
import time
import os

PAYMENT_DEBUG_DELAY_SECONDS = float(os.getenv("ESALE_PAYMENT_DEBUG_DELAY_SECONDS", "0"))
PAYMENT_FORCE_503 = (
    os.getenv(
        "ESALE_PAYMENT_FORCE_503",
        "0",
    )
    == "1"
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    open_pool()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(
    title="E-sale Payment Service",
    lifespan=lifespan,
)


@app.post("/internal/pay/{order_id}")
def pay_order(
    order_id: int,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    if PAYMENT_FORCE_503:
        print("FORCED 503")
        raise HTTPException(
            status_code=503,
            detail="Payment service overloaded",
        )
    with get_connection() as conn:
        with conn.transaction():
            inserted = conn.execute(
                """
                INSERT INTO idempotency_keys (
                    idempotency_key,
                    operation,
                    resource_id,
                    status
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING idempotency_key
                """,
                (
                    idempotency_key,
                    "PAY_ORDER",
                    order_id,
                    "PROGRESSING",
                ),
            ).fetchone()

            if inserted is None:
                existing = conn.execute(
                    """
                    SELECT operation,
                           resource_id,
                           status,
                           response_data
                    FROM idempotency_keys
                    WHERE idempotency_key = %s
                    """,
                    (idempotency_key,),
                ).fetchone()

                if existing is None:
                    raise RuntimeError("Idempotency record disappeared")

                if (
                    existing["operation"] != "PAY_ORDER"
                    or existing["resource_id"] != order_id
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency key conflict",
                    )

                if existing["status"] == "COMPLETED":
                    return existing["response_data"]

                raise HTTPException(
                    status_code=409,
                    detail="Payment already in progress",
                )

            # cursor = conn.execute(
            #     """
            #     UPDATE orders
            #     SET status = 'PAID'
            #     WHERE id = %s
            #       AND status = 'CREATED'
            #     """,
            #     (order_id,),
            # )

            # if cursor.rowcount == 0:
            #     raise HTTPException(
            #         status_code=409,
            #         detail="Order already paid or does not exist",
            #     )

            payment = conn.execute(
                """
                INSERT INTO payments (order_id, status)
                VALUES (%s, %s)
                ON CONFLICT (order_id) DO NOTHING
                RETURNING id
                """,
                (order_id, "SUCCESS"),
            ).fetchone()
            if payment is None:
                raise HTTPException(
                    status_code=409,
                    detail="Order already paid or does not exist",
                )

            response = {
                "order_id": order_id,
                "status": "PAID",
            }

            conn.execute(
                """
                INSERT INTO jobs (
                    job_type,
                    payload,
                    status
                )
                VALUES (%s, %s, %s)
                """,
                (
                    "SEND_PAYMENT_NOTIFICATION",
                    Jsonb({"order_id": order_id}),
                    "PENDING",
                ),
            )

            conn.execute(
                """
                UPDATE idempotency_keys
                SET status = 'COMPLETED',
                    response_data = %s
                WHERE idempotency_key = %s
                """,
                (
                    Jsonb(response),
                    idempotency_key,
                ),
            )
        if PAYMENT_DEBUG_DELAY_SECONDS > 0:
            time.sleep(PAYMENT_DEBUG_DELAY_SECONDS)

        return response


@app.get("/health/live")
def liveness():
    return {"status": "alive"}
