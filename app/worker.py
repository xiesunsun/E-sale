import time
from app.db import open_pool, close_pool, get_connection


def claim_job():
    with get_connection() as conn:
        with conn.transaction():
            job = conn.execute("""
                SELECT id,job_type,payload
                FROM jobs
                WHERE status='PENDING'
                OR(
                    status='PROCESSING'
                    AND locked_at < now() - interval '10 seconds'
                )
                ORDER BY id
                For UPDATE SKIP LOCKED
                LIMIT 1
                """).fetchone()
            if job is None:
                return None

            conn.execute(
                """
                UPDATE jobs
                SET status='PROCESSING',
                locked_at=now(),
                attempts=attempts+1
                WHERE id=%s
                """,
                (job["id"],),
            )
            return job


def execute_job(job):
    if job["job_type"] != "SEND_PAYMENT_NOTIFICATION":
        return
    order_id = job["payload"]["order_id"]
    with get_connection() as conn:
        inserted = conn.execute(
            """
            INSERT INTO notification_deliveries (
                job_id,
                order_id
            ) VALUES (%s, %s)
            ON CONFLICT (job_id) DO NOTHING
            RETURNING id
        """,
            (job["id"], order_id),
        ).fetchone()
        if inserted is None:
            print(f"notification for order {order_id} already sent")
            return
        print(f"notification sent  for order {order_id}," f"job {job['id']}")
    # print(f"sending payment notification for order {order_id}")
    # raise RuntimeError("Simulated woker failure")
    # 模拟一个慢任务
    # time.sleep(2)
    # print(f"notification sent for order { order_id}")


def complete_job(job_id):
    with get_connection() as conn:
        with conn.transaction():
            conn.execute(
                """
                UPDATE jobs
                SET status='COMPLETED',
                locked_at = NULL
                WHERE id=%s
                """,
                (job_id,),
            )


def run_worker():
    open_pool()
    try:
        while True:
            job = claim_job()
            if job is None:
                time.sleep(1)
                continue
            execute_job(job)
            # raise RuntimeError("crash before ack")
            complete_job(job["id"])

    finally:
        close_pool()


if __name__ == "__main__":
    run_worker()
