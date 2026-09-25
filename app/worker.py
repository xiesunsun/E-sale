import time
from app.db import open_pool, close_pool, get_connection


def claim_job():
    with get_connection() as conn:
        with conn.transaction():
            job = conn.execute("""
                SELECT id,job_type,payload
                FROM jobs
                WHERE status='PENDING'
                ORDER BY id
                For UPDATE SKIP LOCKED
                LIMIT 1
                """).fetchone()
            if job is None:
                return None

            time.sleep(2)

            conn.execute(
                """
                UPDATE jobs
                SET status='PROCESSING'
                WHERE id=%s
                """,
                (job["id"],),
            )
            return job


def execute_job(job):
    if job["job_type"] == "SEND_PAYMENT_NOTIFICATION":
        order_id = job["payload"]["order_id"]
        print(f"sending payment notification for order {order_id}")
        # 模拟一个慢任务
        time.sleep(2)
        print(f"notification sent for order { order_id}")


def complete_job(job_id):
    with get_connection() as conn:
        with conn.transaction():
            conn.execute(
                """
                UPDATE jobs
                SET status='COMPLETED'
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
            complete_job(job["id"])

    finally:
        close_pool()


if __name__ == "__main__":
    run_worker()
