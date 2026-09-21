import sqlite3
import os


def get_database_path() -> str:
    return os.getenv("ESALE_DB_PATH", "esale.db")


def get_connection() -> sqlite3.Connection:
    """Open one connection to the in-process SQLite library."""
    conn = sqlite3.connect(get_database_path(), isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the only table needed by Milestone 0."""
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL
            )
            """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments(
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL
            )
            """)
        conn.commit()
    finally:
        conn.close()
