import os
from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None


def get_database_url() -> str:
    return os.getenv("ESALE_DATABASE_URL", "host=127.0.0.1 port=5432 dbname=esale")


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


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
              id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
              product_id  BIGINT NOT NULL,
              quantity INTEGER NOT NULL,
              status TEXT NOT NULL
            )
            """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments(
              id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
              order_id BIGINT NOT NULL UNIQUE,
              status TEXT NOT NULL
            )
            """)


# import sqlite3
# import os


# def get_database_path() -> str:
#     return os.getenv("ESALE_DB_PATH", "esale.db")


# def get_connection() -> sqlite3.Connection:
#     """Open one connection to the in-process SQLite library."""
#     conn = sqlite3.connect(get_database_path(), isolation_level=None)
#     conn.row_factory = sqlite3.Row
#     return conn


# def init_db() -> None:
#     """Create the only table needed by Milestone 0."""
#     conn = get_connection()
#     try:
#         conn.execute("PRAGMA journal_mode=WAL")
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS orders (
#                 id INTEGER PRIMARY KEY,
#                 product_id INTEGER NOT NULL,
#                 quantity INTEGER NOT NULL,
#                 status TEXT NOT NULL
#             )
#             """)
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS payments(
#                 id INTEGER PRIMARY KEY,
#                 order_id INTEGER NOT NULL UNIQUE,
#                 status TEXT NOT NULL
#             )
#             """)
#         conn.commit()
#     finally:
#         conn.close()
