import os
from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None


def get_database_url() -> str:
    return os.getenv(
        "ESALE_DATABASE_URL",
        "postgresql://127.0.0.1:5432/esale",
    )


def open_pool() -> None:
    global _pool
    _pool = ConnectionPool(
        conninfo=get_database_url(),
        min_size=1,
        max_size=5,
        open=False,
        kwargs={
            "row_factory": dict_row,
        },
    )
    _pool.open()
    _pool.wait()


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_connection():
    if _pool is None:
        raise RuntimeError(
            "Connection pool is not initialized. Call open_pool() first."
        )
    with _pool.connection() as conn:
        yield conn
