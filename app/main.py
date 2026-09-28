from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Header
from pydantic import BaseModel, Field
from redis.exceptions import RedisError
from app.db import close_pool, get_connection, open_pool
from psycopg.types.json import Jsonb
from app.cache import open_cache, close_cache, get_cache, release_lock
import json
import time
import uuid
import random
import os
import httpx

CACHE_NOT_FOUND = "__NOT_FOUND__"
CACHE_TTL_SECONDS = 10
NEGATIVE_CACHE_TTL_SECONDS = 5

INSTANCE_ID = os.getenv("ESALE_INSTANCE_ID", "unknown")
PAYMENT_SERVICE_URL = os.getenv(
    "ESALE_PAYMENT_SERVICE_URL",
    "http://127.0.0.1:9000",
)


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
    open_cache()
    try:
        yield
    finally:
        close_pool()
        close_cache()


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
    cache = get_cache()
    key = f"order:{order_id}"
    lock_key = f"lock:order:{order_id}"
    try:
        cached = cache.get(key)
    except RedisError as e:
        print("REDIS ERROR:", e)
        return load_order_from_db(order_id)
    ttl = CACHE_TTL_SECONDS + random.randint(0, 5)
    if cached == CACHE_NOT_FOUND:
        print("NEGATIVE CACHE HIT")
        raise HTTPException(status_code=404, detail="Order not found")
    if cached is not None:
        print("CACHE HIT")
        return json.loads(cached)
    print("CACHE MISS")
    lock_token = str(uuid.uuid4())
    try:
        acquired = cache.set(
            lock_key, lock_token, nx=True, ex=3
        )  # 设置锁的过期时间为3秒

    except RedisError as e:
        print("REDIS ERROR:", e)
        return load_order_from_db(order_id)
    if acquired:
        print("REBUILD LOCK ACQUIRED")
        try:
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
                    try:
                        cache.set(
                            key, CACHE_NOT_FOUND, ex=5
                        )  # 设置负缓存的过期时间为5秒

                    except RedisError as e:
                        print("REDIS ERROR:", e)
                    raise HTTPException(status_code=404, detail="Order not found")
                order = dict(row)
                try:
                    cache.set(key, json.dumps(order), ex=ttl)
                except RedisError as e:
                    print("REDIS ERROR:", e)
                return order
        finally:
            release_lock(lock_key, lock_token)
    print("WAITING FOR CACHE REBUILD")
    for _ in range(20):
        time.sleep(0.05)
        try:
            cached = cache.get(key)
        except RedisError as e:
            print("REDIS ERROR:", e)
            return load_order_from_db(order_id)
        if cached == CACHE_NOT_FOUND:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )
        if cached is not None:
            print("CACHE HIT AFTER WAIT")
            return json.loads(cached)

    raise HTTPException(
        status_code=503,
        detail="Cache rebuild timeout",
    )


@app.post("/orders/{order_id}/pay")
def pay(
    order_id: int,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
    ),
):
    response = httpx.post(
        f"{PAYMENT_SERVICE_URL}/internal/pay/{order_id}",
        headers={
            "Idempotency-Key": idempotency_key,
        },
        timeout=2.0,
    )

    if response.status_code >= 400:
        detail = response.json().get(
            "detail",
            "Payment service error",
        )

        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        )

    result = response.json()

    try:
        cache = get_cache()
        cache.delete(f"order:{order_id}")
    except RedisError as e:
        print("REDIS ERROR:", e)

    return result


def load_order_from_db(order_id: int) -> dict | None:
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


@app.get("/health/live")
def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
def readiness():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database not ready") from e

    return {"status": "ready"}


@app.get("/debug/sleep/{seconds}")
def debug_sleep(seconds: float):
    time.sleep(seconds)

    return {
        "instance": INSTANCE_ID,
        "slept": seconds,
    }
