import sqlite3
from typing import Optional


def count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM notices").fetchone()
    return int(row["n"])


def get(conn: sqlite3.Connection, duid: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM notices WHERE duid = ?", (duid,)
    ).fetchone()


def insert(conn: sqlite3.Connection, notice: dict) -> None:
    conn.execute(
        """
        INSERT INTO notices
            (duid, title, category_id, author, posted_date, modified_date,
             is_pinned, marked_as_new)
        VALUES
            (:duid, :title, :category_id, :author, :posted_date,
             :modified_date, :is_pinned, :marked_as_new)
        """,
        notice,
    )


def update(conn: sqlite3.Connection, notice: dict) -> None:
    conn.execute(
        """
        UPDATE notices
           SET title         = :title,
               category_id   = :category_id,
               author        = :author,
               posted_date   = :posted_date,
               modified_date = :modified_date,
               is_pinned     = :is_pinned,
               marked_as_new = :marked_as_new,
               updated_at    = datetime('now')
         WHERE duid          = :duid
        """,
        notice,
    )
