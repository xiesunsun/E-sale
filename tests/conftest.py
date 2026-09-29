import pytest
from fastapi.testclient import TestClient
from app.db import get_connection
from app.main import app
import os
from app.cache import get_cache


def reset_cache():
    get_cache().flushdb()  # 清空 Redis 缓存


def reset_database():
    with get_connection() as conn:
        conn.execute("""
    TRUNCATE TABLE
        consumer_deliveries,
        outbox_events,
        payment_sagas,
        refunds,
        idempotency_keys,
        payments,
        orders
    RESTART IDENTITY CASCADE;
""")


@pytest.fixture
def client(monkeypatch):
    test_database_url = os.getenv(
        "ESALE_TEST_DATABASE_URL", "postgresql://127.0.0.1:5432/esale_test"
    )
    monkeypatch.setenv(
        "ESALE_DATABASE_URL",
        test_database_url,
    )
    with TestClient(app) as test_client:
        reset_database()
        reset_cache()
        try:
            yield test_client
        finally:
            reset_database()
            reset_cache()
