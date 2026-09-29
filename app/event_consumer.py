from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from psycopg.types.json import Jsonb

from app.db import (
    open_pool,
    close_pool,
    get_connection,
)


class Event(BaseModel):
    event_id: int
    event_type: str
    aggregate_id: int
    payload: dict


@asynccontextmanager
async def lifespan(_: FastAPI):
    open_pool()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(
    title="E-sale Event Consumer",
    lifespan=lifespan,
)


@app.post("/events")
def consume_event(event: Event):
    with get_connection() as conn:
        with conn.transaction():
            inserted = conn.execute(
                """
                INSERT INTO consumer_deliveries (
                    event_id,
                    event_type,
                    aggregate_id,
                    payload
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                RETURNING event_id
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.aggregate_id,
                    Jsonb(event.payload),
                ),
            ).fetchone()

            if inserted is None:
                print(
                    "DUPLICATE EVENT IGNORED:",
                    event.event_id,
                )

                return {
                    "status": "duplicate_ignored",
                    "event_id": event.event_id,
                }

            print(
                "EVENT PROCESSED:",
                event.event_id,
            )

            return {
                "status": "processed",
                "event_id": event.event_id,
            }
