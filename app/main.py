from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.db import close_pool, get_connection, init_db, open_pool


class OrderCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class Order(BaseModel):
    id: int
    product_id: int
    quantity: int
    status: str


# @asynccontextmanager
# async def lifespan(_: FastAPI):
#     init_db()
#     yield


@asynccontextmanager
async def lifespan(_: FastAPI):
    open_pool()
    try:
        init_db()
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
def pay(order_id: int):
    with get_connection() as conn:
        with conn.transaction():
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
        return {"order_id": order_id, "status": "PAID"}


# @app.post("/orders/{order_id}/pay")
# def pay(order_id: int):
#     conn = get_connection()
#     try:
#         row = conn.execute(
#             """
#             SELECT id, product_id, quantity, status
#             FROM orders
#             WHERE id = ?
#             """,
#             (order_id,),
#         ).fetchone()

#         if row is None:
#             raise HTTPException(status_code=404, detail="Order not found")

#         return dict(row)
#     finally:
#         conn.close()


# @app.post("/orders/{order_id}/pay")
# def pay(order_id: int):
#     conn = get_connection()
#     try:
#         conn.execute("BEGIN")
#         cursor = conn.execute(
#             """
#             UPDATE orders
#             SET status = 'PAID'
#             WHERE id = ? AND status = 'CREATED'
#         """,
#             (order_id,),
#         )
#         if cursor.rowcount == 0:
#             raise HTTPException(
#                 status_code=429, detail="Order already paid or does not exist"
#             )
#         conn.execute(
#             """
#             INSERT INTO payments (
#             order_id,
#             status
#             ) VALUES (?, ?)
#         """,
#             (order_id, "SUCCESS"),
#         )
#         conn.commit()
#         return {"order_id": order_id, "status": "PAID"}
#     except:
#         conn.rollback()
#         raise
#     finally:
#         conn.close()
