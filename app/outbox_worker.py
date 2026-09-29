import time

from app.db import (
    open_pool,
    close_pool,
    get_connection,
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

    # 现在先模拟外部消息系统
    print("PUBLISH:", message)


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

            mark_published(event["id"])

    finally:
        close_pool()


if __name__ == "__main__":
    main()
