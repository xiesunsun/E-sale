import time

from app.db import (
    open_pool,
    close_pool,
    get_connection,
)
import os
import httpx

EVENT_CONSUMER_URL = os.getenv(
    "ESALE_EVENT_CONSUMER_URL",
    "http://127.0.0.1:9100",
)

CRASH_AFTER_PUBLISH = (
    os.getenv(
        "ESALE_CRASH_AFTER_PUBLISH",
        "0",
    )
    == "1"
)


def load_next_event():
    with get_connection() as conn:
        return conn.execute("""
            SELECT
                id,
                event_type,
                aggregate_id,
                payload
            FROM outbox_events
            WHERE status = 'PENDING'
            ORDER BY id
            LIMIT 1
            """).fetchone()


def publish_event(event):
    message = {
        "event_id": event["id"],
        "event_type": event["event_type"],
        "aggregate_id": event["aggregate_id"],
        "payload": event["payload"],
    }

    response = httpx.post(
        f"{EVENT_CONSUMER_URL}/events",
        json=message,
        timeout=2.0,
    )

    response.raise_for_status()

    print(
        "PUBLISH SUCCESS:",
        message,
    )


def mark_published(event_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE outbox_events
            SET status = 'PUBLISHED',
                published_at = now()
            WHERE id = %s
            """,
            (event_id,),
        )


def main():
    open_pool()

    try:
        while True:
            event = load_next_event()

            if event is None:
                time.sleep(1)
                continue

            try:
                publish_event(event)
            except Exception as e:
                print(
                    "PUBLISH FAILED:",
                    event["id"],
                    e,
                )

                time.sleep(1)
                continue
            if CRASH_AFTER_PUBLISH:
                os._exit(1)

            mark_published(event["id"])

    finally:
        close_pool()


if __name__ == "__main__":
    main()
