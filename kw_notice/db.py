import sqlite3
from contextlib import contextmanager

from . import config


def connect() -> sqlite3.Connection:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    schema_sql = config.SCHEMA_PATH.read_text(encoding="utf-8")
    seeds_sql = config.SEEDS_PATH.read_text(encoding="utf-8")
    with transaction() as conn:
        conn.executescript(schema_sql)
        conn.executescript(seeds_sql)
