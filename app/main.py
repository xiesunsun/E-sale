from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.db import get_connection, init_db


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
    init_db()
    yield


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
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO orders (product_id, quantity, status)
            VALUES (?, ?, ?)
            """,
            (order.product_id, order.quantity, "CREATED"),
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT id, product_id, quantity, status
            FROM orders
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        if row is None:
            raise RuntimeError("The inserted order could not be read back")

        return dict(row)
    finally:
        conn.close()


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, product_id, quantity, status
            FROM orders
            WHERE id = ?
            """,
            (order_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")

        return dict(row)
    finally:
        conn.close()
