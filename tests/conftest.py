import pytest
from fastapi.testclient import TestClient
from app.db import get_connection
from app.main import app
import os


def reset_database():
    with get_connection() as conn:
        conn.execute("""
            TRUNCATE TABLE payments,orders RESTART IDENTITY CASCADE
            """)


@pytest.fixture
def client(monkeypatch):
    test_database_url = os.getenv(
        "ESALE_TEST_DATABASE_URL", "host=127.0.0.1 port=5432 dbname=esale_test"
    )
    monkeypatch.setenv(
        "ESALE_DATABASE_URL",
        test_database_url,
    )
    with TestClient(app) as test_client:
        reset_database()
        try:
            yield test_client
        finally:
            reset_database()
