from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Header
from pydantic import BaseModel, Field

from app.db import close_pool, get_connection, open_pool
from psycopg.types.json import Jsonb


class OrderCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class Order(BaseModel):
    id: int
    product_id: int
    quantity: int
    status: str


@asynccontextmanager
async def lifespan(_: FastAPI):
    open_pool()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(title="E-sale", version="0.1.0", lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "E-sale is running"}


@app.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
)
def create_order(order: OrderCreate) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO orders (product_id, quantity, status)
            VALUES (%s, %s, %s) 
            RETURNING id, product_id, quantity, status
            """,
            (order.product_id, order.quantity, "CREATED"),
        ).fetchone()
        if row is None:
            raise RuntimeError("The inserted order could not be read back")
        return row


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, product_id, quantity, status
            FROM orders
            WHERE id = %s
            """,
            (order_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(row)


@app.post("/orders/{order_id}/pay")
def pay(
    order_id: int,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
    ),
):
    with get_connection() as conn:
        with conn.transaction():
            inserted = conn.execute(
                """
                INSERT INTO idempotency_keys (
                    idempotency_key,
                    operation,
                    resource_id,
                    status
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING idempotency_key
            """,
                (idempotency_key, "PAY_ORDER", order_id, "PROGRESSING"),
            ).fetchone()
            if inserted is None:
                existing = conn.execute(
                    """
                    SELECT operation, resource_id, status, response_data
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
                        detail="Idempotency key already used for a different operation or resource",
                    )
                if existing["status"] == "COMPLETED":
                    return existing["response_data"]
                raise HTTPException(
                    status_code=409,
                    detail="Payment is already in progress for this order",
                )
            # 第一次请求支付
            cursor = conn.execute(
                """
                UPDATE orders
                SET status = 'PAID'
                WHERE id = %s AND status = 'CREATED'
            """,
                (order_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=409, detail="Order already paid or does not exist"
                )
            conn.execute(
                """
                INSERT INTO payments (
                order_id,
                status
                ) VALUES (%s, %s)
            """,
                (order_id, "SUCCESS"),
            )
            response = {"order_id": order_id, "status": "PAID"}
            conn.execute(
                """
                INSERT INTO jobs (
                    job_type,
                    payload,
                    status
                ) VALUES (%s, %s, %s)
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
                (Jsonb(response), idempotency_key),
            )
        return response
